#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  株式ポートフォリオ管理アプリ"
echo "  Japanese Stock Portfolio Manager"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "[ERROR] Python3 が見つかりません。インストールしてください。"
  exit 1
fi

echo "[1/3] 依存パッケージをインストール中..."
pip install -r requirements.txt -q
echo "      完了 ✓"

echo ""
echo "[2/3] データベースを初期化中..."
python3 -c "import database; database.init_db(); print('      完了 ✓')"

echo ""
echo "[3/3] サーバーを起動します..."
echo ""
echo "  URL: http://localhost:8000"
echo ""
echo "  終了するには Ctrl+C を押してください"
echo "============================================"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
