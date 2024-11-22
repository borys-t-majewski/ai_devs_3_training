def scrape_site(session, url):
    login_response = session.post(
        url,
        # data=login_data,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': url
        }
    )

    # Check if login was successful
    if login_response.ok:
        # Now fetch the target page using the same session
        target_page = session.get(url)
        
        if target_page.ok:
            return target_page.text
        else:
            return f"Failed to fetch target page. Status code: {target_page.status_code}"
    else:
        return f"Login failed. Status code: {login_response.status_code}"


def download_webpage(url, output_folder='downloaded_pages'):
    from pyquery import PyQuery
    import os
    import requests
    from urllib.parse import urljoin, urlparse

    """
    Downloads a webpage and its assets to a local folder and analyzes it using pyquery.
    
    Args:
        url (str): The URL of the webpage to download
        output_folder (str): The folder where files will be saved
    """
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Download the main page
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.RequestException as e:
        print(f"Error downloading page: {e}")
        return None
    
    # Save the main HTML file
    domain = urlparse(url).netloc
    main_file_path = os.path.join(output_folder, f"{domain}.html")
    with open(main_file_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    # Parse the page with PyQuery
    pq = PyQuery(response.text)
    return pq

def sanitize_filename(filename):
    import re
    """Convert header text to a valid filename."""
    # Replace invalid filename characters with underscore
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    return filename or 'unnamed_section'

def download_and_chunk_webpage(url, output_folder='downloaded_pages'):
 
    """
    Downloads a webpage and splits it into separate files based on h2 headers.
    
    Args:
        url (str): The URL of the webpage to download
        output_folder (str): The folder where files will be saved
    """
    from pyquery import PyQuery
    import os
    import requests
    from urllib.parse import urljoin, urlparse


    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Download the main page
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error downloading page: {e}")
        return None
    
    # Parse the page with PyQuery
    pq = PyQuery(response.text)
    
    # Save the original complete HTML file
    domain = urlparse(url).netloc
    main_file_path = os.path.join(output_folder, f"{domain}_complete.html")
    with open(main_file_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"\nComplete page downloaded to: {main_file_path}")
    
    # Create a folder for the chunks
    chunks_folder = os.path.join(output_folder, f"{domain}_chunks")
    if not os.path.exists(chunks_folder):
        os.makedirs(chunks_folder)
    
    # Get all h2 headers
    h2_headers = pq('h2')
    
    if not h2_headers:
        print("No h2 headers found in the page.")
        return pq
    
    print(f"\nFound {len(h2_headers)} h2 headers. Creating separate files...")
    
    # Function to extract content between current and next h2
    def extract_content(start_elem, next_elem=None):
        content = PyQuery('<div></div>')
        current = start_elem[0]
        
        while current is not None and (next_elem is None or current != next_elem):
            next_sibling = current.getnext()
            
            # Break if we hit the next h2
            if next_sibling is not None and next_sibling.tag == 'h2':
                break
                
            content.append(current)
            current = next_sibling
            
        return content
    
    # Process each h2 section
    list_of_chunks =[]
    for i, header in enumerate(h2_headers):
        header_pq = PyQuery(header)
        header_text = header_pq.text().strip()
        filename = f"{i+1:02d}_{sanitize_filename(header_text)}.html"
        file_path = os.path.join(chunks_folder, filename)
        
        # Get content until next h2 or end of document
        next_header = h2_headers.eq(i+1) if i < len(h2_headers)-1 else None
        content = extract_content(header_pq, next_header)
        
        # Create a proper HTML document for this section
        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{header_text}</title>
</head>
<body>
    {content.outer_html()}
</body>
</html>"""
        
        # Save the section to a file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_template)

        list_of_chunks.append(content.outer_html())
        
        print(f"Created: {filename}")
    
    # Create an index file
    index_path = os.path.join(chunks_folder, "00_index.html")
    index_content = ["<!DOCTYPE html><html><head><title>Index</title></head><body>",
                    "<h1>Content Sections</h1>",
                    "<ul>"]
    
    for i, header in enumerate(h2_headers):
        header_text = PyQuery(header).text().strip()
        filename = f"{i+1:02d}_{sanitize_filename(header_text)}.html"
        index_content.append(f'<li><a href="{filename}">{header_text}</a></li>')
    
    index_content.extend(["</ul></body></html>"])
    
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(index_content))
    
    print(f"\nCreated index file: 00_index.html")
    print(f"All chunks saved in: {chunks_folder}")
    
    return pq, list_of_chunks