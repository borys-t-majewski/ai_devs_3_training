
from typing import Iterator
import os 

def for_every_file_in_gen(
    directory: str,
    recursive: bool = True,
    supported_formats: tuple = None,
    include_no_extension: bool = False
) -> Iterator[str]:
    """
    Iterates through files in a directory and its subdirectories.
    
    Args:
        directory: Root directory to start search
        recursive: Whether to search in subdirectories (default: True)
        supported_formats: Tuple of allowed file extensions (e.g., ('.txt', '.jpg'))
                         If None, all files are included
        include_no_extension: Whether to include files without extensions (default: False)
    
    Yields:
        Full path to each matching file
    """
    supported_formats = [s.replace('.','').lower() for s in supported_formats]
    if recursive:
        # Walk through directory and subdirectories
        for root, _, files in os.walk(directory):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                # Get file extension (or empty string if none)
                _, ext = os.path.splitext(filename)
                ext = ext.replace('.','')

                # Check if file should be included
                if supported_formats is None:
                    # Include all files
                    yield file_path
                elif not ext and include_no_extension:
                    # Include files without extension if specified
                    yield file_path
                elif ext.lower() in supported_formats:
                    # Include files with matching extensions
                    yield file_path
    else:
        # Only look in the specified directory
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Skip if it's a directory
            if os.path.isdir(file_path):
                continue
                
            # Get file extension (or empty string if none)
            _, ext = os.path.splitext(filename)
            
            # Check if file should be included
            if supported_formats is None:
                yield file_path
            elif not ext and include_no_extension:
                yield file_path
            elif ext.lower() in supported_formats:
                yield file_path

def for_every_file_in(local_folder,supported_formats: tuple = ('.jpg', '.jpeg', '.png', '.gif', '.webp', 'jfif')):
    import os
    list_of_paths = []
    for filename in os.listdir(local_folder):
        print(filename)
        if filename.lower().endswith(supported_formats):
            list_of_paths.append(os.path.join(local_folder, filename))
    return list_of_paths

if __name__ == "__main__":
    print(for_every_file_in('C:\Projects\AI_DEVS_3\s_2_02_pictures'))


