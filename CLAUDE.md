# このプロジェクトについて

株式ポートフォリオ管理アプリ（スタンドアロンHTML + GitHub Gist同期）

## ユーザーの方針

### コスト
- **無料サービスを最優先で選ぶ**。有料・コストが発生する案は却下。
- 複数の選択肢がある場合は無料かつ最も安定したものを選ぶ（例: JSONBin.ioよりGitHub Gist）。

### 自動化
- **出来るだけ自動で完成させる**。確認なしで進められる作業は自動実行する。
- コードの変更後は自動でコミット・プッシュまで行う。
- 複数の独立したタスクは並列実行する。

### 技術選定の優先順位
1. 永久無料（GitHub Pages, GitHub Gist, Yahoo Finance APIなど）
2. 無料枠あり（小規模利用で超えない見込みがある場合のみ）
3. 有料 → **選ばない**

## アーキテクチャ

- **フロントエンド**: `static/index.html`（1ファイル完結）
  - Alpine.js（CDN）: リアクティブUI
  - Tailwind CSS（CDN）: スタイリング
  - Chart.js（CDN）: 株価チャート
- **データ保存**: ブラウザの `localStorage`
- **クラウド同期**: GitHub Gist API（永久無料）
- **株価データ**: Yahoo Finance API（直接fetch、無料）
- **ホスティング**: GitHub Pages（無料）

## ブランチ

- 開発ブランチ: `claude/kind-hypatia-HfcEQ`

## データ構造（localStorage）

| キー | 内容 |
|------|------|
| `pf_holdings` | 保有銘柄リスト |
| `pf_trades` | 売買履歴 |
| `pf_watchlist` | ウォッチリスト |
| `pf_events` | イベント（決算・配当・優待） |
| `cfg_gist` | GitHub Gist ID（同期設定） |
| `cfg_token` | GitHub Token（同期設定） |
