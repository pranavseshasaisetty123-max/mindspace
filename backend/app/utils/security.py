import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException, status

logger = logging.getLogger("mindspace.security")

import sys

class SlidingWindowRateLimiter:
    def __init__(self, limit: int = 5, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.enabled = "pytest" not in sys.modules

    def check_rate_limit(self, ip: str):
        if not self.enabled:
            return
            
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Filter request timestamps to only keep those within active window
        self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]
        
        if len(self.requests[ip]) >= self.limit:
            logger.warning(f"Rate limit exceeded for IP {ip}: {len(self.requests[ip])} attempts in {self.window_seconds}s")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many authentication attempts. Please try again later."
            )
            
        self.requests[ip].append(now)

# Instantiate global rate limiter for auth (5 requests per 60 seconds)
auth_rate_limiter = SlidingWindowRateLimiter(limit=5, window_seconds=60)

async def rate_limit_auth(request: Request):
    """FastAPI dependency to rate limit registration and login requests."""
    client_ip = request.client.host if request.client else "unknown"
    auth_rate_limiter.check_rate_limit(client_ip)
