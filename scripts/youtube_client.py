"""YouTube Data API v3 client using OAuth refresh-token credentials.

Authentication uses three values supplied via environment variables / GitHub Secrets:
  YOUTUBE_CLIENT_ID
  YOUTUBE_CLIENT_SECRET
  YOUTUBE_REFRESH_TOKEN

These are obtained once via a local OAuth consent flow (see docs/youtube_setup.md).
No browser interaction is needed at run time — the refresh token mints access
tokens automatically.
"""
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeClient:
    def __init__(self):
        client_id = os.environ.get("YOUTUBE_CLIENT_ID")
        client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
        refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")
        missing = [
            name for name, val in [
                ("YOUTUBE_CLIENT_ID", client_id),
                ("YOUTUBE_CLIENT_SECRET", client_secret),
                ("YOUTUBE_REFRESH_TOKEN", refresh_token),
            ] if not val
        ]
        if missing:
            raise RuntimeError(f"Missing YouTube credentials: {', '.join(missing)}")

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=TOKEN_URI,
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
        self.service = build("youtube", "v3", credentials=creds)

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str] = None,
        category_id: str = "10",   # 10 = Music
        privacy_status: str = "public",
    ) -> dict:
        """Upload a video and return the YouTube API response.

        privacy_status: "public", "unlisted", or "private".
        """
        body = {
            "snippet": {
                "title": title[:100],            # YouTube title hard limit
                "description": description[:5000],  # YouTube description hard limit
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }
        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True)
        request = self.service.videos().insert(
            part="snippet,status", body=body, media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"    Upload {int(status.progress() * 100)}%")
        return response
