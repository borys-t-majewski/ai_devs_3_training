from bs4 import BeautifulSoup

def extract_text_by_id(html_file_path, element_id):
    # Read the HTML file
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    # Create BeautifulSoup object
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the element with specific ID
    element = soup.find('p', id=element_id)
    
    # Return text if element is found, None otherwise
    return element.text.strip() if element else None

# Example usage
if __name__ == "__main__":
    # Replace with your HTML file path
    file_path = 'example.html'
    result = extract_text_by_id(file_path, 'human-question')
    print(result)

def get_strings_re(string,pattern=r'<p id="human-question">(.*?)</p>'):
    import re
    match = re.search(pattern, string)
    return match.group(1) if match else None