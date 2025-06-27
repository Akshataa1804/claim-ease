from app import analyze_claim
import time

# Test input
test_input = "My car was stolen from the parking lot on 2023-07-20. Policy number DL987654. Police case FIR-2023-1234"

print("Testing claim analysis...")
start = time.time()
result = analyze_claim(test_input)
print(f"Analysis completed in {time.time() - start:.2f} seconds")
print(result)