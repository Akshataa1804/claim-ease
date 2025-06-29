import ollama
import json
import re
import time
from datetime import datetime
from document_processor import extract_policy_number

def analyze_claim(user_input, model_name="llama3"):
    try:
        # First extract policy number with regex for more reliable detection
        policy_number = extract_policy_number(user_input) or "Unknown"
        
        # Enhanced prompt template
        prompt = f"""
You are an expert insurance claim analyst. Analyze this claim and provide structured output:

**Claim Description:**
{user_input}

**Required Output Format (JSON ONLY):**
{{
  "Name": "<Extracted name or 'Unknown'>",
  "Policy Number": "{policy_number}",
  "Incident Type": "<Specific classification: Auto, Health, Property, Liability, Loan, Reimbursement>",
  "Incident Date": "<YYYY-MM-DD or 'Unknown'>",
  "Estimated Loss": "<Amount with currency or 'Not provided'>",
  "Red Flags": [
    "List specific concerns with evidence",
    "Note missing critical information"
  ],
  "Checklist": [
    "List 3-5 most important required documents",
    "Prioritize based on claim type"
  ],
  "Completeness Score": "<0-100 based on information quality>",
  "Summary": "<2-3 sentence overview of claim>"
}}

**Special Rules:**
1. Output MUST be valid JSON only
2. Policy numbers must match standard formats
3. Dates must be in YYYY-MM-DD format if provided
4. Incident Type must be one of: Auto, Health, Property, Liability, Loan, Reimbursement
5. Completeness Score should reflect data quality (higher = more complete info)
6. Be specific in Red Flags and Checklist items
"""
        # Send to Ollama
        start_time = time.time()
        response = ollama.chat(
            model=model_name,
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            options={'temperature': 0.2}
        )
        processing_time = time.time() - start_time
        
        output = response['message']['content']
        
        # Extract JSON from response
        try:
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                result = json.loads(output)
                
            # Validate required fields
            required_fields = ["Name", "Policy Number", "Incident Type", 
                             "Incident Date", "Estimated Loss", "Red Flags",
                             "Checklist", "Completeness Score", "Summary"]
            for field in required_fields:
                if field not in result:
                    result[field] = "Unknown"
                    
            # Add metadata
            result["processing_time"] = round(processing_time, 2)
            result["model"] = model_name
            result["timestamp"] = datetime.now().isoformat()
            
            return json.dumps(result, indent=2)
            
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": "Failed to parse AI response",
                "raw_output": output,
                "suggestion": "Please rephrase your claim description with more details",
                "processing_time": round(processing_time, 2)
            })
            
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "message": "System error - please try again later",
            "support": "Contact support@claimease.com for help",
            "timestamp": datetime.now().isoformat()
        })