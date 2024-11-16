import os
import io
import requests
from PIL import Image, ImageEnhance
from base64 import b64encode
from typing import Dict

def prepare_image_for_text_recognition(image_path: str, max_size: int = 8000) -> tuple[str, str]:
    """
    Prepares and saves processed image for OCR
    Returns: tuple of (base64_string, processed_image_path)
    """
    # Create processed images directory next to original image
    processed_dir = os.path.join(os.path.dirname(image_path), 'processed_images')
    os.makedirs(processed_dir, exist_ok=True)
    
    # Generate output path
    filename = os.path.basename(image_path)
    processed_path = os.path.join(processed_dir, f'processed_{filename}')

    with Image.open(image_path) as img:
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Increase resolution if image is small
        if max(img.size) < 1000:
            scale_factor = 2
            img = img.resize((img.size[0] * scale_factor, img.size[1] * scale_factor), 
                           Image.Resampling.LANCZOS)
        
        # Enhance image for better text recognition
        enhancers = [
            (ImageEnhance.Contrast, 2),   # Increase contrast
            (ImageEnhance.Sharpness, 1.4),  # Increase sharpness
            (ImageEnhance.Brightness, 1.3)  # Slightly increase brightness
        ]
        
        for enhancer_class, factor in enhancers:
            img = enhancer_class(img).enhance(factor)
        
        # Save processed image to file
        img.save(processed_path, format='PNG', quality=100, optimize=False)
        print(f"Saved processed image to: {processed_path}")
        
        # Create base64 for API
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', quality=100, optimize=False)
        base64_string = b64encode(buffer.getvalue()).decode('utf-8')
        
        return base64_string, processed_path

def analyze_images_for_text(
    client: None,
    local_folder: str = r'C:\Projects\images',
    image_urls: list[str] = None,
    output_file: str = 'image_text_content.json',
    supported_formats: tuple = ('.jpg', '.jpeg', '.png', '.gif', '.webp', 'jfif')
    ,model = None
    ,user_query = ''
    ,system_message = ''
    ,model_type = 'openai'
) -> Dict[str, str]:
    
    text_contents = {}
    output_dir = os.path.join(local_folder, 'text_contents')
    os.makedirs(output_dir, exist_ok=True)

    if image_urls:
        for url in image_urls:
            try:
                # Download image from URL
                response = requests.get(url)
                response.raise_for_status()
                
                # Generate filename from URL
                filename = os.path.basename(url.split('?')[0])  # Remove query parameters
                if not filename:
                    filename = f"image_{len(text_contents)}.jpg"
                
                # Save temporary file
                temp_path = os.path.join(local_folder, f"temp_{filename}")
                with open(temp_path, 'wb') as f:
                    f.write(response.content)
            except:
                print("No url received")

    for filename in os.listdir(local_folder):
        if not filename.lower().endswith(supported_formats):
            continue
            
        image_path = os.path.join(local_folder, filename)
        
        try:
            print(f"Processing {filename}...")
            
            # Get both base64 and processed image path
            base64_image, processed_path = prepare_image_for_text_recognition(image_path)
            print(f"Original image: {image_path}")
            print(f"Processed version saved at: {processed_path}")
            if model_type == 'openai':
                response = client.chat.completions.create(
                
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_query
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}",
                                        "detail": "high"  # This enables maximum detail analysis
                                    }
                                }
                            ]
                        }
                        ,{
                            "role": "system",
                            "content": [
                                {
                                    "type": "text",
                                    "text": system_message
                                }
                            ]
                        }
                    ],
                    max_tokens=4096,  # Increased for more detailed response
                    temperature=0,    # Keep it at 0 for maximum accuracy
                )
                text_content = response.choices[0].message.content

            if model_type == 'anthropic':
                response = client.messages.create(
                    model=model
                    ,system = system_message
                    ,messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_query
                                },
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": base64_image  # This enables maximum detail analysis
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=4096,  # Increased for more detailed response
                    temperature=0,    # Keep it at 0 for maximum accuracy
                    )
                text_content = response.content
            # Add processed image path to the output
            
            
            text_contents[filename] = {
                "text": text_content,
                "processed_image": processed_path
            }
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            text_contents[filename] = {
                "text": f"Error: {str(e)}",
                "processed_image": None
            }
    
    return text_contents 