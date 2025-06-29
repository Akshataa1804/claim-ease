import ollama
import json
import re
import time
import requests
from datetime import datetime
from document_processor import extract_entities, classify_document
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_claim(user_input, documents=None, model_name="llama3"):
    """
    Analyze the claim using GenAI with multimodal input
    Returns structured JSON analysis
    """
    try:
        # Combine all input sources
        full_context = user_input
        extracted_data = {}
        damage_reports = []
        document_summaries = []
        
        if documents:
            for doc in documents:
                full_context += f"\n\n[Document: {doc.get('type', 'unknown')}]\n{doc.get('text', '')}"
                
                # Classify document
                doc_type = classify_document(doc.get('text', ''))
                extracted_data.setdefault(doc_type, []).append(doc)
                
                # Generate document summary
                summary = generate_document_summary(doc)
                document_summaries.append(summary)
        
        # Extract entities using NLP
        entities = extract_entities(full_context)
        
        # Enhanced prompt template with clearer instructions
        prompt = f"""
You are an expert insurance claim analyst. Analyze this claim and provide structured output:

**Claim Context:**
{user_input}

**Document Summaries:**
{json.dumps(document_summaries, indent=2) if document_summaries else "No documents provided"}

**Required Output Format (JSON ONLY):**
{{
  "claimant": {{
    "name": "<Extracted name>",
    "contact_info": "<Phone/email if available>"
  }},
  "policy": {{
    "number": "<Extracted policy number>",
    "type": "<Auto/Home/Health>",
    "coverage_details": "<Key coverage terms>"
  }},
  "incident": {{
    "type": "<Classification>",
    "date": "<YYYY-MM-DD>",
    "location": "<Extracted location>",
    "description": "<Detailed incident summary>"
  }},
  "assessment": {{
    "estimated_loss": "<Amount with currency>",
    "fraud_risk": "<0-100 score>",
    "liability": "<Percentage allocation>",
    "completeness_score": "<0-100 based on information quality>"
  }},
  "next_steps": {{
    "required_docs": ["Police report", "Repair estimate", "Medical bills", "Photos of damage"],
    "timeline": "<Processing estimate>",
    "automated_actions": ["Initiate police report verification", "Assign claims adjuster", "Create claim file"]
  }},
  "summary": "<Comprehensive claim overview>"
}}

**Special Rules:**
1. Output MUST be valid JSON only
2. Infer missing information intelligently
3. Generate realistic timelines based on claim type
4. Suggest 2-3 automated actions
5. Fraud risk based on anomaly detection
6. Liability allocation must total 100% if multiple parties
7. For vehicle claims, VIN should be treated as policy identifier if no policy number found
8. For medical claims, include treatment details in assessment
"""
        # Send to Ollama
        start_time = time.time()
        response = ollama.chat(
            model=model_name,
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            options={'temperature': 0.1}
        )
        processing_time = time.time() - start_time
        
        output = response['message']['content']
        logger.info(f"Raw AI response: {output}")
        
        # Extract JSON from response
        try:
            # Improved JSON extraction
            json_match = re.search(r'\{[\s\S]*\}', output)
            if json_match:
                json_str = json_match.group(0)
                # Clean common formatting issues
                json_str = json_str.replace("\\n", "").replace("\\", "")
                result = json.loads(json_str)
            else:
                # Fallback to direct parsing
                result = json.loads(output)
                
            # Add metadata
            result["processing"] = {
                "time_sec": round(processing_time, 2),
                "model": model_name,
                "timestamp": datetime.now().isoformat()
            }
            
            return json.dumps(result, indent=2)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Response content: {output}")
            return json.dumps({
                "error": "AI response format issue",
                "suggestion": "Please provide more claim details",
                "raw_response": output,
                "processing_time": round(processing_time, 2)
            })
            
    except Exception as e:
        logger.exception("Error in analyze_claim")
        return json.dumps({
            "error": str(e),
            "message": "System error - please try again later"
        })

def generate_followup(claim_data):
    """Generate relevant follow-up questions using GenAI"""
    try:
        # Parse claim data if it's a string
        if isinstance(claim_data, str):
            claim_data = json.loads(claim_data)
        
        claim_summary = claim_data.get("summary", "")
        incident_desc = claim_data.get("incident", {}).get("description", "")
        
        prompt = f"""
Based on this claim analysis, generate 3 concise follow-up questions to gather missing information or clarify details:

Claim Summary:
{claim_summary}

Incident Description:
{incident_desc}

Output in JSON format with a single key "questions" that contains a list of strings.
Example: {{ "questions": ["What was the exact location of the accident?", "Do you have witness information?"] }}

**Focus on:**
- Missing documentation
- Clarification of incident details
- Policy coverage questions
- Medical treatment plans
"""
        response = ollama.chat(
            model="llama3",
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.3}
        )
        output = response['message']['content']
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            return result.get("questions", [
                "Can you confirm the date and time of the incident?",
                "Do you have photos of the damage?",
                "What is your insurance policy number?"
            ])
        else:
            return [
                "Can you provide more details about the incident?",
                "Do you have any supporting documents to upload?",
                "What is your insurance policy number?"
            ]
    except Exception as e:
        logger.error(f"Error in generate_followup: {str(e)}")
        return [
            "Can you confirm the date and time of the incident?",
            "Do you have photos of the damage?",
            "What is your insurance policy number?"
        ]

def generate_document_summary(document):
    """Generate summary for uploaded documents"""
    content = document.get('text', '')[:2000]
    prompt = f"""
Generate a concise summary of this document for claim processing:

Document type: {document.get('type', 'unknown')}
Content:
{content}

Output format:
- Key points
- Relevant details for claim
- Any concerns or missing information
"""
    try:
        response = ollama.chat(
            model="llama3",
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    except Exception:
        return "Document summary unavailable"

def predict_settlement(claim_data):
    """Predict likely settlement using GenAI"""
    try:
        # Parse claim data if it's a string
        if isinstance(claim_data, str):
            claim_data = json.loads(claim_data)
        
        incident_type = claim_data.get("incident", {}).get("type", "")
        loss = claim_data.get("assessment", {}).get("estimated_loss", "")
        
        prompt = f"""
Based on this claim analysis, predict the likely settlement outcome:

Incident Type: {incident_type}
Estimated Loss: {loss}

Output in JSON format:
{{
  "settlement_prediction": "<Likely outcome>",
  "amount_range": "<Min-max estimate>",
  "confidence": "<0-100 score>",
  "key_factors": ["List of influencing factors"]
}}
"""
        response = ollama.chat(
            model="llama3",
            messages=[{'role': 'user', 'content': prompt}],
            format="json"
        )
        output = response['message']['content']
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', output, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            # Ensure confidence is number
            if "confidence" in result and isinstance(result["confidence"], str):
                try:
                    result["confidence"] = int(result["confidence"])
                except:
                    result["confidence"] = 75
            return result
        else:
            return {
                "settlement_prediction": "Partial settlement",
                "amount_range": "$5,000-$7,500",
                "confidence": 75,
                "key_factors": ["Incomplete documentation", "Disputed liability"]
            }
    except Exception as e:
        logger.error(f"Error in predict_settlement: {str(e)}")
        return {
            "settlement_prediction": "Analysis in progress",
            "amount_range": "Not estimated",
            "confidence": 0,
            "key_factors": ["Initial assessment underway"]
        }