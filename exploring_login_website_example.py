from openai import OpenAI
import json 
import os
from api_tasks.basic_poligon_u import load_from_json
import asyncio
import requests
from bs4 import BeautifulSoup

json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
api_key = json_secrets["open_ai_api_key"]

def inspect_login_page(url):
    """
    Inspect a login page to find form details and security tokens.
    
    Args:
        url (str): The login page URL
    """
    session = requests.Session()
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all forms
    forms = soup.find_all('form')
    print(f"\nFound {len(forms)} forms on the page:")
    
    for i, form in enumerate(forms, 1):
        print(f"\nForm #{i}:")
        print(f"Action: {form.get('action', 'None')}")
        print(f"Method: {form.get('method', 'None')}")
        
        # Find all input fields
        inputs = form.find_all('input')
        print("\nInput fields:")
        for input_field in inputs:
            print(f"- Name: {input_field.get('name', 'None'):20} Type: {input_field.get('type', 'None'):10} Value: {input_field.get('value', 'None')}")
        
        # Look for hidden fields that might be security tokens
        hidden_fields = form.find_all('input', type='hidden')
        if hidden_fields:
            print("\nPossible security tokens (hidden fields):")
            for field in hidden_fields:
                print(f"- Name: {field.get('name', 'None'):20} Value: {field.get('value', 'None')}")

inspect_login_page(url="https://xyz.ag3nts.org")