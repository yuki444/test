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

---

## Claude への作業指針（やり取りを減らすための設定）

### 基本方針
- **確認なしで進める**: ファイル編集・新規作成・スクリプト修正はユーザーの承認なしに実施する。明らかに破壊的な操作（ブランチ削除、force push等）のみ事前確認する。
- **日本語で回答**: 応答はすべて日本語で行う。コードのコメントは不要（書く場合も最小限の英語）。
- **実装してから報告**: 「〜しましょうか？」と聞かず、まず実装して結果を報告する。
- **変更後は即コミット&プッシュ**: 作業完了後はコミットしてブランチへプッシュまで行う（PR作成はユーザーが明示的に依頼した場合のみ）。

### コーディングスタイル
- コメントは書かない（コード自体が自明な場合）。WHYが非自明な場合のみ1行。
- 型ヒントは積極的に使う（Python 3.12+）。
- エラー処理は境界（外部API呼び出し）のみに限定する。
- 新機能追加時は既存スクリプトのパターン（argparse + results.json更新）に合わせる。

### このプロジェクト固有のルール
- スタイル変更は `config/styles.json` を直接編集する（スクリプト改修不要）。
- 新スタイル追加時は `name`, `label`, `tags`, `image_prompt` の4フィールド必須。
- メディアファイル（.mp4/.mp3/.png）は `.gitignore` で除外済み。`results.json` のみをコミット対象とする。
- GitHub Actions のワークフロー（`daily_generate.yml`）を変更するときは、`env.SKIP` の分岐パターンを維持する。
- デフォルトのYouTubeプライバシーは `unlisted`（限定公開）。`public` に変える場合はユーザーの明示的な指示が必要。
- スクリプトは冪等性を保つ（再実行で既処理をスキップ）。`youtube_url` が既にあれば再アップロードしない。

### 過去の変更履歴から学んだ傾向
- スタイルは実際に試しながら入れ替える（jpop_citypop → dance_edm、jazz_bossanova → acoustic_fingerpicking など）。スタイル名変更の依頼が来たら `config/styles.json` だけ更新すれば済む。
- コストゼロ優先: 外部サービスは無料枠（Pollinations AI、YouTube Data API無料枠）を使う。有料サービスを追加提案しない。
- 自動化優先: 手動操作が必要なものは GitHub Actions へ組み込む方向で検討する。

---

## セットアップ

### 1. gcui-art/suno-api を自己ホスト

```bash
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
python scripts/generate_music.py --styles electronic_ambient dance_edm
```

### 3. 結果を確認

```bash
python scripts/list_results.py          # 全日付
python scripts/list_results.py --date 2026-05-24  # 特定日
```

結果は `output/YYYY-MM-DD/results.json` に保存される。

## 現在の5スタイル

| スタイル名 | ジャンル |
|-----------|---------|
| `electronic_ambient` | Electronic / Ambient |
| `dance_edm` | Dance / EDM |
| `rock_alternative` | Rock / Alternative |
| `acoustic_fingerpicking` | Acoustic Guitar / Singer-Songwriter |
| `ballad` | Ballad |

スタイルの追加・変更は `config/styles.json` を直接編集するだけ。スクリプト変更不要。

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
    media/          ← .mp4/.mp3/.png（gitignore済み、再生成可能）

config/
  styles.json       ← 5スタイルの設定（ここだけ変えればスタイル変更完了）

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
デフォルトは `unlisted`（限定公開）。`public` へ変更するにはユーザーの明示的な指示が必要。

## コスト

| 工程 | サービス | コスト |
|------|---------|--------|
| 作詞 | Claude Routine | 無料（Proに含む） |
| 作曲 | Suno API + 自己ホスト | サーバー代のみ |
| 画像生成 | Pollinations AI | 無料 |
| 動画化 | ffmpeg | 無料 |
| YouTube投稿 | YouTube Data API | 無料（1日100本まで） |
