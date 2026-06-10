# 開発ルール（Claude Code 必読）

## Git ブランチ運用

- **作業ブランチ**: `claude/financial-planner-tool-QVzK9`
- **すべての変更は作業ブランチへのコミット後、必ず `main` にもマージ・プッシュする**

```bash
# 変更完了後の標準フロー
git add <files>
git commit -m "コミットメッセージ"
git push -u origin claude/financial-planner-tool-QVzK9
git checkout main
git merge claude/financial-planner-tool-QVzK9 --no-edit
git push -u origin main
git checkout claude/financial-planner-tool-QVzK9
```

---

## エラーハンドリング原則

**新規コードを書く際の必須ルール:**

- **空の catch ブロック禁止**: `catch(e){}` は絶対に書かない
- **エラーは必ずユーザーに伝える**: UIコードでは `showToast('❌ ...')` で表示する
- **非UIコードでは `console.error` で記録**: ユーザーに見えない処理でも黙って捨てない
- **失敗時の黙った `return` 禁止**: fetch失敗・バリデーション失敗は原因をユーザーに通知してから終了する
- **フォールバックへの無音移行禁止**: エラーを握りつぶして別処理に進まない。ユーザーに確認を取るかエラーを明示する
- **ユーザーキャンセル（`AbortError`）は例外**: ユーザー自身が中断した操作はエラー表示不要

```javascript
// NG
fetch(url).then(r=>r.json()).catch(()=>{});

// OK
fetch(url)
  .then(r=>{
    if(!r.ok) { showToast('❌ 取得失敗（HTTP '+r.status+'）'); return; }
    return r.json();
  })
  .catch(e=>showToast('❌ ネットワークエラー: '+e.message));
```

---

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
