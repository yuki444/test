@echo off
setlocal

set TASK_NAME=Outlook広告メール既読化
set SCRIPT_PATH=%~dp0mark_ads_read.py
set RUN_DAY=MON
set RUN_TIME=09:00

REM Pythonのパスを取得
for /f "delims=" %%i in ('where python 2^>nul') do set PYTHON_PATH=%%i

if "%PYTHON_PATH%"=="" (
    echo [ERROR] Python が見つかりません。先に Python をインストールしてください。
    pause
    exit /b 1
)

echo ================================
echo Outlook 広告メール既読化 - 週次スケジュール登録
echo ================================
echo.
echo 設定内容:
echo   スクリプト : %SCRIPT_PATH%
echo   Python     : %PYTHON_PATH%
echo   実行タイミング: 毎週月曜日 09:00
echo.

REM 既存タスクを削除（再登録のため）
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM タスクを登録
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
  /sc weekly ^
  /d %RUN_DAY% ^
  /st %RUN_TIME% ^
  /rl highest ^
  /f

if errorlevel 1 (
    echo.
    echo [ERROR] タスクの登録に失敗しました。
    echo 管理者として実行してみてください（右クリック → 管理者として実行）
    pause
    exit /b 1
)

echo.
echo ================================
echo 登録完了！毎週月曜日 09:00 に自動実行されます。
echo.
echo 確認・変更は「タスクスケジューラ」で行えます:
echo   スタートメニュー → タスクスケジューラ → "%TASK_NAME%"
echo.
echo 今すぐ試し実行する場合:
echo   schtasks /run /tn "%TASK_NAME%"
echo ================================
pause
