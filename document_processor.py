import PyPDF2
from PIL import Image
import pytesseract
import io
import re

def extract_text_from_upload(file):
    """Extract text from uploaded files (PDF, images)"""
    try:
        if file.type == "application/pdf":
            # PDF processing
            pdf_reader = PyPDF2.PdfReader(file)
            text = "\n".join([page.extract_text() for page in pdf_reader.pages])
            return text
        
        elif file.type.startswith("image/"):
            # Image processing
            img = Image.open(io.BytesIO(file.getvalue()))
            text = pytesseract.image_to_string(img)
            return text
        
        elif file.type == "text/plain":
            # Text file
            return file.getvalue().decode("utf-8")
            
    except Exception as e:
        return f"Error processing file: {str(e)}"
    
    return "Unsupported file type"

def extract_policy_number(text):
    """Helper function to extract policy numbers from text"""
    patterns = [
        r'\b[A-Z]{2,3}\d{6,8}\b',  # ABC123456
        r'\b\d{3}-\d{3}-\d{4}\b',   # 123-456-7890
        r'\bPOL-\d{6}\b',           # POL-123456
        r'\bPC\d{8}\b',             # PC12345678
        r'\bINS-\d{6}\b'            # INS-123456
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return None