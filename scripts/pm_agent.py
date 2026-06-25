# coding: utf-8
"""
PM エージェント — 日次実行サマリを Notion に投稿する

必要な環境変数（GitHub Secrets / .env）:
  NOTION_TOKEN        : Notion Integration トークン（secret_xxx...）
  NOTION_DATABASE_ID  : レポートを書き込む Notion データベースの ID

使い方（手動）:
  python scripts/pm_agent.py --date 2026-06-25

run_daily.bat / post_process.yml の末尾から自動呼出しされます。
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# ── 設定 ──────────────────────────────────────────────────────────────────────

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION  = "2022-06-28"

# ── ヘルパー ──────────────────────────────────────────────────────────────────

def notion_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def load_results(date_str: str) -> dict | None:
    """output/YYYY-MM-DD/results.json を読み込む。なければ None。"""
    p = Path("output") / date_str / "results.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️  results.json の読み込み失敗: {e}")
        return None


# ── 分析 ──────────────────────────────────────────────────────────────────────

def analyze(data: dict, date_str: str) -> dict:
    """
    results.json を分析してレポート用 dict を返す。

    results.json の期待フォーマット:
    {
      "date": "2026-06-25",
      "songs": [
        {
          "id": "...",
          "title": "...",
          "tags": "pop rock",
          "duration": 210.5,        # 秒
          "status": "complete",
          "audio_url": "https://...",
          "video_url": "https://...",
          "youtube_url": "https://...",  # upload_youtube.py が書き込む
          "style_key": "pop"
        }, ...
      ],
      "errors": ["エラーメッセージ1", ...]
    }
    """
    songs   = data.get("songs", [])
    errors  = data.get("errors", [])

    total   = len(songs)
    ok      = [s for s in songs if s.get("status") == "complete"]
    failed  = [s for s in songs if s.get("status") in ("error", "failed")]

    durations = [s.get("duration", 0) for s in ok if s.get("duration")]
    avg_dur   = sum(durations) / len(durations) if durations else 0

    short_songs = [s for s in ok if s.get("duration", 999) < 180]  # 3 分未満
    yt_uploaded = [s for s in ok if s.get("youtube_url")]

    # スタイル別集計
    styles_done: dict[str, int] = {}
    for s in ok:
        key = s.get("style_key") or s.get("tags", "unknown")
        styles_done[key] = styles_done.get(key, 0) + 1

    # 全体ステータス判定
    if total == 0 or len(errors) > 0 and total == 0:
        overall = "❌ 失敗"
    elif failed:
        overall = "⚠️ 一部失敗"
    elif short_songs:
        overall = "⚠️ 短い曲あり"
    else:
        overall = "✅ 正常"

    # 問題点の列挙
    issues = list(errors)
    if failed:
        issues.append(f"{len(failed)} 曲が生成失敗しました (IDs: {[s['id'] for s in failed]})")
    if short_songs:
        for s in short_songs:
            issues.append(
                f"曲 「{s.get('title','?')}」の尺が短い: {s.get('duration',0):.0f}秒 "
                f"（目標: 240秒以上）→ 歌詞を増やしてください"
            )

    return {
        "date":         date_str,
        "overall":      overall,
        "total":        total,
        "ok":           len(ok),
        "failed":       len(failed),
        "avg_dur_sec":  round(avg_dur, 1),
        "avg_dur_min":  f"{int(avg_dur//60)}:{int(avg_dur%60):02d}",
        "short_count":  len(short_songs),
        "yt_count":     len(yt_uploaded),
        "styles_done":  styles_done,
        "issues":       issues,
        "songs":        ok,
    }


# ── Notion 投稿 ───────────────────────────────────────────────────────────────

def build_notion_page(db_id: str, r: dict) -> dict:
    """Notion ページ作成用のペイロードを組み立てる。"""

    # --- 本文ブロック ---
    blocks = []

    def h2(text):
        return {"object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

    def bullet(text):
        return {"object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

    def para(text):
        return {"object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}}

    # サマリ
    blocks.append(h2("📊 実行サマリ"))
    blocks.append(bullet(f"ステータス  : {r['overall']}"))
    blocks.append(bullet(f"生成曲数    : {r['ok']} / {r['total']} 曲"))
    blocks.append(bullet(f"平均尺      : {r['avg_dur_min']} ({r['avg_dur_sec']}秒)"))
    blocks.append(bullet(f"YouTube投稿 : {r['yt_count']} 曲"))

    # スタイル別
    if r["styles_done"]:
        blocks.append(h2("🎵 スタイル別"))
        for style, cnt in r["styles_done"].items():
            blocks.append(bullet(f"{style}: {cnt} 曲"))

    # 問題点
    if r["issues"]:
        blocks.append(h2("⚠️ 問題・推奨アクション"))
        for issue in r["issues"]:
            blocks.append(bullet(issue))
    else:
        blocks.append(h2("✅ 問題なし"))

    # 曲リスト
    blocks.append(h2("🎶 生成曲一覧"))
    for s in r["songs"]:
        dur = s.get("duration", 0)
        yt  = s.get("youtube_url", "未投稿")
        line = (
            f"[{s.get('title','?')}]  尺: {int(dur//60)}:{int(dur%60):02d}  "
            f"タグ: {s.get('tags','?')}  YouTube: {yt}"
        )
        blocks.append(bullet(line))

    # --- プロパティ（データベースのカラム）---
    # データベースには以下のプロパティが必要:
    #   Name (title), 日付 (date), ステータス (select),
    #   生成曲数 (number), 平均尺 (rich_text), 問題数 (number)
    properties = {
        "Name": {
            "title": [{"type": "text", "text": {
                "content": f"{r['date']} Suno 日報"
            }}]
        },
        "日付": {
            "date": {"start": r["date"]}
        },
        "ステータス": {
            "select": {"name": r["overall"]}
        },
        "生成曲数": {
            "number": r["ok"]
        },
        "平均尺": {
            "rich_text": [{"type": "text", "text": {"content": r["avg_dur_min"]}}]
        },
        "問題数": {
            "number": len(r["issues"])
        },
    }

    return {
        "parent": {"database_id": db_id},
        "properties": properties,
        "children": blocks,
    }


def post_to_notion(token: str, db_id: str, payload: dict) -> dict:
    resp = requests.post(
        f"{NOTION_API_BASE}/pages",
        headers=notion_headers(token),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ── メイン ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Suno 日報を Notion に投稿する")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="対象日 (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Notion への投稿はせずレポートだけ表示する")
    args = parser.parse_args()

    token = os.environ.get("NOTION_TOKEN", "")
    db_id = os.environ.get("NOTION_DATABASE_ID", "")

    if not args.dry_run and (not token or not db_id):
        print("❌ NOTION_TOKEN / NOTION_DATABASE_ID が未設定です。")
        print("   --dry-run オプションでテスト表示だけ行えます。")
        sys.exit(1)

    print(f"📋 PM エージェント起動: {args.date}")

    # --- results.json 読み込み ---
    data = load_results(args.date)
    if data is None:
        print(f"⚠️  output/{args.date}/results.json が見つかりません。")
        # Notion に「実行なし」を記録
        data = {"date": args.date, "songs": [], "errors": ["results.json が見つかりません"]}

    # --- 分析 ---
    report = analyze(data, args.date)

    print(f"\n{'='*50}")
    print(f"  日付      : {report['date']}")
    print(f"  ステータス: {report['overall']}")
    print(f"  生成曲数  : {report['ok']} / {report['total']}")
    print(f"  平均尺    : {report['avg_dur_min']}")
    print(f"  YouTube   : {report['yt_count']} 曲")
    if report["issues"]:
        print(f"\n  ⚠️  問題点:")
        for issue in report["issues"]:
            print(f"    - {issue}")
    print(f"{'='*50}\n")

    if args.dry_run:
        print("（--dry-run: Notion には投稿しません）")
        return

    # --- Notion 投稿 ---
    payload = build_notion_page(db_id, report)
    try:
        result = post_to_notion(token, db_id, payload)
        page_url = result.get("url", "")
        print(f"✅ Notion に日報を投稿しました: {page_url}")
    except requests.HTTPError as e:
        body = e.response.text if e.response else ""
        print(f"❌ Notion 投稿エラー: {e}")
        print(f"   レスポンス: {body[:400]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
