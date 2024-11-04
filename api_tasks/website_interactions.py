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
