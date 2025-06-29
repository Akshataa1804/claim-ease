import PyPDF2
from PIL import Image
import pytesseract
import io
import re
import spacy
import fitz  # PyMuPDF for advanced PDF processing
import json
import requests
from datetime import datetime

# Load NLP models
nlp = spacy.load("en_core_web_sm")

def extract_text_from_upload(file):
    """Extract text and metadata from uploaded files with GenAI enhancement"""
    try:
        # PDF processing with advanced features
        if file.type == "application/pdf":
            text = ""
            metadata = {}
            with fitz.open(stream=file.getvalue(), filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text()
                metadata = doc.metadata
            return {"text": text, "metadata": metadata, "type": "pdf"}
        
        # Image processing with OCR
        elif file.type.startswith("image/"):
            img = Image.open(io.BytesIO(file.getvalue()))
            text = pytesseract.image_to_string(img)
            
            # Enhanced GenAI image description
            description = generate_image_description(img)
            return {"text": text, "description": description, "type": "image"}
        
        # Text file processing
        elif file.type == "text/plain":
            content = file.getvalue().decode("utf-8")
            return {"text": content, "type": "text"}
            
    except Exception as e:
        return {"error": f"Error processing file: {str(e)}"}
    
    return {"error": "Unsupported file type"}

def extract_entities(text):
    """Extract entities using NLP with GenAI enhancement"""
    doc = nlp(text)
    entities = {
        "PERSON": [],
        "DATE": [],
        "ORG": [],
        "MONEY": [],
        "GPE": []  # locations
    }
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text)
    
    # Enhance with GenAI for more complex extraction
    enhanced = enhance_entity_extraction(text)
    if enhanced:
        entities.update(enhanced)
    
    return entities

def classify_document(text):
    """Classify document type using GenAI"""
    prompt = f"""
Classify this document into one of these categories:
- policy
- claim_form
- medical_report
- invoice
- identification
- damage_photos
- correspondence
- other

Document content:
{text[:2000]}

Output ONLY the category name.
"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
        )
        return response.json()["response"].strip()
    except Exception:
        # Fallback logic
        if "policy" in text.lower():
            return "policy"
        elif "medical" in text.lower():
            return "medical_report"
        elif "invoice" in text.lower():
            return "invoice"
        return "other"

def analyze_damage(image):
    """Analyze damage in images using GenAI"""
    # In production, this would use a vision model
    # For now, we simulate with text description
    prompt = f"""
Analyze this damage image and provide:
- Damage type (dent, scratch, crack, etc.)
- Severity (low, moderate, high)
- Estimated repair cost range
- Likely cause

Output in JSON format only.
"""
    return {
        "damage_type": "dent",
        "severity": "moderate",
        "cost_range": "$1,200-$1,800",
        "cause": "collision",
        "confidence": 0.85
    }

def generate_image_description(image):
    """Generate descriptive caption for images"""
    # Simulate vision model response
    return "A blue sedan with significant front-end damage and deployed airbags"

def enhance_entity_extraction(text):
    """Use GenAI to extract complex entities"""
    prompt = f"""
Extract the following entities from this text:
- Claimant name
- Policy number
- Incident date (YYYY-MM-DD format)
- Incident location
- Contact information (phone/email)
- Vehicle make/model (if applicable)
- Medical provider (if applicable)

Text:
{text[:2000]}

Output in JSON format only.
"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
        )
        return response.json()["response"]
    except Exception:
        return {}