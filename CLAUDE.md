# Suno AI Lyrics Integration

毎日歌詞を整理し、Suno AIで5つのスタイルの曲を自動生成するシステム。

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

---

## Claudeへの作業指針

### Webアプリ・静的サイトをGitHub Pagesで公開する場合

ユーザーに「WEBページにして」「アプリとして公開して」と言われたら、**最初から以下をまとめてやること**。途中で手動設定を求めない。

#### 手順（全自動）

1. **`gh-pages` orphanブランチを作成**してアプリファイルをルートに配置しプッシュ
   ```bash
   git checkout --orphan gh-pages
   git rm -rf .
   # アプリファイルをルートにコピー
   git add . && git commit -m "Deploy to GitHub Pages"
   git push -u origin gh-pages
   ```

2. **Pages自動有効化ワークフローを同ブランチに追加**してプッシュ
   - `GITHUB_TOKEN` に `pages: write` 権限を付与
   - `POST /repos/{owner}/{repo}/pages` を叩いてPages設定を自動有効化
   - 既に有効な場合はスキップ（冪等）

   ```yaml
   # .github/workflows/enable-pages.yml (gh-pagesブランチに置く)
   name: Enable GitHub Pages
   on:
     push:
       branches: [gh-pages]
   permissions:
     pages: write
     id-token: write
     contents: read
   jobs:
     enable-pages:
       runs-on: ubuntu-latest
       steps:
         - name: Enable GitHub Pages via API
           env:
             GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
           run: |
             STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
               -H "Authorization: Bearer $GH_TOKEN" \
               -H "Accept: application/vnd.github+json" \
               https://api.github.com/repos/${{ github.repository }}/pages)
             if [ "$STATUS" = "200" ]; then
               echo "Pages already enabled."
             else
               curl -s -X POST \
                 -H "Authorization: Bearer $GH_TOKEN" \
                 -H "Accept: application/vnd.github+json" \
                 -H "Content-Type: application/json" \
                 https://api.github.com/repos/${{ github.repository }}/pages \
                 -d '{"source":{"branch":"gh-pages","path":"/"}}'
               echo "Done. URL: https://${{ github.repository_owner }}.github.io/${{ github.event.repository.name }}/"
             fi
   ```

3. **PWA対応**（スマホでホーム画面追加できるように）
   - `manifest.json` — アプリ名・テーマカラー・アイコン
   - `sw.js` — Service Worker（オフライン対応）
   - `index.html` に `<link rel="manifest">` と `<meta name="apple-mobile-web-app-capable">` を追加

4. **公開URLをユーザーに伝える**
   ```
   https://{owner}.github.io/{repo}/
   ```

#### なぜこの順序か
- `gh-pages` ブランチへの push イベントで `.github/workflows/enable-pages.yml` が自動実行される
- `GITHUB_TOKEN` は `pages: write` があればPages APIを叩けるため、UIでの手動設定不要
- この環境では `gh` CLIや直接API認証トークンが使えないが、Actions内の `GITHUB_TOKEN` は有効

---

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
  generate_music.py ← メイン生成スクリプト
  suno_client.py    ← Suno APIクライアント
  list_results.py   ← 結果一覧表示

.github/workflows/
  daily_generate.yml ← 毎日自動実行
```
