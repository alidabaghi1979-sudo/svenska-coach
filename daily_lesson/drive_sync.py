"""Upload lesson files to your personal Google Drive (OAuth refresh token).

Uses the same [gdrive_oauth] credentials as Svenska Coach's oauth_setup.py.
The lesson folder is found by name or created, and remembered in state.json.
Files get "anyone with the link can view" so the app can play them on the phone
(same approach as the app's drive_upload.py).
"""
from __future__ import annotations

import json
import logging
import mimetypes
from pathlib import Path

from http_utils import APIError, request_with_retry
from settings import Settings

log = logging.getLogger(__name__)

TOKEN_URL = "https://oauth2.googleapis.com/token"
FILES_URL = "https://www.googleapis.com/drive/v3/files"
UPLOAD_URL = "https://www.googleapis.com/upload/drive/v3/files"
FOLDER_MIME = "application/vnd.google-apps.folder"


class DriveClient:
    def __init__(self, settings: Settings):
        if not settings.gdrive_enabled:
            raise ValueError("Google Drive credentials (GDRIVE_*) are not configured")
        self.s = settings
        self._token: str | None = None

    @property
    def headers(self) -> dict[str, str]:
        if not self._token:
            resp = request_with_retry("POST", TOKEN_URL, data={
                "client_id": self.s.gdrive_client_id,
                "client_secret": self.s.gdrive_client_secret,
                "refresh_token": self.s.gdrive_refresh_token,
                "grant_type": "refresh_token",
            }, max_attempts=3)
            self._token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {self._token}"}

    def ensure_folder(self, cached_id: str | None) -> str:
        if cached_id:
            try:
                r = request_with_retry("GET", f"{FILES_URL}/{cached_id}", headers=self.headers,
                                       params={"fields": "id,trashed"}, max_attempts=2).json()
                if not r.get("trashed"):
                    return cached_id
            except APIError as exc:
                log.warning("Cached Drive folder not usable (%s) — recreating", exc.status)
        name = self.s.gdrive_folder_name.replace("'", "\\'")
        q = f"name = '{name}' and mimeType = '{FOLDER_MIME}' and trashed = false"
        found = request_with_retry("GET", FILES_URL, headers=self.headers,
                                   params={"q": q, "fields": "files(id)", "spaces": "drive"}).json()
        if found.get("files"):
            return found["files"][0]["id"]
        created = request_with_retry("POST", FILES_URL, headers=self.headers,
                                     params={"fields": "id"},
                                     json={"name": self.s.gdrive_folder_name, "mimeType": FOLDER_MIME}).json()
        log.info("Created Drive folder '%s'", self.s.gdrive_folder_name)
        return created["id"]

    def upload(self, path: Path, folder_id: str, public: bool = True) -> tuple[str, str]:
        """Resumable upload (works for any size). Returns (file_id, direct play link)."""
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        init = request_with_retry(
            "POST", UPLOAD_URL,
            params={"uploadType": "resumable", "fields": "id,webViewLink"},
            headers={**self.headers, "Content-Type": "application/json; charset=UTF-8",
                     "X-Upload-Content-Type": mime},
            data=json.dumps({"name": path.name, "parents": [folder_id]}),
        )
        session_url = init.headers["Location"]
        resp = request_with_retry("PUT", session_url, headers={"Content-Type": mime},
                                  data=path.read_bytes(), timeout=600).json()
        file_id = resp["id"]
        if public:
            request_with_retry("POST", f"{FILES_URL}/{file_id}/permissions", headers=self.headers,
                               json={"role": "reader", "type": "anyone"})
        log.info("Uploaded %s to Google Drive", path.name)
        return file_id, f"https://drive.google.com/uc?export=download&id={file_id}"
