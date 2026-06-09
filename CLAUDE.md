# Project Memory

このファイルはプロジェクト横断のルール集です。作業内容に応じて該当セクションを参照してください。

---

# Part 1: Suno AI Lyrics Integration

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

---

# Part 2: iOS App Development

iOSアプリを開発する際は、このセクションのルールをすべて適用してください。

## 1. 開発環境・ツール連携

### Xcode MCP 接続
- **Xcode 26.3以降**のMCPサーバーに接続し、ビルド・テスト・`DocumentationSearch`を活用する
- 最新SwiftUI API・WWDC情報は必ずMCP経由で取得し、古いAPIを誤用しない

### 必須スクリプト（.xcodeproj直接編集禁止）
```bash
# 新規ファイル追加時（プロジェクト破壊防止）
./.claude/scripts/on_new_file.sh <path>

# ビルド確認
./.claude/scripts/on_build.sh
```
`.xcodeproj` を直接編集してはならない。上記スクリプトを必ず経由すること。

### コンテキスト管理
| タイミング | アクション |
|-----------|-----------|
| タスク完了・切り替え時 | `/clear` で履歴リセット |
| トークン消費 70% 超過 | `/compact` で要約 |

---

## 2. コーディング・デザインルール（HIG準拠）

### ナビゲーション
- iOS標準のスワイプバック（`NavigationStack`）を採用する
- Android風ボトムナビ・マテリアルデザインは禁止

### UIの品質基準
- タップ領域は **44 × 44 pt 以上** を常に確保
- システムフォント・Dynamic Type に対応する
- ダークモード対応（`Color` アセットにLight/Dark両バリアント設定）

### ネイティブ価値の実装
単なるWebViewラッパー禁止。必ず以下のいずれかを含むこと:
- プッシュ通知（UserNotifications）
- カメラ・フォトライブラリ（AVFoundation / PhotosUI）
- 位置情報（CoreLocation）
- その他ネイティブAPI活用機能

---

## 3. App Store 審査対策（リジェクト回避）

### 完成度
- クラッシュ・未実装画面・「Coming Soon」等のプレースホルダーは**厳禁**
- 全画面・全フローを動作確認してからサブミットする

### アカウント管理
- アカウント作成機能がある場合、**アプリ内でのアカウント削除機能**は必須
  - 削除フロー: 設定 → アカウント → アカウントを削除
  - 削除後は関連データをサーバー側からも消去する

### 審査員用デモ環境
- ログインが必要なアプリは、App Store Connectの「審査用メモ」に以下を記載できる状態にする:
  - デモアカウントのメールアドレス・パスワード
  - 特殊な操作が必要な場合はその手順

---

## 4. プライバシー・法的遵守

### プライバシーポリシー
- 全アプリにプライバシーポリシーURLを設置（設定画面またはオンボーディング）
- App Store Connect の「プライバシーの慣行」セクションも漏れなく記入

### トラッキング（ATT）
- ユーザーをトラッキングする場合は **AppTrackingTransparency (ATT)** フレームワークで許可を取得
- `Info.plist` に `NSUserTrackingUsageDescription` を追加し、明確な理由を記載

### 子ども向けアプリ（13歳未満対象）
- サードパーティ製広告・アナリティクスSDK禁止
- **ペアレンタルゲート**を有料コンテンツ・外部リンク前に実装

### 著作権・商標
- 生成AIによるコード・素材の著作権リスクを常に意識する
- Appleのロゴ・絵文字を埋め込まない
- アプリ名は「〇〇 for iPhone」形式の参照表示に留める（「iPhone」単体をアプリ名に含めない）

---

## 5. 日本市場向け決済ルール（スマホ新法 2025年12月施行）

### 外部決済（アプリ外課金）を導入する場合
1. **開示シート（モーダル）の表示**: Apple指定のモーダルをユーザーが外部リンクをタップする前に必ず表示する
2. **手数料の認識**:
   - 中小企業プログラム対象: 売上の **10%** をAppleへ支払う
   - それ以外: 売上の **15%** をAppleへ支払う
   - 月次売上レポートをAppleへ提出する義務がある
3. **IAP との並列提示**: Appleアプリ内課金（IAP）を、外部決済と同程度に目立つ形で選択肢として提示すること（外部決済だけを目立たせてはならない）

### IAPのみの場合
- 上記開示シート・手数料報告は不要
- 通常のStoreKitフローを実装する

---

## 6. ファイル構成（参考）

```
MyApp/
  MyApp.xcodeproj/        ← 直接編集禁止
  MyApp/
    App/
      MyAppApp.swift
    Features/             ← 機能別モジュール
    Shared/               ← 共通コンポーネント・拡張
    Resources/            ← Assets.xcassets, Info.plist
  MyAppTests/
  MyAppUITests/

.claude/
  scripts/
    on_new_file.sh        ← ファイル追加時に実行
    on_build.sh           ← ビルド確認時に実行

docs/
  privacy_policy.md
  review_notes.md         ← 審査用メモのテンプレート
```

---

## 7. よくあるリジェクト理由チェックリスト

- [ ] アカウント削除機能が実装されているか
- [ ] ATT許可ダイアログの`NSUserTrackingUsageDescription`が明確か
- [ ] プライバシーポリシーURLが有効か
- [ ] 全デバイス（iPhone/iPad）・OSバージョン（最新2世代）で動作確認済みか
- [ ] 外部リンクへの誘導前に開示シートを表示しているか（日本向け外部決済の場合）
- [ ] 「Coming Soon」「未実装」のプレースホルダーがないか
- [ ] クラッシュしないか（TestFlightでの実機テスト完了）
- [ ] タップ領域が44×44pt以上か
