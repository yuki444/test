"""
Suno AI 初回ログインヘルパー

このスクリプトを一度だけ実行してブラウザでログインします。
ログイン情報は ~/.suno_playwright_profile に保存され、
以降の自動実行ではブラウザを開かずにログイン状態を維持できます。

使い方:
    python scripts/suno_login.py
"""

import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright

DEFAULT_PROFILE_DIR = Path.home() / ".suno_playwright_profile"


async def main():
    profile_dir = Path(
        os.environ.get("SUNO_PROFILE_DIR", "") or DEFAULT_PROFILE_DIR
    )
    profile_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Suno AI ログインヘルパー")
    print("=" * 60)
    print(f"プロファイル保存先: {profile_dir}")
    print()
    print("ブラウザが開きます。Suno AI (https://suno.com) にログインしてください。")
    print("ログイン完了後、このターミナルに戻ってきてください。")
    print()

    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,  # ログインはヘッドフルで
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        page = await context.new_page()
        await page.goto("https://suno.com", wait_until="networkidle")

        print("ブラウザが開きました。")
        print("まだログインしていない場合は右上の「Sign In」からログインしてください。")
        print()
        print("ログインが完了したら Enter を押してください...")
        input()

        # ログイン確認
        await page.goto("https://suno.com", wait_until="networkidle")
        url = page.url

        if any(kw in url for kw in ("sign-in", "login", "auth")):
            print("❌ まだログインできていないようです。もう一度試してください。")
        else:
            # Clerk セッションの存在確認
            try:
                await page.wait_for_function("() => !!window.Clerk?.session", timeout=10_000)
                session_info = await page.evaluate(
                    "() => ({ userId: window.Clerk.session.user?.id, email: window.Clerk.session.user?.primaryEmailAddress?.emailAddress })"
                )
                print("✅ ログイン成功!")
                if session_info.get("email"):
                    print(f"   アカウント: {session_info['email']}")
            except Exception:
                print("✅ ログイン成功! (セッション情報の取得はスキップ)")

        await context.close()

    print()
    print("ブラウザを閉じました。ログイン情報は保存されました。")
    print()
    print("次回以降の自動実行では、以下のコマンドで楽曲を生成できます:")
    print("  python scripts/generate_music.py --date $(date +%Y-%m-%d)")
    print()
    print("スケジュール実行の設定は docs/playwright_setup.md を参照してください。")


if __name__ == "__main__":
    asyncio.run(main())
