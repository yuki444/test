#!/bin/bash
# ワードローブコーディネーター 起動スクリプト (Mac / Linux)

cd "$(dirname "$0")"

echo ""
echo " ============================================"
echo "  ワードローブコーディネーター"
echo " ============================================"
echo ""

# Python確認
PYTHON=""
for cmd in python3 python; do
    if command -v $cmd &> /dev/null; then
        PYTHON=$cmd
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[エラー] Python がインストールされていません。"
    echo "https://www.python.org/downloads/ からインストール後、再実行してください。"
    exit 1
fi

# 初回セットアップ: .env がなければ対話式でAPIキーを設定
if [ ! -f .env ]; then
    echo " 初回セットアップ"
    echo " ----------------------------------------"
    echo " Anthropic APIキーが必要です。"
    echo ""
    echo " 取得場所: https://console.anthropic.com"
    echo "   1. アカウント作成（Googleログイン可）"
    echo "   2. 左メニュー「API Keys」→「Create Key」"
    echo "   3. Billing でクレジットカード登録・\$5チャージ"
    echo ""
    read -p " APIキーを貼り付けて Enter: " apikey
    echo "ANTHROPIC_API_KEY=$apikey" > .env
    echo ""
    echo " APIキーを保存しました。"
    echo ""
fi

# ライブラリのインストール（不足分のみ）
echo "ライブラリを確認中..."
$PYTHON -m pip install -r requirements.txt -q
echo ""

# 2秒後にブラウザを自動オープン（Mac と Linux 両対応）
(sleep 2 && (open "http://localhost:5001" 2>/dev/null || xdg-open "http://localhost:5001" 2>/dev/null)) &

echo "アプリを起動しました。ブラウザが自動で開きます。"
echo "終了するには Ctrl+C を押してください。"
echo ""

$PYTHON app.py
