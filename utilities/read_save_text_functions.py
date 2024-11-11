import json
from datetime import datetime
import os

def save_text_to_json(text: str, file_path: str, file_name: str = None, add_timestamp: bool = True) -> str:
    """
    Save text content to a JSON file with optional timestamp in filename.
    
    Args:
        text (str): The text content to save
        file_path (str): Relative path to save directory
        file_name (str, optional): Base name for the file (without extension)
        add_timestamp (bool): Whether to add timestamp to filename
    
    Returns:
        str: Path to the created JSON file
    """
    # Create directory if it doesn't exist
    os.makedirs(file_path, exist_ok=True)
    
    # Generate filename
    if file_name is None:
        file_name = "text_content"
    
    if add_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{file_name}_{timestamp}.json"
    else:
        full_filename = f"{file_name}.json"
    
    # Prepare data structure
    data = {
        "content": text,
        "timestamp": datetime.now().isoformat(),
        "filename": full_filename
    }
    
    # Create full file path
    full_path = os.path.join(file_path, full_filename)
    
    # Save to JSON file
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    return full_path

def read_text_from_json(file_path: str) -> dict:
    """
    Read text content from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
    
    Returns:
        dict: Dictionary containing the file contents with keys:
              'content', 'timestamp', 'filename'
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in file: {file_path}")
    
def get_source_data_from_zip(data_source_url:str= '') -> None:
    import os 
    import requests
    import zipfile
    import io
    # Create the directory if it doesn't exist
    path2use = os.path.join(os.path.dirname(__file__), 's_2_01_audiofiles')
    os.makedirs(path2use, exist_ok=True)

    response = requests.get(data_source_url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        # Extract all files to the specified directory
        zf.extractall(path2use)

