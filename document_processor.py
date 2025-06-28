import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import re

# Set Tesseract path for Windows
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except:
    pass  # Use system PATH if not Windows

def extract_text_from_upload(file):
    """Extract text from uploaded files with OCR"""
    try:
        if file.type == "application/pdf":
            images = convert_from_bytes(file.read())
            text = "\n".join(pytesseract.image_to_string(image) for image in images)
            return f"PDF Content:\n{text}"
        
        elif file.type.startswith("image/"):
            image = Image.open(io.BytesIO(file.read()))
            text = pytesseract.image_to_string(image)
            return f"Image Content:\n{text}"
        
        elif file.type == "text/plain":
            return file.getvalue().decode("utf-8")
            
        return f"Unsupported file type: {file.type}"
    except Exception as e:
        return f"Error processing document: {str(e)}"