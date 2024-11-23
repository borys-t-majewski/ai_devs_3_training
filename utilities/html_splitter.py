import re

def parse_html_elements(text):
    """
    Parse HTML text to extract img tags and download links.
    
    Args:
        text (str): String containing HTML elements
        
    Returns:
        dict: Dictionary with 'images' and 'downloads' lists
        
    Examples:
        >>> text = '<img src="a.png"/> <p><a href="file.mp3" download>file.mp3</a></p>'
        >>> parse_html_elements(text)
        {
            'images': ['<img src="a.png"/>'],
            'downloads': ['<p><a href="file.mp3" download>file.mp3</a></p>']
        }
    """
    # Pattern for img tags
    img_pattern = r'<img\s+[^>]+?/>'
    
    # Pattern for download links (including surrounding p tag)
    download_pattern = r'<p><a\s+href="[^"]+"\s+download>[^<]+</a></p>'
    download_pattern = r'<a\s+href="[^"]+"\s+download(?:="")?\s*>[^<]+</a>'
    
    # Find all matches
    images = re.findall(img_pattern, text)
    downloads = re.findall(download_pattern, text)
    
    # Clean up any extra whitespace
    images = [img.strip() for img in images]
    downloads = [dl.strip() for dl in downloads]
    
    return {
        'images': images,
        'downloads': downloads
    }

def validate_elements(elements):
    """
    Validate that parsed elements are properly formatted.
    
    Args:
        elements (dict): Dictionary with 'images' and 'downloads' lists
        
    Returns:
        dict: Dictionary with validation results for each type
    """
    img_pattern = r'^<img\s+src="[^"]+"\s*/>[^>]*$'
    download_pattern = r'^<p><a\s+href="[^"]+"\s+download>[^<]+</a></p>$'
    
    return {
        'images': all(re.match(img_pattern, img) for img in elements['images']),
        'downloads': all(re.match(download_pattern, dl) for dl in elements['downloads'])
    }

# Example usage
if __name__ == "__main__":
    sample_text = '''<img src="https://centrala.ag3nts.org/dane/i/rynek.png"/>
            <img src="https://centrala.ag3nts.org/dane/i/rynek_glitch.png"/>
            <p><a href="i/rafal_dyktafon.mp3" download>rafal_dyktafon.mp3</a></p>'''
    
    sample_text = '''<img src="https://centrala.ag3nts.org/dane/i/rynek.png"/>
            <img src="https://centrala.ag3nts.org/dane/i/rynek_glitch.png"/>
            <a href="i/rafal_dyktafon.mp3" download="">rafal_dyktafon.mp3</a>'''
    
    # <a href="i/rafal_dyktafon.mp3" download="">rafal_dyktafon.mp3</a>


    # Parse the elements
    result = parse_html_elements(sample_text)
    
    # Validate the results
    validation = validate_elements(result)
    
    # Print results
    print("Images found:")
    for img in result['images']:
        print(f"  {img}")
        
    print("\nDownloads found:")
    for dl in result['downloads']:
        print(f"  {dl}")
        
    # Print validation results
    print("\nValidation results:")
    print(f"Images valid: {validation['images']}")
    print(f"Downloads valid: {validation['downloads']}")