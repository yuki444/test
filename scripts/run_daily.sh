#!/bin/bash
# run_daily.sh — Agent②（Suno 作曲）専用ローカル実行スクリプト（Mac / Linux 用）
#
# Agent③④（動画化・YouTube投稿）は results.json の push をトリガーに
# GitHub Actions (post_process.yml) が自動実行します。
#
# cron 設定例（毎日 9:30 JST = 0:30 UTC）:
#   crontab -e
#   30 0 * * * /path/to/repo/scripts/run_daily.sh >> /path/to/repo/logs/daily.log 2>&1
#
# 初回: python scripts/suno_login.py でログインが必要です。

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TODAY="$(date +%Y-%m-%d)"
LOG_DIR="$REPO_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/${TODAY}.log"
PYTHON="${PYTHON:-python3}"

log() { echo "$1" | tee -a "$LOG_FILE"; }

log "=============================="
log "🎵 Suno 作曲 開始: $TODAY $(date +%T)"
log "=============================="

cd "$REPO_DIR"

# 最新コードを取得（歌詞ファイルが GitHub Actions によって push されているはず）
log "📥 git pull..."
git pull --ff-only origin "$(git rev-parse --abbrev-ref HEAD)" 2>&1 | tee -a "$LOG_FILE" || true

# 歌詞ファイル確認
LYRICS_FILE="$REPO_DIR/lyrics/$TODAY/song.txt"
if [ ! -f "$LYRICS_FILE" ]; then
    log "❌ 歌詞ファイルが見つかりません: $LYRICS_FILE"
    log "   GitHub Actions (daily_generate.yml) がまだ実行されていない可能性があります。"
    log "   少し待ってから再試行するか、手動で作成してください。"
    exit 1
fi
log "✅ 歌詞ファイル確認: $LYRICS_FILE"

# Agent②: Suno で5スタイル作曲
log ""
log "🎼 Agent②: Suno AI で作曲中（約5〜10分かかります）..."
"$PYTHON" "$REPO_DIR/scripts/generate_music.py" --date "$TODAY" 2>&1 | tee -a "$LOG_FILE"

# results.json を git push → GitHub Actions が Agent③④を自動起動
log ""
log "📤 results.json を push → Agent③④（動画化・YouTube投稿）が自動起動..."
git add "output/$TODAY/results.json"
if git diff --cached --quiet; then
    log "⚠️  変更なし — 既に push 済みかもしれません。"
else
    git commit -m "chore: Agent② 完了 — Suno 作曲 $TODAY"
    git push origin "$(git rev-parse --abbrev-ref HEAD)"
    log "✅ push 完了。GitHub Actions で動画化・YouTube投稿が自動実行されます。"
fi

log ""
log "✅ ローカル処理完了: $TODAY $(date +%T)"
log "   GitHub Actions の進捗: https://github.com/yuki444/test/actions"
