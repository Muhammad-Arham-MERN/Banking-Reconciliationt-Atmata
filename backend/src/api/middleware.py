# بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ
"""
API Middleware
Rate limiting, security, and request processing middleware
"""
import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ
class RateLimiter:
    """
    Simple rate limiter for API endpoints
    Limits requests per client IP to prevent abuse
    """

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_history = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed under rate limit"""
        current_time = time.time()
        minute_ago = current_time - 60

        # Clean old requests
        self.request_history[client_id] = [
            req_time for req_time in self.request_history[client_id]
            if req_time > minute_ago
        ]

        # Check if under limit
        if len(self.request_history[client_id]) < self.requests_per_minute:
            self.request_history[client_id].append(current_time)
            return True

        return False

# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=60)

async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware
    Limits requests to prevent abuse and ensure fair usage
    """
    client_id = request.client.host if request.client else "unknown"

    if not rate_limiter.is_allowed(client_id):
        logger.warning(f"⚠️  Rate limit exceeded for {client_id}")
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "details": {
                    "limit": rate_limiter.requests_per_minute,
                    "window": "1 minute"
                }
            }
        )

    response = await call_next(request)
    return response

async def security_middleware(request: Request, call_next):
    """
    Security middleware for input validation and threat detection
    """
    # Check for suspicious patterns
    suspicious_patterns = [
        '../',  # Path traversal attempt
        '<script',  # XSS attempt
        'SELECT ',  # SQL injection attempt
        'UNION ',   # SQL injection attempt
    ]

    # Check URL and headers for suspicious patterns
    url_str = str(request.url).lower()
    for pattern in suspicious_patterns:
        if pattern.lower() in url_str:
            logger.warning(f"🚨 Suspicious pattern detected from {request.client.host}: {pattern}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "bad_request",
                    "message": "Invalid request detected",
                    "details": {"reason": "suspicious_pattern"}
                }
            )

    response = await call_next(request)
    return response

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ