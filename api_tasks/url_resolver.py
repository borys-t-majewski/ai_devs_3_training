from urllib.parse import urljoin, urlparse
import os.path
import re

def make_relative(base_url, absolute_url):
    """
    Convert an absolute URL to a relative URL based on the base URL.
    
    Args:
        base_url (str): The base URL of the webpage
        absolute_url (str): The absolute URL to convert
        
    Returns:
        str: Relative URL path
    """
    # Ensure base_url has a scheme
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
        
    # Parse both URLs
    base_parts = urlparse(base_url)
    abs_parts = urlparse(absolute_url)
    
    # If domains are different, keep the absolute URL
    if base_parts.netloc != abs_parts.netloc:
        return absolute_url
    
    # Get the directory of the base URL
    base_dir = os.path.dirname(base_parts.path)
    if not base_dir.endswith('/'):
        base_dir += '/'
        
    # If the absolute URL is under a different path branch,
    # use root-relative path for simplicity and reliability
    if not abs_parts.path.startswith(base_dir):
        return abs_parts.path
    
    # Convert to relative path
    rel_path = os.path.relpath(
        abs_parts.path,
        start=base_dir
    )
    
    return rel_path

def resolve_urls(base_url, html_content, make_absolute=True):
    """
    Resolves URLs in HTML content, converting between relative and absolute forms.
    
    Args:
        base_url (str): The base URL of the webpage
        html_content (str): HTML content containing URLs
        make_absolute (bool): If True, converts to absolute URLs; if False, converts to relative URLs
        
    Returns:
        str: HTML content with converted URLs
    """
    # Ensure base_url has a scheme
    if not base_url.startswith(('http://', 'https://')):
        base_url = 'https://' + base_url
    
    # Parse the base URL to get the scheme and netloc
    parsed_base = urlparse(base_url)
    base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
    
    def replace_url(match):
        url = match.group(2)
        
        if make_absolute:
            # Skip if it's already an absolute URL
            if url.startswith(('http://', 'https://', '//')):
                return match.group(0)
            
            # Handle root-relative URLs
            if url.startswith('/'):
                return f'{match.group(1)}{base_domain}{url}{match.group(3)}'
                
            # Convert relative URL to absolute
            absolute_url = urljoin(base_url, url)
            return f'{match.group(1)}{absolute_url}{match.group(3)}'
        else:
            # Skip if it's already a relative URL or starts with //
            if not url.startswith(('http://', 'https://')):
                return match.group(0)
            
            # Convert absolute URL to relative
            relative_url = make_relative(base_url, url)
            return f'{match.group(1)}{relative_url}{match.group(3)}'
    
    # Pattern to match URLs in src and href attributes
    pattern = r'((?:src|href)=[\'"]{1})(.*?)([\'"]{1})'
    
    # Replace all matched URLs
    resolved_html = re.sub(pattern, replace_url, html_content)
    
    return resolved_html




def normalize_download_links(full_text):
    from pyquery import PyQuery as pq
    d = pq(full_text)
    
    # Find all download links (with either download or download="")
    download_links = d('a[download]')
    
    for link in download_links:
        link = pq(link)
        # Normalize the download attribute
        link.attr('download', '')
        
        # If the link is inside a p tag, extract it
        parent_p = link.parent('p')
        if parent_p:
            # Replace p tag with its contents
            parent_p.replaceWith(link)
            
        # Or if you prefer to always wrap in p:
        # if not link.parent('p'):
        #     link.wrap('<p></p>')
    
    return d.outer_html()


# def get_links
def normalize_download_link(html_string):
    from pyquery import PyQuery as pq
    
    d = pq(html_string)
    
    # Get the link element (whether it's in a p tag or not)
    link = d('a')
    
    # Normalize the download attribute
    if 'download' in link.attr:
        link.attr('download', '')  # Set to empty string
    
    # You can choose to either:
    # 1. Always wrap in p:
    return f'<p>{link.outer_html()}</p>'



# Example usage
if __name__ == "__main__":
    base_url = "www.asd.pl/dane/arxiv-draft.html"
    
    # Test both conversions
    html_content = """
    <html>
        <body>
            <img src="i/strangefruit.png"/>
            <img src="/images/apple.jpg"/>
            <a href="../docs/paper.pdf">Document</a>
            <img src="https://external.com/image.jpg"/>
        </body>
    </html>
    """
    
    print("Original HTML:")
    print(html_content)
    print("\n")
    
    # Convert to absolute URLs
    absolute_html = resolve_urls(base_url, html_content, make_absolute=True)
    print("Absolute URLs:")
    print(absolute_html)
    print("\n")
    
    # Convert back to relative URLs
    relative_html = resolve_urls(base_url, absolute_html, make_absolute=False)
    print("Relative URLs:")
    print(relative_html)


    # Example usage:
    text = """
    Some text before
    <p><a href="i/rafal_dyktafon.mp3" download>rafal_dyktafon.mp3</a></p>
    Some text in between
    <a href="i/rafal_dyktafon.mp3" download="">rafal_dyktafon.mp3</a>
    Some text after
    """
    print(text)
    normalized = normalize_download_links(text)
    print(normalized)