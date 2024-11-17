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
    

def extract_nested_zips(zip_data, extract_path):
    import os 
    import requests
    import zipfile
    import io
    """
    Recursively extract ZIP files, including any ZIP files contained within.
    
    Args:
        zip_data: Either a path to a ZIP file, or a bytes-like object containing ZIP data
        extract_path: Directory where files should be extracted
    """
    def _extract_nested(zip_obj, current_path):
        for name in zip_obj.namelist():
            # Normalize path separators and remove any leading slashes
            safe_name = name.replace('/', os.sep).replace('\\', os.sep).lstrip(os.sep)
            out_path = os.path.join(current_path, safe_name)
            
            # Skip if it's just a directory entry
            if name.endswith('/') or name.endswith('\\'):
                os.makedirs(out_path, exist_ok=True)
                continue
                
            # Create parent directory if it doesn't exist
            parent_dir = os.path.dirname(out_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
                
            # Extract the file
            data = zip_obj.read(name)
            
            # Check if this is a ZIP file by looking at its magic numbers
            is_zip = data.startswith(b'PK\x03\x04')
            
            if is_zip:
                # If it's a ZIP file, extract it recursively
                try:
                    with zipfile.ZipFile(io.BytesIO(data)) as nested_zip:
                        nested_path = os.path.join(current_path, os.path.splitext(safe_name)[0])
                        _extract_nested(nested_zip, nested_path)
                except:
                    print(f"Error unzipping {nested_path}")
            else:
                # If it's not a ZIP file, write it to disk
                try:
                    with open(out_path, 'wb') as f:
                        f.write(data)
                except OSError as e:
                    print(f"Error writing file {out_path}: {e}")

    # Handle both file paths and bytes-like objects
    if isinstance(zip_data, (str, bytes, bytearray)):
        if isinstance(zip_data, str):
            zip_obj = zipfile.ZipFile(zip_data)
        else:
            zip_obj = zipfile.ZipFile(io.BytesIO(zip_data))
        
        with zip_obj:
            _extract_nested(zip_obj, extract_path)

def get_source_data_from_zip(data_source_url:str= '',directory_suffix:str = 's_2_01_audiofiles', extract_sublevel = True) -> None:
    import os 
    import requests
    import zipfile
    import io
    # Create the directory if it doesn't exist
    path2use = os.path.join(os.path.dirname(__file__), directory_suffix)
    os.makedirs(path2use, exist_ok=True)

    response = requests.get(data_source_url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        # Extract all files to the specified directory
        if extract_sublevel:
            extract_nested_zips(response.content, path2use)
        else:
            zf.extractall(path2use)
    