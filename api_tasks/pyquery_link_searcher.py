from pyquery import PyQuery as pq
import requests
from urllib.parse import urljoin

def is_visible(element):
    """
    Check if an element is visible by checking various CSS properties
    and HTML attributes that commonly indicate hidden elements.
    """
    # Get computed style properties
    display = element.css('display')
    visibility = element.css('visibility')
    opacity = element.css('opacity')
    
    # Check various attributes and properties that indicate visibility
    is_hidden = (
        display == 'none' or
        visibility == 'hidden' or
        opacity == '0' or
        element.attr('hidden') is not None or
        element.attr('aria-hidden') == 'true' or
        element.closest('[style*="display: none"]') or
        element.closest('[style*="visibility: hidden"]') or
        # Check parent elements with class 'hidden' or similar
        element.closest('.hidden, .d-none, .invisible')
    )
    
    return not is_hidden

def get_filtered_links(url, options=None):
    """
    Get filtered links from a website using PyQuery
    
    Args:
        url (str): The website URL to scrape
        options (dict): Filtering options
            - selector (str): Custom CSS selector
            - exclude_external (bool): Exclude external links
            - exclude_empty (bool): Exclude empty links
            - exclude_javascript (bool): Exclude javascript: links
            - keep_relative (bool): Keep URLs relative (default: False)
            - only_visible (bool): Only return visible links (default: False)
            
    Returns:
        list: List of dictionaries containing filtered link information
    """
    if options is None:
        options = {}
        
    default_options = {
        'selector': 'a',
        'domain_url': None,
        'exclude_external': False,
        'exclude_empty': True,
        'exclude_javascript': True,
        'keep_relative': False,
        'only_visible': False
    }
    
    # Merge default options with provided options
    options = {**default_options, **options}
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        doc = pq(response.text)
        links = doc(options['selector'])
        
        link_data = []
        
        for link in links.items():
            # Skip if link is not visible and only_visible option is True
            if options['only_visible'] and not is_visible(link):
                continue
                
            href = link.attr('href')
            
            # Skip if conditions are met
            if not href and options['exclude_empty']:
                continue
            if href and href.startswith('javascript:') and options['exclude_javascript']:
                continue
                
            # Convert relative URLs to absolute unless keep_relative is True
            if not options['keep_relative']:
                if href and not href.startswith(('javascript:', 'mailto:', '#')):
                    href = urljoin(url, href)
            
            # Check if external after URL conversion
            is_external = href and href.startswith(('http', 'https')) and not href.startswith(url)

            if options['domain_url'] is not None:
                if not href.startswith(options['domain_url']) and href.startswith(('http', 'https')):
                    continue
            
            if is_external and options['exclude_external']:
                continue
                
            link_data.append({
                'href': href,
                'text': link.text().strip(),
                'title': link.attr('title'),
                'classes': link.attr('class'),
                'is_external': is_external,
                'is_visible': is_visible(link)
            })
            
        return link_data
        
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return []

# Example usage:
if __name__ == "__main__":
    url = "https://example.com"
    
    
    # Get only visible links from navigation
    visible_nav_links = get_filtered_links(url, {
        'selector': 'a',
        'exclude_external': False,
        'only_visible': True  # This will exclude hidden links
        ,'exclude_javascript': False
        ,"domain_url": "https://example.com"
    })

        #     'selector': 'a',
        # 'exclude_external': False,
        # 'exclude_empty': True,
        # 'exclude_javascript': True,
        # 'keep_relative': False,
        # 'only_visible': False
    

    print("Visible navigation links:", visible_nav_links)

    for m in visible_nav_links:
        print(m)