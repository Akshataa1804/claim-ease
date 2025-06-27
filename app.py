import ollama
import json
import re
import time

def check_red_flags(response_dict):
    """Detect additional red flags"""
    flags = []
    if "Unknown" in response_dict.get("Name", ""):
        flags.append("Missing claimant name")
    if not re.match(r"^[A-Z]{2}\d{6,8}$", response_dict.get("Policy Number", "")):
        flags.append("Suspicious policy number format")
    if "Unknown" in response_dict.get("Incident Date", ""):
        flags.append("Missing incident date")
    return flags

def analyze_claim(user_input):
    """Process user input with Llama3"""
    # Load your prompt template
    with open("prompt_template.txt", "r") as f:
        prompt = f.read().replace("{user_input}", user_input)
    
    try:
        # Record start time for performance monitoring
        start_time = time.time()
        
        # Send to Ollama
        response = ollama.chat(
            model='llama3',
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            options={'temperature': 0.2}
        )
        
        output = response['message']['content']
        print(f"Response time: {time.time() - start_time:.2f} seconds")
        
        # Clean up JSON output (models sometimes add markdown)
        output = output.replace('```json', '').replace('```', '').strip()
        
        # Parse to JSON
        parsed = json.loads(output)
        
        # Add additional red flags
        extra_flags = check_red_flags(parsed)
        if "Red Flags" in parsed:
            parsed["Red Flags"] += extra_flags
        else:
            parsed["Red Flags"] = extra_flags
            
        return json.dumps(parsed)
    
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "raw_output": output,
            "message": "Failed to process claim. Please try again."
        })