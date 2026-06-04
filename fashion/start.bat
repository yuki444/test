@echo off
chcp 65001 > nul
title ワードローブコーディネーター

cd /d "%~dp0"

echo.
echo  ============================================
echo   ワードローブコーディネーター
echo  ============================================
echo.

:: Python確認
python --version > nul 2>&1
if errorlevel 1 (
    echo [エラー] Python がインストールされていません。
    echo https://www.python.org/downloads/ からインストール後、再実行してください。
    pause
    exit /b 1
)

:: 初回セットアップ: .env がなければ対話式でAPIキーを設定
if not exist .env (
    echo  初回セットアップ
    echo  ----------------------------------------
    echo  Anthropic APIキーが必要です。
    echo.
    echo  取得場所: https://console.anthropic.com
    echo    1. アカウント作成（Googleログイン可）
    echo    2. 左メニュー「API Keys」→「Create Key」
    echo    3. Billing でクレジットカード登録・$5チャージ
    echo.
    set /p APIKEY= APIキーを貼り付けて Enter:
    echo ANTHROPIC_API_KEY=%APIKEY%> .env
    echo.
    echo  APIキーを保存しました。
    echo.
)

:: ライブラリのインストール（不足分のみ）
echo ライブラリを確認中...
pip install -r requirements.txt -q
echo.

:: 2秒後にブラウザを自動オープン
start "" cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:5001"

echo アプリを起動しました。ブラウザが自動で開きます。
echo 終了するには このウィンドウを閉じるか Ctrl+C を押してください。
echo.

python app.py
pause
