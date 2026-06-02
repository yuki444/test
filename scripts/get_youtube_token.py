"""One-time helper: obtain a YouTube OAuth refresh token via a local consent flow.

Run this once on your own machine:

    python scripts/get_youtube_token.py

It opens a browser, asks you to authorize, then prints a refresh token to store
as the YOUTUBE_REFRESH_TOKEN GitHub Secret. See docs/youtube_setup.md.

You will be prompted for the Client ID and Client Secret created in the Google
Cloud console (or set them via YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET env vars).
"""
import os

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID") or input("Client ID: ").strip()
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET") or input("Client Secret: ").strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    # access_type=offline + prompt=consent guarantees a refresh token is returned
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    print("\n" + "=" * 60)
    print("SUCCESS! Add these to your GitHub Secrets:")
    print("=" * 60)
    print(f"YOUTUBE_CLIENT_ID     = {client_id}")
    print(f"YOUTUBE_CLIENT_SECRET = {client_secret}")
    print(f"YOUTUBE_REFRESH_TOKEN = {creds.refresh_token}")
    print("=" * 60)


if __name__ == "__main__":
    main()
