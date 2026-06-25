# coding: utf-8
"""
PM エージェント — 品質チェック & Notion 日報

役割:
  - 歌詞ファイルの品質を検査（テンプレートテキスト検出）
  - 生成結果の品質スコアを算出
  - GitHub Actions の pre-flight チェック
  - Notion への日報投稿（NOTION_TOKEN 環境変数が必要な場合のみ）

使い方:
  python scripts/pm_agent.py --date 2026-06-25           # 品質チェックのみ
  python scripts/pm_agent.py --date 2026-06-25 --notify  # Notion 投稿あり
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LYRICS_DIR = REPO_ROOT / "lyrics"

# ── テンプレートテキスト検出 ──────────────────────────────────────────────

PLACEHOLDER_KEYWORDS = [
    "ここに曲のタイトルを入力",
    "1番の歌詞をここに書く",
    "メロディーラインに合わせて",
    "自然な区切りで改行する",
    "サビの歌詞 — 一番印象的なフレーズ",
    "繰り返しが多いと覚えやすい",
    "この曲の核心となる言葉",
    "2番の歌詞をここに書く",
    "インストロ部分 — 任意",
    "サビへの繋ぎ",
    "気持ちが高まっていく",
]

def check_lyrics_quality(date_str: str) -> dict:
    """歌詞ファイルの品質を検査する。"""
    path = LYRICS_DIR / date_str / "song.txt"

    if not path.exists():
        return {
            "status": "missing",
            "score": 0,
            "message": f"歌詞ファイルなし: {path}",
            "issues": ["lyrics file not found"],
        }

    content = path.read_text(encoding="utf-8")

    issues = []

    # プレースホルダー検出
    found_placeholders = [kw for kw in PLACEHOLDER_KEYWORDS if kw in content]
    if found_placeholders:
        issues.append(f"テンプレートテキスト検出: {found_placeholders[:2]}")

    # セクション数チェック
    sections = [l.strip() for l in content.split("\n")
                if l.strip().startswith("[") and l.strip().endswith("]")]
    if len(sections) < 5:
        issues.append(f"セクション数が少なすぎます: {len(sections)} (最低5つ必要)")

    # 歌詞行数チェック（タイトル・セクション名・区切り線を除く）
    lyric_lines = [l for l in content.split("\n")
                   if l.strip()
                   and not l.strip().startswith("[")
                   and not l.strip().startswith("title:")
                   and l.strip() != "---"]
    if len(lyric_lines) < 20:
        issues.append(f"歌詞が短すぎます: {len(lyric_lines)}行 (最低20行必要)")

    # タイトル取得
    title = ""
    for line in content.split("\n"):
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
            break
    if not title or title in PLACEHOLDER_KEYWORDS:
        issues.append("タイトルが未設定またはプレースホルダー")

    score = 100
    if found_placeholders:
        score -= 60
    if len(sections) < 5:
        score -= 20
    if len(lyric_lines) < 20:
        score -= 15
    if not title or title in PLACEHOLDER_KEYWORDS:
        score -= 20
    score = max(0, score)

    status = "ok" if score >= 80 else ("low_quality" if score >= 40 else "failed")

    return {
        "status": status,
        "score": score,
        "title": title,
        "sections": len(sections),
        "lyric_lines": len(lyric_lines),
        "issues": issues,
        "message": f"スコア:{score} / セクション:{len(sections)} / 行数:{len(lyric_lines)}",
    }


# ── results.json 品質チェック ────────────────────────────────────────────

def check_results_quality(date_str: str) -> dict:
    """生成結果の品質を検査する。"""
    path = REPO_ROOT / "output" / date_str / "results.json"

    if not path.exists():
        return {"status": "missing", "issues": ["results.json not found"]}

    data = json.loads(path.read_text(encoding="utf-8"))
    songs  = data.get("songs", [])
    errors = data.get("errors", [])
    issues = []

    seen_ids = set()
    unique_songs = []
    for s in songs:
        sid = s.get("id")
        if sid and sid not in seen_ids:
            seen_ids.add(sid)
            unique_songs.append(s)

    if not unique_songs:
        issues.append("生成された曲が0曲")

    short_songs = [s for s in unique_songs
                   if (s.get("duration_sec") or s.get("duration") or 0) < 180]
    if short_songs:
        issues.append(f"短い曲あり: {len(short_songs)}曲 (3分未満)")

    if errors:
        issues.append(f"エラー: {len(errors)}件")

    yt_count = sum(1 for s in unique_songs if s.get("youtube_url"))
    video_count = sum(1 for s in unique_songs if s.get("video_path"))

    avg_dur = 0
    if unique_songs:
        durations = [(s.get("duration_sec") or s.get("duration") or 0)
                     for s in unique_songs]
        avg_dur = sum(durations) / len(durations)

    if errors or not unique_songs:
        status = "failed"
    elif short_songs:
        status = "warning"
    else:
        status = "ok"

    return {
        "status": status,
        "total": len(unique_songs),
        "avg_duration_sec": avg_dur,
        "youtube_count": yt_count,
        "video_count": video_count,
        "errors": errors,
        "issues": issues,
        "songs": unique_songs,
    }


# ── Notion 投稿 ───────────────────────────────────────────────────────────

def post_to_notion(date_str: str, lyrics_qc: dict, results_qc: dict):
    """results.json の内容を Notion に投稿する。"""
    import urllib.request
    import urllib.error

    token = os.environ.get("NOTION_TOKEN", "")
    db_id = os.environ.get("NOTION_DATABASE_ID", "")

    if not token or not db_id:
        print("  NOTION_TOKEN / NOTION_DATABASE_ID が未設定のためスキップ")
        return None

    # 総合ステータス判定
    if results_qc["status"] == "failed" or lyrics_qc["status"] == "failed":
        overall = "❌ 失敗"
    elif results_qc["status"] == "warning" or lyrics_qc["status"] in ("low_quality",):
        overall = "⚠️ 要確認"
    elif results_qc["status"] == "missing":
        overall = "⚠️ 作曲未実行"
    else:
        overall = "✅ 正常"

    songs = results_qc.get("songs", [])
    avg_dur = results_qc.get("avg_duration_sec", 0)
    avg_str = f"{int(avg_dur // 60)}:{int(avg_dur % 60):02d}" if avg_dur > 0 else "—"

    song_list = "\n".join(
        f"- [{s.get('style_label','')}] {s.get('title','')} / "
        f"{int((s.get('duration_sec') or s.get('duration') or 0) // 60)}:"
        f"{int((s.get('duration_sec') or s.get('duration') or 0) % 60):02d}"
        + (f" → [{s['youtube_url']}]({s['youtube_url']})" if s.get("youtube_url") else "")
        for s in songs
    ) or "（なし）"

    issues_all = lyrics_qc.get("issues", []) + results_qc.get("issues", [])
    issues_str = "\n".join(f"- {i}" for i in issues_all) if issues_all else "問題なし"

    content_md = f"""## 📊 実行サマリ

| 項目 | 値 |
|------|-----|
| ステータス | {overall} |
| 生成曲数 | {results_qc.get('total', 0)} 曲 |
| 平均尺 | {avg_str} |
| YouTube 投稿 | {results_qc.get('youtube_count', 0)} 曲 |
| 動画生成 | {results_qc.get('video_count', 0)} 曲 |

## 🎵 生成曲一覧

{song_list}

## 🎤 歌詞品質チェック

- スコア: {lyrics_qc.get('score', 0)} / 100
- タイトル: {lyrics_qc.get('title', '—')}
- セクション数: {lyrics_qc.get('sections', 0)}
- 歌詞行数: {lyrics_qc.get('lyric_lines', 0)}

## ⚠️ 問題点

{issues_str}
"""

    payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "日報名": {"title": [{"text": {"content": f"{date_str} Suno 日報"}}]},
            "date": {"date": {"start": date_str}},
            "ステータス": {"select": {"name": overall}},
            "生成曲数": {"number": results_qc.get("total", 0)},
            "平均尺": {"rich_text": [{"text": {"content": avg_str}}]},
            "問題数": {"number": len(issues_all)},
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content_md}}]
                }
            }
        ]
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.notion.com/v1/pages",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            url = result.get("url", "")
            print(f"  ✅ Notion 投稿完了: {url}")
            return url
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")
        print(f"  ❌ Notion 投稿失敗 ({e.code}): {body_err[:200]}")
        return None


# ── メイン ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PM エージェント — 品質チェック & Notion 日報")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--notify", action="store_true", help="Notion に投稿する")
    parser.add_argument("--check-only", action="store_true", help="品質チェックのみ（CI 用）")
    args = parser.parse_args()

    print(f"\n=== PM Agent : {args.date} ===\n")

    # 歌詞品質チェック
    print("--- 歌詞品質チェック ---")
    lyrics_qc = check_lyrics_quality(args.date)
    print(f"  ステータス : {lyrics_qc['status']}")
    print(f"  {lyrics_qc['message']}")
    for issue in lyrics_qc.get("issues", []):
        print(f"  ⚠️  {issue}")

    # 生成結果品質チェック
    print("\n--- 生成結果チェック ---")
    results_qc = check_results_quality(args.date)
    print(f"  ステータス : {results_qc['status']}")
    for issue in results_qc.get("issues", []):
        print(f"  ⚠️  {issue}")
    if results_qc.get("total", 0) > 0:
        print(f"  曲数: {results_qc['total']} / 平均尺: "
              f"{int(results_qc['avg_duration_sec']//60)}:"
              f"{int(results_qc['avg_duration_sec']%60):02d}")

    # CI チェックモード: 歌詞が失敗なら exit 1
    if args.check_only:
        if lyrics_qc["status"] == "failed":
            print(f"\n❌ 歌詞品質チェック失敗 — GitHub Actions を中断します")
            sys.exit(1)
        print("\n✅ 品質チェック通過")
        return

    # Notion 投稿
    if args.notify:
        print("\n--- Notion 投稿 ---")
        post_to_notion(args.date, lyrics_qc, results_qc)

    print("\n=== PM Agent 完了 ===")


if __name__ == "__main__":
    main()
