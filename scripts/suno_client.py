"""
Suno AI client — Playwright persistent-context + direct internal API.

仕組み:
  1. Playwright の persistent context でブラウザを起動（ログイン状態を保持）
  2. window.Clerk.session.getToken() で短命 JWT を取得
  3. aiohttp で Suno の内部 API を直接呼び出す

追加コスト: ¥0（既存の Suno Pro クレジットを使用）
初回のみ: python scripts/suno_login.py でブラウザを使ってログイン

Note: Suno は非公式 API のため URL・ペイロードが変わる場合があります。
      変更が必要な場合は INTERNAL_API_BASE / GENERATE_ENDPOINT 等を更新してください。
"""

import asyncio
import atexit
import os
import time
from pathlib import Path

import aiohttp
from playwright.async_api import async_playwright, BrowserContext, Page

# ── 設定 ─────────────────────────────────────────────────────────────────────

INTERNAL_API_BASE = "https://studio-api-prod.suno.com"
GENERATE_ENDPOINT = f"{INTERNAL_API_BASE}/api/generate/v2-web/"  # 2026-06: v2→v2-web
FEED_ENDPOINT     = f"{INTERNAL_API_BASE}/api/feed/v3"           # 2026-06: v2(GET)→v3(POST)
BILLING_ENDPOINT  = f"{INTERNAL_API_BASE}/api/billing/info/"

# Suno のモデルバージョン（2026-06 時点）
# ブラウザ DevTools で確認した値: chirp-fenix
SUNO_MODEL_VERSION = "chirp-fenix"

DEFAULT_PROFILE_DIR = Path.home() / ".suno_playwright_profile"


# ── メインクライアント ──────────────────────────────────────────────────────

class SunoClient:
    """
    既存の suno_client.py (gcui-art 版) と同じシグネチャを持つ drop-in 置き換え。
    generate_music.py を変更なしで動かせます。
    """

    def __init__(self, base_url: str = None, profile_dir: Path = None, headless: bool = True):
        # base_url は後方互換のため残す（使用しない）
        self.profile_dir = Path(
            profile_dir
            or os.environ.get("SUNO_PROFILE_DIR", "")
            or DEFAULT_PROFILE_DIR
        )
        self.headless = headless

        self._playwright = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

        self._token: str | None = None
        self._token_expiry: float = 0.0

        atexit.register(self._shutdown)

    # ── 同期パブリック API（generate_music.py から呼ばれる） ───────────────

    def generate(self, prompt: str, tags: str, title: str, wait_audio: bool = True) -> list[dict]:
        """カスタム歌詞＋スタイルで楽曲を生成する（通常 2 曲返る）。"""
        return self._run(self._generate(prompt, tags, title, wait_audio))

    def get_song(self, song_id: str) -> dict:
        """単一曲のステータス・メタデータを取得する。"""
        return self._run(self._get_songs([song_id]))[0]

    def wait_for_completion(self, song_id: str, timeout: int = 600) -> dict:
        """曲が complete になるまでポーリングする。"""
        return self._run(self._poll_until_complete(song_id, timeout))

    def extend_audio(self, song_id: str, prompt: str = "", continue_at: float = None) -> list[dict]:
        """既存の曲を延長する。"""
        return self._run(self._extend(song_id, prompt, continue_at))

    def get_limit(self) -> dict:
        """残りクレジットを確認する。"""
        return self._run(self._billing())

    # ── 内部: asyncio ループ管理 ─────────────────────────────────────────

    def _run(self, coro):
        loop = self._get_loop()
        return loop.run_until_complete(coro)

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def _shutdown(self):
        """atexit で呼ばれる。ブラウザを閉じる。"""
        if self._loop and not self._loop.is_closed():
            try:
                self._loop.run_until_complete(self._close_browser())
            except Exception:
                pass
            self._loop.close()

    # ── 内部: ブラウザ管理 ───────────────────────────────────────────────

    async def _ensure_browser(self):
        """必要に応じてブラウザを起動し、suno.com にナビゲートする。"""
        if self._page is not None:
            return  # already running

        self._playwright = await async_playwright().start()
        self.profile_dir.mkdir(parents=True, exist_ok=True)

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            headless=self.headless,
            # bot 検出を回避するための設定
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            ignore_default_args=["--enable-automation"],
            # 実際の Chrome と区別されにくくするための UA
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        self._page = await self._context.new_page()

        # suno.com にアクセスして Clerk を初期化
        # wait_until="load" を使う（networkidle は SPA で永遠に終わらないため）
        await self._page.goto("https://suno.com", wait_until="load", timeout=60_000)

        # ログインチェック
        if any(kw in self._page.url for kw in ("sign-in", "login", "auth")):
            await self._close_browser()
            raise RuntimeError(
                "\n❌ Suno AI にログインしていません。\n"
                "   初回は以下を実行してブラウザでログインしてください:\n"
                "     python scripts/suno_login.py\n"
            )

        # Clerk の初期化を待つ
        await self._page.wait_for_function("() => !!window.Clerk?.session", timeout=30_000)
        print("✅ Suno AI ブラウザセッション確立")

    async def _close_browser(self):
        if self._context:
            await self._context.close()
            self._context = None
            self._page = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    # ── 内部: トークン管理 ──────────────────────────────────────────────

    async def _get_token(self) -> str:
        """Clerk JWT を取得・キャッシュする（~55 秒でリフレッシュ）。"""
        await self._ensure_browser()

        if self._token and time.time() < self._token_expiry:
            return self._token

        # ブラウザ内で Clerk のトークンを取得
        result = await self._page.evaluate(
            "async () => window.Clerk.session.getToken()"
        )
        if not result:
            raise RuntimeError("Clerk トークンの取得に失敗しました。セッションが切れているかもしれません。")

        self._token = result
        self._token_expiry = time.time() + 55  # 60s の JWT を 55s でリフレッシュ
        return self._token

    async def _headers(self) -> dict:
        token = await self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }

    # ── 内部: API 呼び出し ────────────────────────────────────────────────

    async def _generate(self, prompt: str, tags: str, title: str, wait_audio: bool) -> list[dict]:
        headers = await self._headers()
        # 2026-06 実測ペイロード（Custom Mode / v2-web）
        payload = {
            "token": None,
            "generation_type": "TEXT",
            "mv": SUNO_MODEL_VERSION,
            "prompt": prompt,                # 歌詞（Custom Mode）
            "tags": tags,                    # スタイルタグ
            "title": title,
            "gpt_description_prompt": "",    # Custom Mode では空
            "make_instrumental": False,
            "user_uploaded_images_b64": None,
            "metadata": {
                "web_client_pathname": "/create",
                "is_max_mode": False,
                "is_mumble": False,
                "create_mode": "custom",
                "disable_volume_normalization": False,
                "lyrics_model": "default",
            },
            "override_fields": [],
            "cover_clip_id": None,
        }

        data = None
        for attempt in range(3):  # 503 など一時エラーは最大3回リトライ
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    GENERATE_ENDPOINT,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status == 401:
                        # トークン切れ → リフレッシュして即リトライ
                        self._token = None
                        self._token_expiry = 0
                        headers = await self._headers()
                        continue
                    if resp.status in (502, 503, 504):
                        wait = 20 * (attempt + 1)
                        print(f"  サーバーエラー {resp.status}、{wait}秒後にリトライ ({attempt+1}/3)...")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = await resp.json()
                    break

        if data is None:
            raise RuntimeError("Suno API が503を繰り返しています。しばらく時間をおいて再試行してください。")

        clips = data.get("clips", [])
        if not clips:
            raise RuntimeError(f"生成失敗 — API レスポンス: {data}")

        if wait_audio:
            results = []
            for clip in clips:
                completed = await self._poll_until_complete(clip["id"])
                results.append(completed)
            return results

        return clips

    async def _get_songs(self, ids: list[str]) -> list[dict]:
        headers = await self._headers()
        # feed/v3 は POST + JSON body（旧 feed/v2 は GET + query params）
        async with aiohttp.ClientSession() as session:
            async with session.post(
                FEED_ENDPOINT,
                headers=headers,
                json={"ids": ids},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                # v3 は {"clips": [...]} 形式の可能性があるため両対応
                if isinstance(data, list):
                    return data
                return data.get("clips", data.get("data", []))

    async def _poll_until_complete(self, song_id: str, timeout: int = 600) -> dict:
        start = time.time()
        while time.time() - start < timeout:
            songs = await self._get_songs([song_id])
            if not songs:
                await asyncio.sleep(15)
                continue
            song = songs[0]
            status = song.get("status", "")
            if status == "complete":
                return song
            if status in ("error", "failed"):
                raise RuntimeError(f"曲 {song_id} の生成が失敗しました: {song}")
            # streaming 中はログを出す
            if status == "streaming":
                pct = song.get("metadata", {}).get("stream_audio_url_completion_percentage", 0)
                print(f"    ストリーミング中 {pct:.0f}%...")
            await asyncio.sleep(15)
        raise TimeoutError(f"曲 {song_id} が {timeout}s 以内に完了しませんでした")

    async def _extend(self, song_id: str, prompt: str, continue_at: float | None) -> list[dict]:
        headers = await self._headers()
        # v2-web 形式（2026-06）: continue_clip_id で既存曲を延長
        payload: dict = {
            "token": None,
            "generation_type": "TEXT",
            "mv": SUNO_MODEL_VERSION,
            "prompt": prompt or "",
            "tags": "",
            "title": "",
            "gpt_description_prompt": "",
            "make_instrumental": False,
            "user_uploaded_images_b64": None,
            "metadata": {
                "web_client_pathname": "/create",
                "is_max_mode": False,
                "is_mumble": False,
                "create_mode": "custom",
                "disable_volume_normalization": False,
                "lyrics_model": "default",
            },
            "override_fields": [],
            "cover_clip_id": None,
            "continue_clip_id": song_id,
        }
        if continue_at is not None:
            payload["continue_at"] = continue_at

        async with aiohttp.ClientSession() as session:
            async with session.post(
                GENERATE_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 400:
                    # 延長が失敗した場合は元の曲をそのまま返す（延長なし）
                    print(f"    延長スキップ（400エラー）: 元の曲をそのまま使用します")
                    original = await self._poll_until_complete(song_id)
                    return [original]
                resp.raise_for_status()
                data = await resp.json()

        clips = data.get("clips", [])
        results = []
        for clip in clips:
            completed = await self._poll_until_complete(clip["id"])
            results.append(completed)
        return results

    async def _billing(self) -> dict:
        headers = await self._headers()
        async with aiohttp.ClientSession() as session:
            async with session.get(
                BILLING_ENDPOINT,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
