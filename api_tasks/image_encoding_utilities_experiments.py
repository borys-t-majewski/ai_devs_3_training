import os
import ntpath

def test_png(h, f):
    if isinstance(h, str):
        h = h.encode('latin1')
    if h.startswith(b'\211PNG\r\n\032\n'):
        return 'png'

def test_jpeg(h, f):
    if isinstance(h, str):
        h = h.encode('latin1')
    if h.startswith(b'\377\330'):
        return 'jpeg'

def test_gif(h, f):
    if isinstance(h, str):
        h = h.encode('latin1')
    if h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
        return 'gif'

def test_webp(h, f):
    if isinstance(h, str):
        h = h.encode('latin1')
    if h.startswith(b'RIFF') and h[8:12] == b'WEBP':
        return 'webp'

def whaat(file=None, data=None):
    """
    Detect the type of image contained in a file or memory buffer.
    
    Args:
        file: Path to image file (can be full path, supports Windows paths)
        data: Binary or string image data
        
    Returns:
        str: Image type ('png', 'jpeg', 'gif', 'webp') or None if not detected
    """
    if file is None and data is None:
        raise ValueError("Either file or data must be provided")
    
    tests = [test_png, test_jpeg, test_gif, test_webp]
    
    if data is not None:
        if isinstance(data, bytes):
            header = data[:12]
        elif isinstance(data, str):
            header = data[:12]
            # header = os.path.basename(data)[:12]
        else:
            return None
    else:
        try:
            # Normalize path separators for the operating system
            file_path = os.path.normpath(file)
            
            # Convert to absolute path while preserving Windows backslashes
            file_path = os.path.abspath(file_path)

            file_path = os.path.basename(file_path)
            

            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'rb') as fp:
                header = fp.read(12)
        except Exception as e:
            print(f"Error reading file: {e}")  # Added error printing for debugging
            return None
    print('XDXFFXF')
    print(header)
    print(header)
    print(header)
    print(header)

    for test in tests:
        result = test(header, None)
        if result:
            return result
            
    return None
def check_jpeg_base64(base64_string):
    """
    Checks specific aspects of JPEG base64 string
    """
    import re
    import base64
    from base64 import b64decode
    print("Base64 String Analysis:")
    print(f"Length: {len(base64_string)}")
    print(f"Starts with JPEG header: {base64_string.startswith('/9j/')}")
    print("Contains newlines: {0}".format('\n' in base64_string))
    print("Contains carriage returns: {0}".format('\r' in base64_string))
    print(f"Contains spaces: {' ' in base64_string}")
        
    # Check for any non-base64 characters
    invalid_chars = re.findall('[^A-Za-z0-9+/=]', base64_string)
    if invalid_chars:
        print(f"Invalid characters found: {set(invalid_chars)}")
    else:
        print("No invalid characters found")
        
    # Try decoding
    try:
        decoded = base64.b64decode(base64_string)
        print(f"Successfully decoded! Length: {len(decoded)} bytes")
    except Exception as e:
        print(f"Decoding error: {str(e)}")

def validate_base64(base64_string):
    import base64
    import re
    """
    Validates if a string is proper base64, with special handling for JPEG headers
    """
    try:
        # JPEG files typically start with /9j/ in base64
        if base64_string.startswith('/9j/'):
            # Try to decode it
            base64.b64decode(base64_string)
            return True
            
        # For other image types, check if string contains only valid base64 characters
        if not re.match('^[A-Za-z0-9+/]*={0,3}$', base64_string):
            return False
        # Try to decode it
        base64.b64decode(base64_string)
        return True
    except Exception as e:
        print(f"Base64 validation error: {str(e)}")
        return False
    
def image_to_bytes(pil_image, format='PNG'):
    import io
    from io import BytesIO
    from PIL import Image, ImageEnhance
    # print(f"guess_format: {pil_image.split('.')[-1]}")
    
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format=format)
    return img_byte_arr.getvalue()

def validate_and_convert_image(image_url, max_size_mb=25,print_info_debug=False,local_image = False):
    """
    Validates and converts an image URL to base64, with detailed error checking
    
    Args:
        image_url (str): URL of the image
        max_size_mb (int): Maximum allowed size in MB
        
    Returns:
        tuple: (base64_string, media_type) or (None, error_message)
    """
    import requests
    # import imghdr
    from PIL import Image, ImageEnhance
    from io import BytesIO
    import base64
    from base64 import b64encode
    import re



    # try:
    if local_image:
        # used_image = image_to_bytes(image_url)
        used_image = image_url
    else:
    # Download the image
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        used_image = response.content
    print('KURWAAAAAAAAAAAAAAA')
    # Check file size
    content_length = len(used_image)
    if content_length > max_size_mb * 1024 * 1024:
        return None, f"Image too large: {content_length / (1024*1024):.2f}MB (max {max_size_mb}MB)"
        
    # Verify it's actually an image
    # image_type = imghdr.what(None, used_image)
    print(used_image)
    print(local_image)
    if local_image:
        image_type = whaat(used_image, None)
    else:
        image_type = whaat(None, used_image)

    if not image_type:
        return None, "File is not a recognized image format"

    # Try to open with PIL to verify it's not corrupted
    try:
        img = Image.open(BytesIO(used_image))
        img.verify()
    except Exception as e:
        return None, f"Invalid image data: {str(e)}"
        
    # Convert to base64
    base64_string = base64.b64encode(used_image).decode('utf-8')
    
    # Determine media type
    media_type = f"image/{image_type}"
    if image_type == 'jpeg' or image_type == 'jpg':
        media_type = "image/jpeg"
    elif image_type == 'png':
        media_type = "image/png"
    
    if print_info_debug:
        print(f'base 64 status {validate_base64(base64_string)}')
        print(f'debug 64 status {check_jpeg_base64(base64_string)}')
        print(f'Media type: {media_type}')
    return base64_string, media_type
        
    # except requests.exceptions.RequestException as e:
    #     return None, f"Download error: {str(e)}"
    # except Exception as e:
    #     return None, f"Unexpected error: {str(e)}"
    

def convert_local_picture(image_path: str, max_size: int = 8000, brightness_par = 1.3, sharpness_par = 1.4, contrast_par = 2, apply_enhancing = True, output_processed_path= False)  -> tuple[str, str]:
    """
    Prepares and saves processed image for OCR
    Returns: tuple of (base64_string, processed_image_path)
    Uses local path
    """
    import os 
    from PIL import Image, ImageEnhance
    from math import floor

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
        if max(img.size) > max_size:
            scale_factor = max_size / max(img.size)
            img = img.resize((floor(img.size[0] * scale_factor), floor(img.size[1] * scale_factor)), 
                           Image.Resampling.LANCZOS)
        

        # Enhance image for better text recognition
        enhancers = [
            (ImageEnhance.Contrast, 2),   # Increase contrast
            (ImageEnhance.Sharpness, 1.4),  # Increase sharpness
            (ImageEnhance.Brightness, 1.3)  # Slightly increase brightness
        ]
        
        if apply_enhancing:
            for enhancer_class, factor in enhancers:
                img = enhancer_class(img).enhance(factor)
            
        # Save processed image to file
        img.save(processed_path, format='PNG', quality=100, optimize=False)
        print(f"Saved processed image to: {processed_path}")
        return img, processed_path
    

        
        # Create base64 for API
        buffer = io.BytesIO()
        img.save(buffer, format='PNG', quality=100, optimize=False)
        base64_string = b64encode(buffer.getvalue()).decode('utf-8')
        
        return base64_string, processed_path


def extract_text_from_image(image_path):
    import cv2
    import tesseract
    # Read image using cv2
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Simple preprocessing to improve OCR
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # Extract text
    text = tesseract.image_to_string(gray)
    return text

def easy_ocr_read(image_path):
    import easyocr

    # Initialize the reader - first time will download models
    reader = easyocr.Reader(['en','pl'])  # 'en' for English, you can add more languages like ['en', 'fr']

    # Read image
    results = reader.readtext(image_path)  # replace with your image path
    return results
    # Print the extracted text
    # for detection in result:
    #     return detection