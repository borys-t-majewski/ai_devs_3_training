import requests
from requests.exceptions import RequestException

def login_to_website(login_url, username, password, answer):

    """
    Thanks, Claude
    Perform a login POST request to a website.
    
    Args:
        login_url (str): The website's login endpoint URL
        username (str): User's username or email
        password (str): User's password
    
    Returns:
        tuple: (bool, str|requests.Response) - (success status, error message or response object)
    """
    # Setup the session to maintain cookies
    session = requests.Session()
    
    # Headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    # Login form data
    login_data = {
        'username': username,
        'password': password,
        'answer': answer
        # Add any other required form fields here
        # 'remember_me': 'true',
        # 'csrf_token': 'token_value'
    }
    
    try:
        # Make the POST request
        response = session.post(
            login_url,
            data=login_data,
            headers=headers,
            timeout=10
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Check for successful login (modify based on website's response)
        if response.status_code == 200:
            # You might want to check for specific cookies or response content
            # to confirm successful login
            return True, response
        else:
            return False, f"Login failed with status code: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except requests.exceptions.ConnectionError:
        return False, "Connection error occurred"
    except requests.exceptions.RequestException as e:
        return False, f"An error occurred: {str(e)}"
    finally:
        session.close()

# Example usage
if __name__ == "__main__":
    login_url = "https://example.com/login"
    username = "your_username"
    password = "your_password"
    
    success, result = login_to_website(login_url, username, password)
    
    if success:
        print("Login successful!")
        # Access the response object
        response = result
        print("Response headers:", response.headers)
    else:
        print("Login failed:", result)