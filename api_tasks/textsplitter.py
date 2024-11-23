from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re
from tiktoken import Encoding, get_encoding  # Using tiktoken instead of tiktokenizer

@dataclass
class DocumentMetadata:
    tokens: int
    headers: Dict[str, List[str]]
    urls: List[str]
    images: List[str]

@dataclass
class Document:
    text: str
    metadata: DocumentMetadata

class TextSplitter:
    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        self.tokenizer: Optional[Encoding] = None
        self.special_tokens = {
            "<|im_start|>": 100264,
            "<|im_end|>": 100265,
            "<|im_sep|>": 100266
        }

    def initialize_tokenizer(self) -> None:
        """Initialize the tokenizer if it hasn't been initialized yet."""
        if not self.tokenizer:
            self.tokenizer = get_encoding(self.model_name)
            # Add special tokens to the tokenizer
            # Note: This is a simplified version as tiktoken handles special tokens differently

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text."""
        if not self.tokenizer:
            raise RuntimeError("Tokenizer not initialized")
        formatted_content = self.format_for_tokenization(text)
        return len(self.tokenizer.encode(formatted_content))

    def format_for_tokenization(self, text: str) -> str:
        """Format the text for tokenization."""
        return f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant<|im_end|>"

    async def split(self, text: str, limit: int) -> List[Document]:
        """Split the text into chunks based on the token limit."""
        print(f"Starting split process with limit: {limit} tokens")
        self.initialize_tokenizer()
        chunks: List[Document] = []
        position = 0
        total_length = len(text)
        current_headers: Dict[str, List[str]] = {}

        while position < total_length:
            print(f"Processing chunk starting at position: {position}")
            chunk_text, chunk_end = self.get_chunk(text, position, limit)
            tokens = self.count_tokens(chunk_text)
            print(f"Chunk tokens: {tokens}")

            headers_in_chunk = self.extract_headers(chunk_text)
            self.update_current_headers(current_headers, headers_in_chunk)

            content, urls, images = self.extract_urls_and_images(chunk_text)

            chunks.append(Document(
                text=content,
                metadata=DocumentMetadata(
                    tokens=tokens,
                    headers=dict(current_headers),
                    urls=urls,
                    images=images
                )
            ))

            print(f"Chunk processed. New position: {chunk_end}")
            position = chunk_end

        print(f"Split process completed. Total chunks: {len(chunks)}")
        return chunks

    def get_chunk(self, text: str, start: int, limit: int) -> Tuple[str, int]:
        """Get a chunk of text that fits within the token limit."""
        print(f"Getting chunk starting at {start} with limit {limit}")
        
        # Calculate token overhead
        overhead = self.count_tokens(self.format_for_tokenization("")) - self.count_tokens("")
        
        # Initial tentative end position
        end = min(
            start + int((len(text) - start) * limit / self.count_tokens(text[start:])),
            len(text)
        )
        
        # Adjust end to avoid exceeding token limit
        chunk_text = text[start:end]
        tokens = self.count_tokens(chunk_text)
        
        while tokens + overhead > limit and end > start:
            print(f"Chunk exceeds limit with {tokens + overhead} tokens. Adjusting end position...")
            end = self.find_new_chunk_end(text, start, end)
            chunk_text = text[start:end]
            tokens = self.count_tokens(chunk_text)

        # Adjust chunk end to align with newlines
        end = self.adjust_chunk_end(text, start, end, tokens + overhead, limit)
        
        chunk_text = text[start:end]
        print(f"Final chunk end: {end}")
        return chunk_text, end

    def adjust_chunk_end(self, text: str, start: int, end: int, current_tokens: int, limit: int) -> int:
        """Adjust the chunk end to align with newlines while maintaining token limit."""
        min_chunk_tokens = int(limit * 0.8)  # Minimum chunk size is 80% of limit

        next_newline = text.find('\n', end)
        prev_newline = text.rfind('\n', start, end)

        # Try extending to next newline
        if next_newline != -1 and next_newline < len(text):
            extended_end = next_newline + 1
            chunk_text = text[start:extended_end]
            tokens = self.count_tokens(chunk_text)
            if tokens <= limit and tokens >= min_chunk_tokens:
                print(f"Extending chunk to next newline at position {extended_end}")
                return extended_end

        # Try reducing to previous newline
        if prev_newline > start:
            reduced_end = prev_newline + 1
            chunk_text = text[start:reduced_end]
            tokens = self.count_tokens(chunk_text)
            if tokens <= limit and tokens >= min_chunk_tokens:
                print(f"Reducing chunk to previous newline at position {reduced_end}")
                return reduced_end

        return end

    def find_new_chunk_end(self, text: str, start: int, end: int) -> int:
        """Find a new chunk end position when the current chunk exceeds the token limit."""
        new_end = end - ((end - start) // 10)  # Reduce by 10% each iteration
        if new_end <= start:
            new_end = start + 1  # Ensure at least one character is included
        return new_end

    def extract_headers(self, text: str) -> Dict[str, List[str]]:
        """Extract headers from the text."""
        headers: Dict[str, List[str]] = {}
        header_regex = r'(^|\n)(#{1,6})\s+(.*)'
        
        for match in re.finditer(header_regex, text, re.MULTILINE):
            level = len(match.group(2))
            content = match.group(3).strip()
            key = f"h{level}"
            if key not in headers:
                headers[key] = []
            headers[key].append(content)

        return headers

    def update_current_headers(self, current: Dict[str, List[str]], 
                             extracted: Dict[str, List[str]]) -> None:
        """Update the current headers based on extracted headers."""
        for level in range(1, 7):
            key = f"h{level}"
            if key in extracted:
                current[key] = extracted[key]
                self.clear_lower_headers(current, level)

    def clear_lower_headers(self, headers: Dict[str, List[str]], level: int) -> None:
        """Clear headers of lower levels."""
        for l in range(level + 1, 7):
            headers.pop(f"h{l}", None)

    def extract_urls_and_images(self, text: str) -> Tuple[str, List[str], List[str]]:
        """Extract URLs and images from the text, replacing them with placeholders."""
        urls: List[str] = []
        images: List[str] = []
        url_index = 0
        image_index = 0

        def replace_image(match: re.Match) -> str:
            nonlocal image_index
            alt_text = match.group(1)
            url = match.group(2)
            images.append(url)
            result = f"![{alt_text}]({{{{$img{image_index}}}}})"
            image_index += 1
            return result

        def replace_url(match: re.Match) -> str:
            nonlocal url_index
            link_text = match.group(1)
            url = match.group(2)
            urls.append(url)
            result = f"[{link_text}]({{{{$url{url_index}}}}})"
            url_index += 1
            return result

        # Replace images first, then URLs
        content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image, text)
        content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_url, content)

        return content, urls, images