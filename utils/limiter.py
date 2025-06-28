import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=5, per_seconds=60):
        self.max_requests = max_requests
        self.per_seconds = per_seconds
        self.request_times = deque()
        
    def allow(self):
        now = time.time()
        # Remove old requests
        while self.request_times and self.request_times[0] <= now - self.per_seconds:
            self.request_times.popleft()
            
        if len(self.request_times) < self.max_requests:
            self.request_times.append(now)
            return True
        return False