@echo off
echo Outlook MCP Server セットアップ
echo ================================

REM Pythonの確認
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python が見つかりません。https://www.python.org からインストールしてください
    pause
    exit /b 1
)

echo [OK] Python が見つかりました

REM 依存パッケージのインストール
echo.
echo 依存パッケージをインストールしています...
pip install mcp pywin32

if errorlevel 1 (
    echo [ERROR] インストールに失敗しました
    pause
    exit /b 1
)

echo.
echo ================================
echo セットアップ完了！
echo.
echo 次のステップ:
echo   Claude Code のローカル設定に以下を追加してください
echo.
echo   claude mcp add -s user outlook-desktop -- python "%~dp0server.py"
echo.
echo   または手動で ~/.claude.json に追記:
echo   "outlook-desktop": {
echo     "command": "python",
echo     "args": ["%~dp0server.py"]
echo   }
echo.
pause
