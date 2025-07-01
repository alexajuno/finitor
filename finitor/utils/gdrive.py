from __future__ import annotations

"""Google Drive helper utilities for Finitor.

Requires the following packages (added to requirements.txt):
    google-auth-oauthlib
    google-auth-httplib2
    google-api-python-client

Usage:
    from finitor.utils.gdrive import upload_to_drive
    upload_to_drive('/path/to/file', folder_id='optional_folder_id')

The first time it runs it will open a browser window asking for permission.
A refresh token is stored in ~/.finitor_drive_token.pickle so subsequent
calls are silent.
"""

from pathlib import Path
from typing import Optional
import pickle
import os

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# Drive API scope: only allow modifying files the app creates
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
# Where to cache OAuth credentials
TOKEN_PATH = Path.home() / ".finitor_drive_token.pickle"
# Default location to look for client secrets downloaded from Google Cloud
CLIENT_SECRET_PATH = Path.home() / ".finitor_credentials.json"


def _get_credentials() -> "google.oauth2.credentials.Credentials":  # type: ignore
    """Load stored credentials or run OAuth flow to obtain new ones."""
    creds = None
    if TOKEN_PATH.exists():
        creds = pickle.loads(TOKEN_PATH.read_bytes())
    # Refresh token if needed
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not CLIENT_SECRET_PATH.exists():
            raise FileNotFoundError(
                f"Google Drive client secret not found at {CLIENT_SECRET_PATH}. "
                "Download it from Google Cloud Console and place it there."
            )
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_PATH), SCOPES)
        creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_bytes(pickle.dumps(creds))
    return creds


def get_drive_service():
    """Build and return an authenticated Google Drive service client."""
    creds = _get_credentials()
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def upload_to_drive(file_path: str, folder_id: Optional[str] = None) -> str:
    """Upload a local file to Google Drive.

    Parameters
    ----------
    file_path : str
        Path to the file on the local filesystem.
    folder_id : Optional[str]
        ID of the Drive folder to upload into. If omitted, uploads to root.

    Returns
    -------
    str
        The file ID of the newly-uploaded file on Drive.
    """

    service = get_drive_service()
    file_metadata: dict = {"name": os.path.basename(file_path)}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaFileUpload(file_path, resumable=True)
    created = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    return created["id"] 