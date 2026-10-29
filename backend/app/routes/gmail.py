"""
Gmail OAuth API routes.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from .. import gmail_service
from ..schemas import GmailAuthStatus

router = APIRouter(prefix="/api/gmail", tags=["gmail"])


class AuthUrlResponse(BaseModel):
    url: str


@router.get("/auth-url", response_model=AuthUrlResponse)
def get_auth_url():
    """Return the Google OAuth consent URL."""
    url = gmail_service.get_auth_url()
    return {"url": url}


@router.get("/callback")
def oauth_callback(code: str):
    """Handle the OAuth callback from Google."""
    try:
        gmail_service.handle_oauth_callback(code)
        # Redirect back to the frontend dashboard
        return RedirectResponse("http://localhost:5173/?auth=success")
    except Exception as e:
        return RedirectResponse(f"http://localhost:5173/?auth=error&msg={str(e)}")


@router.get("/status", response_model=GmailAuthStatus)
def auth_status():
    """Check if the application has valid Gmail credentials."""
    is_auth = gmail_service.is_authenticated()
    email = gmail_service.get_user_email() if is_auth else None
    
    return GmailAuthStatus(
        authenticated=is_auth,
        email=email,
        message="Authenticated" if is_auth else "Not authenticated"
    )


@router.post("/disconnect")
def disconnect_gmail():
    """Disconnect Gmail and remove credentials."""
    gmail_service.disconnect()
    return {"message": "Disconnected"}
