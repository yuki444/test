# Playwright を使った Suno AI 自動化セットアップガイド

## なぜ Playwright？

| 案 | 追加コスト | 手作業 | 安定性 |
|----|-----------|--------|--------|
| A: sunoapi.org | **有料** | ゼロ | △ |
| B: gcui-art VPS | **¥440/月〜** | Cookie 再取得が必要 | △ |
| C: 手動操作 | ¥0 | 毎日30分 | ✅ |
| **D: Playwright（今回採用）** | **¥0** | **ゼロ（初回のみログイン）** | **✅** |

Playwright は **本物の Chrome ブラウザ**を動かします。Suno の視点からは通常のユーザー操作と区別がつきにくく、bot 検出のリスクが最小限です。また、Suno Pro の既存クレジットをそのまま使うので追加費用は一切かかりません。

---

## 前提条件

- Python 3.11 以上
- 常時起動している PC / Mac
- Suno AI Pro アカウント

---

## セットアップ手順

### 1. 依存関係のインストール

```bash
pip install playwright aiohttp
playwright install chromium
```

### 2. 初回ログイン（一度だけ）

```bash
python scripts/suno_login.py
```

ブラウザが開きます。Suno AI にログインしてください。ログイン完了後 Enter を押すとブラウザが閉じ、セッションが `~/.suno_playwright_profile` に保存されます。

> **セキュリティ注意**: このフォルダにはログイン情報が含まれます。他人と共有しないでください。

### 3. 動作テスト

```bash
# 今日の歌詞を作成（テスト用）
mkdir -p lyrics/$(date +%Y-%m-%d)
cp lyrics/template/song.txt lyrics/$(date +%Y-%m-%d)/

# 1スタイルだけテスト生成
python scripts/generate_music.py --styles electronic_ambient
```

### 4. 定時実行の設定

#### Mac / Linux（cron）

```bash
crontab -e
```

以下を追加（毎日 9:00 JST に実行）:

```cron
0 0 * * * /path/to/repo/scripts/run_daily.sh >> /path/to/repo/logs/cron.log 2>&1
```

> パスは実際のリポジトリの場所に合わせてください。

#### Windows（タスクスケジューラ）

PowerShell（管理者権限）で実行:

```powershell
$action  = New-ScheduledTaskAction -Execute "cmd.exe" `
             -Argument '/c "C:\path\to\repo\scripts\run_daily.bat"'
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
$settings = New-ScheduledTaskSettingsSet -WakeToRun $false -RunOnlyIfNetworkAvailable $true
Register-ScheduledTask -Action $action -Trigger $trigger `
  -TaskName "SunoDaily" -RunLevel Highest -Settings $settings
```

---

## トラブルシューティング

### `Not logged in to Suno AI` エラー

セッションが切れています。以下を実行してください:

```bash
python scripts/suno_login.py
```

Suno の Pro 契約を更新した直後などもセッションが切れることがあります。

### `Could not get Suno auth token` エラー

Suno のフロントエンドが Clerk の初期化に失敗している可能性があります。

```bash
# ヘッドフル（ブラウザを表示）でデバッグ
SUNO_HEADLESS=false python scripts/generate_music.py
```

### API エンドポイントが変わった場合

Suno は非公式 API のため URL が変更されることがあります。`scripts/suno_client.py` の先頭にある定数を更新してください:

```python
INTERNAL_API_BASE = "https://studio-api.suno.ai"  # ← 変更点があればここ
GENERATE_ENDPOINT = f"{INTERNAL_API_BASE}/api/generate/v2/"
FEED_ENDPOINT     = f"{INTERNAL_API_BASE}/api/feed/v2/"
```

ブラウザの DevTools（F12 → Network タブ）で `studio-api.suno.ai` へのリクエストを確認すれば現在のエンドポイントがわかります。

### headless / headful の切り替え

環境変数 `SUNO_HEADLESS=false` を設定すると、ブラウザが画面に表示されます（デバッグ時に便利）。

```bash
SUNO_HEADLESS=false python scripts/generate_music.py --date 2026-06-17
```

---

## 全体アーキテクチャ（完成形）

```
毎日 9:00
    ↓
[Agent①: 作詞] Claude Routine → 歌詞生成 → Git コミット
    ↓（GitHub Actions が検知、または cron でトリガー）
[Agent②: 作曲] ★Playwright + Suno 内部 API★
    ↓
[Agent③: 動画化] Pollinations 画像 + ffmpeg
    ↓
[Agent④: YouTube 投稿] YouTube Data API
```

Agent ① ③ ④ は GitHub Actions で完結。  
Agent ② は常時起動の PC でローカル実行します。

---

## コスト一覧

| 工程 | サービス | コスト |
|------|---------|--------|
| ①作詞 | Claude Routine（Pro に含む） | **¥0** |
| ②作曲 | Playwright + Suno Pro（既存） | **¥0** |
| ③画像生成 | Pollinations AI | **¥0** |
| ③動画化 | ffmpeg（ローカル） | **¥0** |
| ④YouTube 投稿 | YouTube Data API | **¥0** |
| **合計** |  | **¥0** |
