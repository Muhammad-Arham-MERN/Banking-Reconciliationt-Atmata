# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Auth.js JWT verification service
Decodes and verifies Auth.js session tokens using the shared secret
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv
import jwt

load_dotenv()

logger = logging.getLogger(__name__)

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ

def verify_auth_token(token: str) -> Optional[dict]:
    """
    Verify an Auth.js JWT token and return user info.
    Uses symmetric HS256 verification with the shared NEXTAUTH_SECRET.

    Args:
        token: The JWT string from the Authorization header

    Returns:
        dict with user_id and email on success, or None on failure
    """
    secret = os.getenv("NEXTAUTH_SECRET", "")
    if not secret:
        logger.error("NEXTAUTH_SECRET is not configured")
        return None

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["sub"]},
        )
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email", ""),
        }
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected token verification error: {e}")
        return None
# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
