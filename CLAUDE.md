# Suno AI Lyrics Integration

毎日歌詞を整理し、Suno AIで5つのスタイルの曲を自動生成し、
カバー画像付き動画にしてYouTubeへ自動投稿するシステム。

## パイプライン全体像

```
① 作詞       歌詞ファイル作成（手動 or Routine）
② 作曲       generate_music.py → Suno API（5スタイル、4-5分）
③ 動画化     make_videos.py → Pollinations画像 + ffmpeg（無料）
④ YouTube投稿 upload_youtube.py → YouTube Data API（無料）
```

各工程の結果はすべて `output/YYYY-MM-DD/results.json` に追記される。

## セットアップ

### 1. gcui-art/suno-api を自己ホスト

```bash
# Dockerでローカルに立ち上げる場合
git clone https://github.com/gcui-art/suno-api.git
cd suno-api
cp .env.example .env
# .env の SUNO_COOKIE に Suno アカウントのCookieを設定
docker-compose up -d
```

Suno CookieはブラウザのDevTools → Application → Cookies → suno.com で取得。

### 2. GitHub Secrets に設定

リポジトリの Settings → Secrets → Actions に追加:

| Secret | 値 |
|--------|---|
| `SUNO_API_URL` | 自己ホストAPIのURL (例: `https://your-server.com`) |

### 3. Python依存関係インストール

```bash
pip install -r requirements.txt
```

## 毎日の使い方

### 1. 歌詞ファイルを作成

```bash
mkdir -p lyrics/$(date +%Y-%m-%d)
cp lyrics/template/song.txt lyrics/$(date +%Y-%m-%d)/song.txt
# ファイルを編集して歌詞を書く
```

ファイル形式:
```
title: 曲のタイトル
---
[Verse 1]
歌詞...

[Chorus]
サビの歌詞...
```

### 2. 曲を生成

```bash
# 今日の歌詞で5スタイル全て生成
python scripts/generate_music.py

# 特定の日付
python scripts/generate_music.py --date 2026-05-24

# 特定スタイルだけ
python scripts/generate_music.py --styles electronic_ambient jpop_citypop
```

### 3. 結果を確認

```bash
python scripts/list_results.py          # 全日付
python scripts/list_results.py --date 2026-05-24  # 特定日
```

結果は `output/YYYY-MM-DD/results.json` に保存される。

## 5つのスタイル

| スタイル名 | ジャンル |
|-----------|---------|
| `electronic_ambient` | Electronic / Ambient |
| `jpop_citypop` | J-Pop / City Pop |
| `rock_alternative` | Rock / Alternative |
| `jazz_bossanova` | Jazz / Bossa Nova |
| `ballad` | Ballad |

スタイルの設定は `config/styles.json` で変更可能。

## 自動実行

GitHub Actions が毎日 11:00 JST に実行される。  
その日の `lyrics/YYYY-MM-DD/song.txt` が存在すれば自動で5スタイルの曲を生成し、`output/` にコミットする。

手動実行: Actions タブ → Daily Music Generation → Run workflow

## ファイル構成

```
lyrics/
  YYYY-MM-DD/
    song.txt        ← 歌詞をここに書く
  template/
    song.txt        ← テンプレート

output/
  YYYY-MM-DD/
    results.json    ← 生成された曲のURL・情報

config/
  styles.json       ← 5スタイルの設定

scripts/
  generate_music.py   ← ②作曲（Suno API）
  suno_client.py      ← Suno APIクライアント
  make_videos.py      ← ③画像生成(Pollinations)＋動画化(ffmpeg)
  upload_youtube.py   ← ④YouTube投稿
  youtube_client.py   ← YouTube APIクライアント
  get_youtube_token.py← 初回トークン取得ヘルパー
  list_results.py     ← 結果一覧表示

docs/
  youtube_setup.md    ← YouTube連携の初回設定手順

.github/workflows/
  daily_generate.yml  ← 毎日自動実行（②→③→④）
```

## YouTube連携

初回のみOAuth設定が必要（約10分）。詳細は `docs/youtube_setup.md` を参照。

必要な GitHub Secrets:

| Secret | 用途 |
|--------|------|
| `YOUTUBE_CLIENT_ID` | OAuth クライアントID |
| `YOUTUBE_CLIENT_SECRET` | OAuth クライアントシークレット |
| `YOUTUBE_REFRESH_TOKEN` | リフレッシュトークン |

投稿の公開範囲は `upload_youtube.py --privacy {public,unlisted,private}` で指定。
デフォルトは `unlisted`（限定公開）。

## コスト

| 工程 | サービス | コスト |
|------|---------|--------|
| 作詞 | Claude Routine | 無料（Proに含む） |
| 作曲 | Suno API + 自己ホスト | サーバー代のみ |
| 画像生成 | Pollinations AI | 無料 |
| 動画化 | ffmpeg | 無料 |
| YouTube投稿 | YouTube Data API | 無料（1日100本まで） |
