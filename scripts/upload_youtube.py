# coding: utf-8
"""
Agent④ — YouTube 投稿スクリプト

output/YYYY-MM-DD/results.json に video_path が記録された MP4 を
YouTube Data API v3 でアップロードします。

必要な環境変数（GitHub Secrets）:
  YOUTUBE_CLIENT_ID       : OAuth クライアント ID
  YOUTUBE_CLIENT_SECRET   : OAuth クライアントシークレット
  YOUTUBE_REFRESH_TOKEN   : 事前に取得したリフレッシュトークン

初回セットアップ:
  python scripts/upload_youtube.py --setup
  （ブラウザで認証してリフレッシュトークンを取得します）

通常実行:
  python scripts/upload_youtube.py --date 2026-06-25
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# ── 設定 ──────────────────────────────────────────────────────────────────────

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_URI      = "https://oauth2.googleapis.com/token"

# 動画のデフォルト設定
DEFAULT_CATEGORY_ID = "10"   # 10 = Music
DEFAULT_PRIVACY     = "public"   # "public" / "private" / "unlisted"

# 動画説明テンプレート
DESCRIPTION_TEMPLATE = """\
{title}

🎵 AI 作曲: Suno AI
🎼 スタイル: {tags}
📅 生成日: {date}

このトラックは Suno AI と Claude によって自動生成されました。

---
#SunoAI #AIMusic #自動作曲
"""

# ── 認証 ──────────────────────────────────────────────────────────────────────

def get_credentials() -> Credentials:
    """環境変数からリフレッシュトークンを使って Credentials を生成する。"""
    client_id     = os.environ.get("YOUTUBE_CLIENT_ID", "")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN", "")

    if not all([client_id, client_secret, refresh_token]):
        raise RuntimeError(
            "YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET / YOUTUBE_REFRESH_TOKEN "
            "が未設定です。\n"
            "  python scripts/upload_youtube.py --setup  で初回設定を行ってください。"
        )

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=client_id,
        client_secret=client_secret,
        scopes=YOUTUBE_SCOPES,
    )
    creds.refresh(Request())
    return creds


def setup_oauth():
    """
    ブラウザで OAuth 認証してリフレッシュトークンを取得する（初回のみ）。
    取得したトークンを GitHub Secret に設定してください。
    """
    from google_auth_oauthlib.flow import InstalledAppFlow

    client_id     = input("YouTube OAuth クライアント ID を入力: ").strip()
    client_secret = input("YouTube OAuth クライアントシークレットを入力: ").strip()

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": TOKEN_URI,
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, YOUTUBE_SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "=" * 60)
    print("✅ 認証成功！以下の値を GitHub Secrets に登録してください:")
    print(f"\n  YOUTUBE_CLIENT_ID     = {client_id}")
    print(f"  YOUTUBE_CLIENT_SECRET = {client_secret}")
    print(f"  YOUTUBE_REFRESH_TOKEN = {creds.refresh_token}")
    print("=" * 60)


# ── アップロード ───────────────────────────────────────────────────────────────

def upload_video(youtube, video_path: Path, song: dict, date_str: str) -> str:
    """
    YouTube に動画をアップロードして動画 URL を返す。
    """
    title = song.get("title", f"Suno AI Music - {date_str}")[:100]  # 100文字制限
    tags  = song.get("tags", "")
    description = DESCRIPTION_TEMPLATE.format(
        title=title, tags=tags, date=date_str
    )

    # キーワードタグ（カンマ区切りのタグを分割）
    keyword_tags = [t.strip() for t in tags.replace(",", " ").split() if t.strip()]
    keyword_tags += ["SunoAI", "AIMusic", "自動作曲"]

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": keyword_tags[:30],         # 最大30タグ
            "categoryId": DEFAULT_CATEGORY_ID,
            "defaultLanguage": "ja",
        },
        "status": {
            "privacyStatus": DEFAULT_PRIVACY,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10 MB チャンク
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    print(f"  📤 アップロード中: {video_path.name}")
    response = None
    retry    = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"    {pct}% 完了...")
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and retry < 5:
                wait = 2 ** retry * 5
                print(f"  ⚠️  サーバーエラー {e.resp.status}、{wait}s 後にリトライ...")
                time.sleep(wait)
                retry += 1
            else:
                raise

    video_id  = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"  ✅ アップロード完了: {video_url}")
    return video_url


# ── ヘルパー ──────────────────────────────────────────────────────────────────

def load_results(date_str: str) -> dict:
    p = Path("output") / date_str / "results.json"
    if not p.exists():
        raise FileNotFoundError(f"results.json が見つかりません: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_results(date_str: str, data: dict):
    p = Path("output") / date_str / "results.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── メイン ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="YouTube に動画を投稿する")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="対象日 (YYYY-MM-DD)")
    parser.add_argument("--setup", action="store_true",
                        help="初回 OAuth 認証（リフレッシュトークン取得）")
    parser.add_argument("--privacy", default=DEFAULT_PRIVACY,
                        choices=["public", "private", "unlisted"],
                        help="プライバシー設定 (default: public)")
    args = parser.parse_args()

    if args.setup:
        setup_oauth()
        return

    print(f"📺 Agent④ YouTube 投稿 開始: {args.date}")

    # 認証
    try:
        creds   = get_credentials()
        youtube = build("youtube", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ YouTube 認証失敗: {e}")
        sys.exit(1)

    # results.json 読み込み
    try:
        data = load_results(args.date)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)

    songs   = data.get("songs", [])
    ok      = 0
    failed  = 0

    for song in songs:
        # status フィールドがない場合は complete 扱い（generate_music.py の仕様）
        status = song.get("status", "complete")
        if status not in ("complete", ""):
            continue

        # 既に投稿済みならスキップ
        if song.get("youtube_url"):
            print(f"  ✅ 投稿済みスキップ: {song.get('title')} → {song['youtube_url']}")
            continue

        video_path_str = song.get("video_path")
        if not video_path_str:
            print(f"  ⚠️  video_path なし、スキップ: {song.get('id')}")
            failed += 1
            continue

        video_path = Path(video_path_str)
        if not video_path.exists():
            print(f"  ❌ 動画ファイルが見つかりません: {video_path}")
            failed += 1
            continue

        print(f"\n  処理中: {song.get('title','?')}")
        try:
            url = upload_video(youtube, video_path, song, args.date)
            song["youtube_url"] = url
            ok += 1
        except Exception as e:
            print(f"  ❌ アップロード失敗: {e}")
            failed += 1

    # results.json 更新（youtube_url を追加）
    save_results(args.date, data)

    print(f"\n{'='*50}")
    print(f"  YouTube 投稿完了: {ok} 曲 / 失敗: {failed} 曲")
    print(f"{'='*50}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
