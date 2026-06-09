#!/usr/bin/env python3
"""
Claude APIのレート制限を確認し、usage-dashboard/api-limits.json に書き出す。
ANTHROPIC_API_KEY が設定されている場合のみ実際のAPIコールを行う。
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

DASHBOARD_DIR = Path(__file__).parent.parent / "usage-dashboard"
OUTPUT_FILE = DASHBOARD_DIR / "api-limits.json"


def parse_number(s):
    """文字列から数値へ変換（None/空文字は None を返す）"""
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def check_limits_via_api():
    """Anthropic APIにテストリクエストを送り、レート制限ヘッダーを取得する"""
    try:
        import anthropic
    except ImportError:
        print("❌ anthropic パッケージがインストールされていません。")
        print("   pip install anthropic")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY が設定されていません。")
        print("   APIレート制限の取得をスキップします。")
        return None

    client = anthropic.Anthropic(api_key=api_key)
    print("📡 APIに最小限のリクエストを送信中...")

    try:
        with client.messages.with_raw_response.create(
            model="claude-haiku-4-5",
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        ) as raw:
            headers = dict(raw.headers)
            # レスポンスを消費してエラーがないか確認
            _ = raw.parse()
    except anthropic.AuthenticationError:
        print("❌ APIキーが無効です。ANTHROPIC_API_KEY を確認してください。")
        return None
    except anthropic.RateLimitError as e:
        print(f"⚠️  レート制限に達しています: {e}")
        # ヘッダーはエラーレスポンスからも取得可能な場合がある
        headers = dict(e.response.headers) if hasattr(e, "response") else {}
    except Exception as e:
        print(f"❌ APIエラー: {e}")
        return None

    # x-ratelimit-* ヘッダーを解析
    data = {
        "checkedAt": datetime.utcnow().isoformat() + "Z",
        # Requests per minute
        "limitRpm":     parse_number(headers.get("x-ratelimit-limit-requests")),
        "remainingRpm": parse_number(headers.get("x-ratelimit-remaining-requests")),
        "resetRpm":     headers.get("x-ratelimit-reset-requests"),
        # Tokens per minute
        "limitTpm":     parse_number(headers.get("x-ratelimit-limit-tokens")),
        "remainingTpm": parse_number(headers.get("x-ratelimit-remaining-tokens")),
        "resetTpm":     headers.get("x-ratelimit-reset-tokens"),
        # Tokens per day
        "limitTpd":     parse_number(headers.get("x-ratelimit-limit-tokens-day")),
        "remainingTpd": parse_number(headers.get("x-ratelimit-remaining-tokens-day")),
        # Input tokens per minute (一部ティアで別途制限あり)
        "limitItpm":     parse_number(headers.get("x-ratelimit-limit-input-tokens")),
        "remainingItpm": parse_number(headers.get("x-ratelimit-remaining-input-tokens")),
        # retry-after (429の場合)
        "retryAfter": headers.get("retry-after"),
    }

    # 使用トークン情報 (今回のリクエスト分)
    if "x-request-id" in headers:
        data["lastRequestId"] = headers["x-request-id"]

    return data


def print_summary(data):
    """結果を読みやすく表示"""
    print()
    print("=" * 50)
    print("  Claude API レート制限サマリー")
    print("=" * 50)
    print(f"  確認時刻: {data['checkedAt']}")
    print()

    def show(label, rem, lim, reset=None):
        if lim is None:
            print(f"  {label:30s} 情報なし")
            return
        used = lim - (rem or 0) if rem is not None else "?"
        pct = (used / lim * 100) if isinstance(used, (int, float)) else 0
        bar_len = 20
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        status = "🔴" if pct >= 90 else "🟡" if pct >= 70 else "🟢"
        print(f"  {status} {label:28s} [{bar}] {pct:5.1f}%")
        print(f"     残: {rem:,} / 上限: {lim:,}" if rem is not None else f"     上限: {lim:,}")
        if reset:
            print(f"     リセット: {reset}")
        print()

    show("リクエスト/分 (RPM)",   data["remainingRpm"],  data["limitRpm"],  data["resetRpm"])
    show("トークン/分 (TPM)",     data["remainingTpm"],  data["limitTpm"],  data["resetTpm"])
    show("トークン/日 (TPD)",     data["remainingTpd"],  data["limitTpd"])
    show("入力トークン/分 (ITPM)", data["remainingItpm"], data["limitItpm"])

    if data.get("retryAfter"):
        print(f"  ⏳ retry-after: {data['retryAfter']}秒")


def main():
    print("🔍 Claude API 使用量チェッカー")
    print()

    data = check_limits_via_api()

    if data is None:
        # APIキーなし or エラーの場合でも既存データを表示
        if OUTPUT_FILE.exists():
            with open(OUTPUT_FILE) as f:
                data = json.load(f)
            print(f"📂 既存のデータを表示: {OUTPUT_FILE}")
            print_summary(data)
        else:
            print("ℹ️  ANTHROPIC_API_KEY を設定すると、APIのレート制限をリアルタイムで確認できます。")
            print("   ダッシュボードは usage-dashboard/index.html をブラウザで開いてください。")
        sys.exit(0)

    # JSON ファイルに保存
    DASHBOARD_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print_summary(data)
    print(f"✅ {OUTPUT_FILE} に保存しました")
    print()
    print("💡 ダッシュボード: usage-dashboard/index.html をブラウザで開いてください")
    print("   30秒ごとに自動でデータを読み込みます")


if __name__ == "__main__":
    main()
