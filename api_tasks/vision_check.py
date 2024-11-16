from openai import OpenAI
import os
import io
from PIL import Image
from base64 import b64encode
from typing import List, Dict
import json

def prepare_image_for_text_recognition(image_path: str, max_size: int = 4000) -> str:
    """
    Prepares image for optimal text recognition:
    1. Converts to RGB if needed
    2. Increases contrast
    3. Resizes while maintaining quality
    4. Optimizes for text clarity
    """
    
    with Image.open(image_path) as img:
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Adjust contrast to make text more readable
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)  # Increase contrast by 50%
        
        # Resize if too large while maintaining aspect ratio
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', quality=95, optimize=True)
        return b64encode(buffer.getvalue()).decode('utf-8')
    
def analyze_images(
    client: OpenAI,
    local_folder: str = r'C:\Projects\images',
    output_file: str = 'image_descriptions.json',
    supported_formats: tuple = ('.jpg', '.jpeg', '.png', '.gif', '.webp'),
    model = "gpt-4-vision-preview",
    request = "Please describe this image in detail. Focus on main subjects, actions, and important visual elements.",
    pre_text_encoding = False
) -> Dict[str, str]:
    """
    Analyzes all images in a directory using OpenAI's Vision model.
    
    Args:
        client: OpenAI client instance
        local_folder: Directory containing images
        output_file: JSON file to save descriptions
        supported_formats: Tuple of supported image extensions
    
    Returns:
        Dictionary with filenames as keys and descriptions as values
    """
    
    descriptions = {}
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(local_folder, 'descriptions')
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each image in the directory
    for filename in os.listdir(local_folder):
        if not filename.lower().endswith(supported_formats):
            continue
            
        image_path = os.path.join(local_folder, filename)
        
        try:
            # Read and encode the image
            with open(image_path, "rb") as image_file:
                if pre_text_encoding:
                    base64_image = prepare_image_for_text_recognition(image_file)
                else:
                    base64_image = b64encode(image_file.read()).decode('utf-8')
            
            print(f"Processing {filename}...")
            
            # Call Vision API
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": request
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            # Extract description
            description = response.choices[0].message.content
            descriptions[filename] = description
            
            print(f"Processed {filename}")
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            descriptions[filename] = f"Error: {str(e)}"
    
    # Save descriptions to JSON file
    output_path = os.path.join(output_dir, output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=2)
    
    return descriptions

# Example usage:
if __name__ == "__main__":
    client = OpenAI(api_key="your-api-key")
    results = analyze_images(client)
    
    # Print results
    for filename, description in results.items():
        print(f"\n{filename}:")
        print(description)