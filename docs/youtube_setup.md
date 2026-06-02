# YouTube アップロード設定（初回のみ・約10分）

YouTubeへの自動投稿には1回だけOAuth認証が必要です。一度設定すれば以後は完全自動です。

## 1. Google Cloud プロジェクト作成（無料）

1. https://console.cloud.google.com/ にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」で **YouTube Data API v3** を検索して有効化

## 2. OAuth 認証情報を作成

1. 「APIとサービス」→「OAuth同意画面」を開く
2. User Type は「外部」を選択して作成
3. アプリ名など必須項目を入力
4. **公開ステータスを「本番環境」にする**
   - ⚠️ 重要: 「テスト中」のままだとリフレッシュトークンが**7日で失効**します
   - 自分専用なので「未確認のアプリ」警告は無視してOK
5. 「認証情報」→「認証情報を作成」→「OAuthクライアントID」
6. アプリケーションの種類は「デスクトップアプリ」を選択
7. 作成された **クライアントID** と **クライアントシークレット** を控える

## 3. リフレッシュトークンを取得（ローカルで1回だけ実行）

```bash
pip install -r requirements.txt
python scripts/get_youtube_token.py
```

ブラウザが開くのでGoogleアカウントでログイン・許可します。
完了するとターミナルに **リフレッシュトークン** が表示されます。

## 4. GitHub Secrets に登録

リポジトリの Settings → Secrets → Actions に追加:

| Secret | 値 |
|--------|---|
| `YOUTUBE_CLIENT_ID` | 手順2のクライアントID |
| `YOUTUBE_CLIENT_SECRET` | 手順2のクライアントシークレット |
| `YOUTUBE_REFRESH_TOKEN` | 手順3で表示されたトークン |

これで設定完了です。以後は毎日自動でYouTubeに投稿されます。

## コストについて

- YouTube Data API: **無料**（1日あたり10,000クォータ＝動画約100本投稿可能）
- 今回は1日5本なので無料枠で十分です
