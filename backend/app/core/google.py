from functools import partial
from google.oauth2 import id_token
from google.auth.transport.requests import Request
from app.core.config import settings

def verify_google_identity(token: str) -> dict:
    claims = id_token.verify_oauth2_token(token, partial(Request(), timeout=10), settings.google_client_id)
    if not claims.get("email_verified") or not claims.get("email") or not claims.get("sub"):
        raise ValueError("A verified Google email is required")
    return claims
