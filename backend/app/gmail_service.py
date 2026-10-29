"""
Gmail OAuth 2.0 + Draft-creation service.

NEVER sends an email — only creates drafts.
"""

import os
import json
import base64
import logging
from email.mime.text import MIMEText
from typing import Optional, Tuple

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]  # minimum scope for drafts

_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "token.json")
_CREDENTIALS: Optional[Credentials] = None


def _get_client_config() -> dict:
    """Build the OAuth client config from env vars."""
    return {
        "web": {
            "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
            "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/gmail/callback")],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def get_auth_url() -> str:
    """Return the Google OAuth consent URL."""
    flow = Flow.from_client_config(_get_client_config(), scopes=SCOPES)
    flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/gmail/callback")
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def handle_oauth_callback(code: str) -> Credentials:
    """Exchange the authorization code for credentials and persist them."""
    global _CREDENTIALS
    flow = Flow.from_client_config(_get_client_config(), scopes=SCOPES)
    flow.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/gmail/callback")
    flow.fetch_token(code=code)
    _CREDENTIALS = flow.credentials
    _save_token(_CREDENTIALS)
    return _CREDENTIALS


def _save_token(creds: Credentials):
    """Persist credentials to disk."""
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES,
    }
    with open(_TOKEN_PATH, "w") as f:
        json.dump(token_data, f)


def _load_token() -> Optional[Credentials]:
    """Load persisted credentials from disk."""
    if not os.path.exists(_TOKEN_PATH):
        return None
    with open(_TOKEN_PATH) as f:
        data = json.load(f)
    creds = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )
    return creds


def get_credentials() -> Optional[Credentials]:
    """Return valid credentials, refreshing if needed."""
    global _CREDENTIALS
    if _CREDENTIALS and _CREDENTIALS.valid:
        return _CREDENTIALS

    creds = _load_token()
    if not creds:
        return None

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return None

    _CREDENTIALS = creds
    return _CREDENTIALS


def is_authenticated() -> bool:
    """Check if we have valid Gmail credentials."""
    creds = get_credentials()
    return creds is not None and (creds.valid or creds.refresh_token is not None)


def get_user_email() -> Optional[str]:
    """Return the authenticated user's email address."""
    creds = get_credentials()
    if not creds:
        return None
    try:
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress")
    except Exception as e:
        logger.error(f"Failed to get user email: {e}")
        return None


def create_draft(to_email: str, subject: str, body: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Create a Gmail draft. NEVER sends.

    Returns (success, draft_id, error_message).
    """
    creds = get_credentials()
    if not creds:
        return False, None, "Not authenticated with Gmail"

    try:
        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(body, "html")
        message["to"] = to_email
        message["subject"] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        draft_body = {"message": {"raw": raw}}

        draft = service.users().drafts().create(userId="me", body=draft_body).execute()
        draft_id = draft.get("id", "")
        logger.info(f"Draft created for {to_email} — ID: {draft_id}")
        return True, draft_id, None

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to create draft for {to_email}: {error_msg}")
        return False, None, error_msg


def disconnect():
    """Remove stored credentials."""
    global _CREDENTIALS
    _CREDENTIALS = None
    if os.path.exists(_TOKEN_PATH):
        os.remove(_TOKEN_PATH)
