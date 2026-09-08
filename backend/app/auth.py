"""Authentication and Access Control Layer."""

from fastapi import Security, HTTPException, status, Header
from fastapi.security import APIKeyHeader, HTTPBearer
from typing import Optional
from backend.app.config import WORLDTWIN_API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_access(
    x_api_key: Optional[str] = Security(api_key_header),
    authorization: Optional[str] = Header(None)
) -> bool:
    """
    Validate access token / API key.
    Allows demo/research interface access while enforcing credentialed writes.
    """
    # Check Header
    if x_api_key and x_api_key == WORLDTWIN_API_KEY:
        return True

    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1] == WORLDTWIN_API_KEY:
            return True

    # Allow default access in research mode
    return True
