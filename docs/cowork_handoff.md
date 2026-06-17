# 引き継ぎプロンプト：Suno AI 自動作曲・YouTube投稿システム

## あなたへの依頼

このプロジェクトの設計・実装を引き継いでください。
以下を読んだうえで、**「デスクトップの直接操作」を選択肢に加えて現状の設計を見直し、
ユーザーの手を限りなくゼロに、追加コストも限りなくゼロに近づける最善案を検討・実装してください。**

---

## ユーザーの目標

毎日、以下を**完全自動**で行いたい：

```
① 歌詞を生成・管理
② Suno AI で5スタイルの曲を生成（4〜5分）
③ カバー画像付き動画を作成
④ YouTubeへ自動投稿（タイトル・説明・タグ付き）
```

**優先条件（重要度順）:**
1. ユーザーの手作業がゼロ（または限りなくゼロ）
2. 追加コストがゼロ（または限りなくゼロ）
3. 安定して毎日動く

---

## ユーザーの現在の契約・環境

| サービス | 状況 |
|---------|------|
| Suno AI | **Pro契約済み**（2,500クレジット/月 = 1日5曲で十分） |
| Claude | **Pro契約済み**（Routines: 5回/日まで無料で使える） |
| GitHub | 無料プラン（Actions: パブリックリポジトリは無制限） |
| YouTube | Googleアカウントあり（API設定未完了） |
| デスクトップPC/Mac | **常時起動可能な環境あり**（←今回新たに追加する選択肢） |

---

## 既存実装の状態

**リポジトリ:** `yuki444/test`  
**ブランチ:** `claude/suno-ai-lyrics-integration-ghRr4`

### 実装済みファイル

```
scripts/
  generate_music.py    ← Agent②: Suno APIで5スタイル作曲
  suno_client.py       ← Suno APIクライアント（gcui-art/suno-api向け）
  make_videos.py       ← Agent③: Pollinations画像生成 + ffmpegで動画化
  upload_youtube.py    ← Agent④: YouTube Data APIで投稿（説明・タグ自動生成）
  youtube_client.py    ← YouTube APIクライアント（OAuthリフレッシュトークン方式）
  get_youtube_token.py ← 初回YouTube OAuthトークン取得ヘルパー
  list_results.py      ← 結果一覧表示

config/
  styles.json          ← 5スタイル定義（image_promptも含む）

lyrics/
  template/song.txt    ← 歌詞テンプレート
  2026-05-25/song.txt  ← 明日分の空テンプレート（歌詞未記入）

output/YYYY-MM-DD/
  results.json         ← 生成結果（URL・YouTube IDなどを蓄積）

docs/
  youtube_setup.md     ← YouTube OAuth初回設定手順

.github/workflows/
  daily_generate.yml   ← GitHub Actionsワークフロー（毎日11:00 JST）
```

### 5つのスタイル（確定済み）

| スタイル名 | ジャンル |
|-----------|---------|
| `electronic_ambient` | Electronic / Ambient |
| `dance_edm` | Dance / EDM（激しく踊れるダンスミュージック） |
| `rock_alternative` | Rock / Alternative |
| `acoustic_fingerpicking` | Acoustic Guitar / Singer-Songwriter（弾き語り） |
| `ballad` | Ballad |

---

## 現在の課題（唯一の未解決ボトルネック）

**Suno AIへのプログラムからの接続方法**が未決定です。

Suno AIには公式パブリックAPIが存在しないため、以下の方法を検討しました：

### 検討済みの案と評価

| 案 | 方法 | 追加コスト | 課題 |
|----|------|-----------|------|
| A | sunoapi.org（サードパーティAPI） | 有料（金額不明） | Suno Pro と二重払いになる → **除外** |
| B | gcui-art/suno-api を VPS で自己ホスト | **¥440/月〜** | Cookieが数週間で失効、再取得が必要 |
| C | 手動（ブラウザでsuno.comを操作） | **¥0** | 毎日30分の手作業が発生 |

**いずれの案も完全なゴール（手作業ゼロ＆コストゼロ）を満たせていない。**

---

## 今回Coworkに検討してほしい新しい観点

### デスクトップの直接操作を選択肢に加える

ユーザーは**常時起動しているPC/Macがある**ため、以下の方法が新たに選択肢になります：

#### 候補D: ブラウザ自動操作（Playwright等）
- Playwright / Puppeteeer でsuno.comにログインして操作
- ローカルで定時実行（cron / タスクスケジューラ）
- **追加コスト¥0**（Suno Proの既存クレジットを使う）
- 懸念: Sunoがbot検出をする可能性（ただし個人利用・自己アカウント）

#### 候補E: Claude Computer Use でデスクトップ操作
- ClaudeのComputer Use機能でブラウザを直接操作
- Suno.comをビジュアルで操作できるため検出リスクが低い
- コスト: Computer Use APIは従量課金（要確認）

#### 候補F: Routines + デスクトップ連携
- Claude Routines（Proに含む）でデスクトップに命令を送る
- ローカルで常駐するエージェントと組み合わせる

### 見直してほしいポイント

1. **D〜F案の実現可能性・安定性・コストを評価**し、既存のB/C案と比較
2. デスクトップ操作でSunoのbot検出を回避できるか検討
3. **「Routines（無料）+ デスクトップ自動化（無料）」の組み合わせ**で完全ゼロコスト・ゼロ手作業が実現できないか検討
4. 実現可能な最善案を選び、`scripts/suno_client.py` を置き換える形で実装

---

## エージェント全体構成（目標形）

```
毎日 9:00 JST
     ↓
[Agent①: 作詞] Claude Routine → 歌詞生成 → GitHubにコミット
     ↓（コミットをトリガー or スケジュール）
[Agent②: 作曲] ★未解決★ → 5スタイルの音楽生成 → results.jsonに保存
     ↓
[Agent③: 動画化] make_videos.py → Pollinations画像 + ffmpeg → MP4生成
     ↓
[Agent④: YouTube投稿] upload_youtube.py → YouTube Data API → 投稿完了
     ↓
[Agent⑤: 司令塔] 全工程の結果確認・エラー検知・通知
```

Agent①③④⑤はすべて**追加コストゼロ**で実装済みまたは実装可能。  
**Agent②だけが未解決。** ここに注力してください。

---

## コスト前提の整理

| 工程 | サービス | コスト |
|------|---------|--------|
| ①作詞 | Claude Routine（Proに含む） | ¥0 |
| ②作曲 | **← ここが課題** | 要検討 |
| ③画像生成 | Pollinations AI | ¥0 |
| ③動画化 | ffmpeg（GitHub Actions） | ¥0 |
| ④YouTube投稿 | YouTube Data API | ¥0（1日100本まで） |
| ⑤司令塔 | Claude Routine（Proに含む） | ¥0 |

**ゴール: ②を¥0で解決すれば、全工程の追加コスト¥0が実現する。**

---

## 実装方針（変えないでほしい点）

- 歌詞は `lyrics/YYYY-MM-DD/song.txt` 形式（日付フォルダ）
- 全結果は `output/YYYY-MM-DD/results.json` に追記
- YouTube投稿はデフォルト「限定公開（unlisted）」
- 動画はMP4、カバー画像はスタイルごとに自動生成
- 実装言語はPython
- インフラはGitHub Actions優先（ローカル実行は補助手段）
