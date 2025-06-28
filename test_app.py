import sys
import os
import json
import time

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from app import analyze_claim

# Test cases
test_cases = [
    ("My car was stolen yesterday. Policy AB123456.", "Standard claim"),
    ("", "Empty input"),
    ("Bicycle accident with medical bills", "Minimal information"),
    ("Name: John Doe, Policy: KA987654, Date: 2023-01-01, Loss: ₹50,000", "Complete information")
]

def run_tests():
    print("Starting ClaimEase test suite...\n")
    results = []
    
    for i, (test_input, description) in enumerate(test_cases, 1):
        print(f"Test {i}: {description}")
        print(f"Input: '{test_input}'")
        
        start_time = time.time()
        try:
            result = analyze_claim(test_input)
            parsed = json.loads(result)
            print(f"Status: Success")
            print(f"Response: {json.dumps(parsed, indent=2)}")
        except Exception as e:
            print(f"Status: Failed - {str(e)}")
            parsed = {"error": str(e)}
        
        print(f"Time: {time.time() - start_time:.2f}s")
        print("-" * 50)
        results.append((test_input, parsed))
    
    print("\nTest suite completed.")
    return results

if __name__ == "__main__":
    run_tests()