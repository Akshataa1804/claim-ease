import ollama
import json
import re
import time
from datetime import datetime
from database import log_claim, get_claim_history

def analyze_claim(user_input, claim_type="Insurance", model_name="llama3"):
    try:
        # Load prompt template
        with open("prompt_template.txt", "r") as f:
            prompt = f.read().replace("{user_input}", user_input)
            prompt = prompt.replace("{claim_type}", claim_type)
        
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
            # Look for JSON code block
            json_match = re.search(r'```json\n(.*?)\n```', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
            else:
                # Look for plain JSON
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    # Fallback to direct parsing
                    result = json.loads(output)
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw_output": output}
        
        # Add metadata
        result["processing_time"] = f"{processing_time:.2f} seconds"
        result["model"] = model_name
        result["claim_type"] = claim_type
        result["timestamp"] = datetime.now().isoformat()
        
        return result
            
    except Exception as e:
        return {"error": str(e)}