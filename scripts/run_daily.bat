@echo off
REM run_daily.bat — Agent②（Suno 作曲）専用ローカル実行スクリプト（Windows 用）
REM
REM Agent③④（動画化・YouTube投稿）は results.json の push をトリガーに
REM GitHub Actions (post_process.yml) が自動実行します。
REM
REM タスクスケジューラ登録（PowerShell / 管理者権限）:
REM   $action  = New-ScheduledTaskAction -Execute "cmd.exe" -Argument '/c "C:\path\to\repo\scripts\run_daily.bat"'
REM   $trigger = New-ScheduledTaskTrigger -Daily -At "09:30"
REM   Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "SunoDaily" -RunLevel Highest
REM
REM 初回: python scripts\suno_login.py でログインが必要です。

setlocal enabledelayedexpansion

set REPO_DIR=%~dp0..
set PYTHON=python

REM 日付取得（PowerShell を使って確実に YYYY-MM-DD 形式で）
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%i

set LOG_DIR=%REPO_DIR%\logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set LOG_FILE=%LOG_DIR%\%TODAY%.log

echo ============================== >> "%LOG_FILE%"
echo Suno 作曲 開始: %TODAY% %TIME% >> "%LOG_FILE%"
echo ============================== >> "%LOG_FILE%"

cd /d "%REPO_DIR%"

echo 📥 git pull... >> "%LOG_FILE%"
git pull --ff-only >> "%LOG_FILE%" 2>&1

if not exist "lyrics\%TODAY%\song.txt" (
    echo ❌ 歌詞ファイルが見つかりません: lyrics\%TODAY%\song.txt >> "%LOG_FILE%"
    echo    GitHub Actions がまだ実行されていない可能性があります。 >> "%LOG_FILE%"
    exit /b 1
)
echo ✅ 歌詞ファイル確認 >> "%LOG_FILE%"

echo. >> "%LOG_FILE%"
echo 🎼 Agent②: Suno AI で作曲中... >> "%LOG_FILE%"
%PYTHON% scripts\generate_music.py --date %TODAY% >> "%LOG_FILE%" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 作曲に失敗しました。ログを確認してください。 >> "%LOG_FILE%"
    exit /b 1
)

echo. >> "%LOG_FILE%"
echo 📤 results.json を push... >> "%LOG_FILE%"
git add "output\%TODAY%\results.json" >> "%LOG_FILE%" 2>&1
git diff --cached --quiet >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    git commit -m "chore: Agent② 完了 — Suno 作曲 %TODAY%" >> "%LOG_FILE%" 2>&1
    git push >> "%LOG_FILE%" 2>&1
    echo ✅ push 完了。GitHub Actions で動画化・YouTube投稿が自動実行されます。 >> "%LOG_FILE%"
) else (
    echo ⚠️  変更なし — 既に push 済みかもしれません。 >> "%LOG_FILE%"
)

echo. >> "%LOG_FILE%"
echo ✅ ローカル処理完了: %TODAY% %TIME% >> "%LOG_FILE%"
