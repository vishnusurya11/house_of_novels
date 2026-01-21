"""
YouTube OAuth Credentials Management

Handles OAuth 2.0 authentication with automatic token refresh.
Tokens are stored in .youtube_token.json for persistence.
"""

import os
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from src.config import (
    YOUTUBE_CLIENT_SECRETS_FILE,
    YOUTUBE_TOKEN_FILE,
    YOUTUBE_SCOPES,
)


class YouTubeCredentialsManager:
    """Manage YouTube API credentials with secure token storage."""

    def __init__(
        self,
        client_secrets_file: Path = None,
        token_file: Path = None,
        scopes: list[str] = None,
    ):
        self.client_secrets_file = client_secrets_file or YOUTUBE_CLIENT_SECRETS_FILE
        self.token_file = token_file or YOUTUBE_TOKEN_FILE
        self.scopes = scopes or YOUTUBE_SCOPES
        self.credentials = None

    def get_credentials(self) -> Credentials:
        """Get valid credentials, refreshing or re-authenticating as needed."""
        self._load_credentials()

        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self._refresh_credentials()
            else:
                self._authenticate()

            self._save_credentials()

        return self.credentials

    def get_youtube_service(self):
        """Get authenticated YouTube API service."""
        credentials = self.get_credentials()
        return build('youtube', 'v3', credentials=credentials)

    def _load_credentials(self):
        """Load credentials from token file."""
        if os.path.exists(self.token_file):
            try:
                self.credentials = Credentials.from_authorized_user_file(
                    str(self.token_file),
                    self.scopes
                )
            except Exception as e:
                print(f">>> Warning: Could not load credentials: {e}")
                self.credentials = None

    def _refresh_credentials(self):
        """Refresh expired access token using refresh token."""
        try:
            self.credentials.refresh(Request())
            print(">>> Access token refreshed successfully.")
        except Exception as e:
            print(f">>> Token refresh failed: {e}")
            print(">>> Re-authenticating...")
            self._authenticate()

    def _authenticate(self):
        """Run OAuth flow to get new credentials."""
        if not os.path.exists(self.client_secrets_file):
            raise FileNotFoundError(
                f"client_secrets.json not found at {self.client_secrets_file}\n"
                "To set up YouTube API:\n"
                "1. Go to https://console.cloud.google.com/\n"
                "2. Create a project and enable YouTube Data API v3\n"
                "3. Create OAuth 2.0 credentials (Desktop app)\n"
                "4. Download and save as 'client_secrets.json' in project root"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self.client_secrets_file),
            self.scopes
        )

        # Use offline access to get refresh token
        self.credentials = flow.run_local_server(
            port=8080,
            access_type='offline',
            prompt='consent'  # Force consent to always get refresh token
        )
        print(">>> YouTube authentication completed successfully.")

    def _save_credentials(self):
        """Save credentials to token file."""
        if self.credentials:
            with open(self.token_file, 'w') as f:
                f.write(self.credentials.to_json())
            print(f">>> Credentials saved to {self.token_file}")

    def validate_credentials(self) -> bool:
        """Check if credentials are valid without triggering auth flow."""
        self._load_credentials()
        if not self.credentials:
            return False
        if self.credentials.expired and self.credentials.refresh_token:
            try:
                self._refresh_credentials()
                self._save_credentials()
                return True
            except Exception:
                return False
        return self.credentials.valid

    def revoke_credentials(self):
        """Revoke current credentials and delete token file."""
        import requests

        if self.credentials:
            try:
                requests.post(
                    'https://oauth2.googleapis.com/revoke',
                    params={'token': self.credentials.token},
                    headers={'content-type': 'application/x-www-form-urlencoded'}
                )
            except Exception as e:
                print(f">>> Warning: Could not revoke token: {e}")

        if os.path.exists(self.token_file):
            os.remove(self.token_file)

        self.credentials = None
        print(">>> Credentials revoked and token file deleted.")


def get_youtube_service():
    """Convenience function to get authenticated YouTube service."""
    manager = YouTubeCredentialsManager()
    return manager.get_youtube_service()


def validate_youtube_credentials() -> bool:
    """Check if YouTube credentials are valid."""
    manager = YouTubeCredentialsManager()
    return manager.validate_credentials()
