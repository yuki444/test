"""Suno API client for gcui-art/suno-api self-hosted instance."""
import os
import time
import requests


class SunoClient:
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or os.environ.get("SUNO_API_URL", "http://localhost:3000")).rstrip("/")
        self.session = requests.Session()

    def generate(self, prompt: str, tags: str, title: str, wait_audio: bool = True) -> list[dict]:
        """Generate music with custom lyrics and style tags."""
        payload = {
            "prompt": prompt,
            "tags": tags,
            "title": title,
            "make_instrumental": False,
            "wait_audio": wait_audio,
        }
        resp = self.session.post(f"{self.base_url}/api/custom_generate", json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()

    def get_song(self, song_id: str) -> dict:
        """Get song status and metadata."""
        resp = self.session.get(f"{self.base_url}/api/get", params={"ids": song_id}, timeout=30)
        resp.raise_for_status()
        return resp.json()[0]

    def wait_for_completion(self, song_id: str, timeout: int = 600) -> dict:
        """Poll until song generation is complete."""
        start = time.time()
        while time.time() - start < timeout:
            song = self.get_song(song_id)
            status = song.get("status", "")
            if status == "complete":
                return song
            if status == "error":
                raise RuntimeError(f"Song {song_id} generation failed: {song}")
            time.sleep(15)
        raise TimeoutError(f"Song {song_id} did not complete within {timeout}s")

    def extend_audio(self, song_id: str, prompt: str = "", continue_at: float = None) -> list[dict]:
        """Extend an existing song from a given timestamp."""
        payload = {"id": song_id, "prompt": prompt}
        if continue_at is not None:
            payload["continue_at"] = continue_at
        resp = self.session.post(f"{self.base_url}/api/extend_audio", json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()

    def get_limit(self) -> dict:
        """Check remaining API credits."""
        resp = self.session.get(f"{self.base_url}/api/get_limit", timeout=30)
        resp.raise_for_status()
        return resp.json()
