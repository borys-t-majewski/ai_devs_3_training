import requests
import os
import json 
from typing import Dict, Any


def load_from_json(filepath: str = 'config.json') -> Dict[str, Any]:
    """Load secrets from JSON file"""
    try:
        with open(filepath, 'r') as f:
            secrets = json.load(f)
            
        required_keys = {'api_key'}
        missing_keys = required_keys - set(secrets.keys())
        
        if missing_keys:
            raise ValueError(f"Missing required keys in config: {', '.join(missing_keys)}")
            
        return secrets
    except FileNotFoundError:
        raise FileNotFoundError(f"Secrets file not found: {filepath}")
    
def download_data(url:str):
    import requests
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to download content. Status code: {response.status_code}")
    
def get_desired_format(byte):
    return [x for x in byte.decode().split('\n') if len(x) > 0]

def post_request(target:str, files):
    code = requests.post(target,data=files)
    return code

