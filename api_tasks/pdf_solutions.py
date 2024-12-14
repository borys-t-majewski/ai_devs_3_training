import PyPDF2
from pdf2image import convert_from_path
import pytesseract
import fitz  # PyMuPDF
import requests
import io
import tempfile
import os
from PIL import Image

def download_pdf(url):
    """
    Download PDF from URL and return as bytes
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return io.BytesIO(response.content)
    except Exception as e:
        raise Exception(f"Failed to download PDF: {str(e)}")

def extract_with_pypdf2(source):
    """
    Extract text using PyPDF2 - fastest but basic text extraction
    """
    text = []
    try:
        if isinstance(source, str) and source.startswith('http'):
            pdf_file = download_pdf(source)
        else:
            pdf_file = open(source, 'rb') if isinstance(source, str) else source
            
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            text.append(page.extract_text() or '')  # Handle None returns
        
        if isinstance(pdf_file, io.IOBase):
            pdf_file.close()
        # return '\n'.join(text)
        return text
    except Exception as e:
        return f"Error with PyPDF2: {str(e)}"

def extract_with_ocr(source):
    """
    Extract text using OCR - best for scanned documents
    Requires poppler-utils to be installed
    """
    try:
        if isinstance(source, str) and source.startswith('http'):
            # Create a temporary file for the downloaded PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(download_pdf(source).read())
                tmp_path = tmp_file.name
        else:
            tmp_path = source

        # Convert PDF to images
        images = convert_from_path(tmp_path)
        text = []
        
        # Perform OCR on each image
        for image in images:
            text.append(pytesseract.image_to_string(image) or '')
        
        # Clean up temporary file if we created one
        if isinstance(source, str) and source.startswith('http'):
            os.unlink(tmp_path)
            
        # return '\n'.join(text)
        return text
    except Exception as e:
        return f"Error with OCR: {str(e)}"

def extract_with_pymupdf(source):
    """
    Extract text using PyMuPDF - good balance of speed and accuracy
    """
    text = []
    try:
        if isinstance(source, str) and source.startswith('http'):
            pdf_file = download_pdf(source)
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        else:
            doc = fitz.open(source)
            
        for page in doc:
            text.append(page.get_text() or '')  # Handle None returns
        doc.close()
        # return '\n'.join(text)
        return text
    except Exception as e:
        return f"Error with PyMuPDF: {str(e)}"

def extract_pages_as_images(source, output_dir="pdf_pages", dpi=200, format="PNG"):
    """
    Extract each page as an image
    Returns: List of paths to saved images
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        if isinstance(source, str) and source.startswith('http'):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(download_pdf(source).read())
                tmp_path = tmp_file.name
        else:
            tmp_path = source

        images = convert_from_path(tmp_path, dpi=dpi)
        saved_paths = []
        
        for i, image in enumerate(images):
            file_path = os.path.join(output_dir, f'page_{i+1}.{format.lower()}')
            image.save(file_path, format)
            saved_paths.append(file_path)
            
        # Clean up temporary file if we created one
        if isinstance(source, str) and source.startswith('http'):
            os.unlink(tmp_path)
            
        return saved_paths
    except Exception as e:
        return f"Error extracting pages as images: {str(e)}"

def extract_embedded_images(source, output_dir="embedded_images"):
    """
    Extract all embedded images from the PDF using PyMuPDF
    Returns: List of paths to saved images
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        saved_paths = []
        
        if isinstance(source, str) and source.startswith('http'):
            pdf_file = download_pdf(source)
            doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        else:
            doc = fitz.open(source)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                
                img_filename = os.path.join(output_dir, f'image_{page_num + 1}_{img_index + 1}.{ext}')
                with open(img_filename, "wb") as img_file:
                    img_file.write(image_bytes)
                saved_paths.append(img_filename)
        
        doc.close()
        return saved_paths
    except Exception as e:
        return f"Error extracting embedded images: {str(e)}"

def extract_text_from_pdf(source, method='pymupdf'):
    """
    Main function to extract text using the specified method
    source: can be either a local file path or a URL
    """
    methods = {
        'pypdf2': extract_with_pypdf2,
        'ocr': extract_with_ocr,
        'pymupdf': extract_with_pymupdf
    }
    
    if method not in methods:
        return f"Invalid method. Choose from: {', '.join(methods.keys())}"
    
    return methods[method](source)

# Example usage:
if __name__ == "__main__":
    # Example with local file
    pdf_path = "example.pdf"
    
    # Extract text
    text = extract_text_from_pdf(pdf_path, method='pymupdf')
    print(f"Extracted text (first 300 chars):\n{text[:300]}...")
    
    # Extract pages as images
    page_images = extract_pages_as_images(pdf_path, dpi=300)
    print(f"\nSaved {len(page_images)} pages as images")
    
    # Extract embedded images
    embedded_images = extract_embedded_images(pdf_path)
    print(f"\nExtracted {len(embedded_images)} embedded images")