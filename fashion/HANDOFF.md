# ファッションコーディネーターアプリ 引き継ぎドキュメント

## プロジェクト概要

ファッションに無頓着な家族持ち男性向けの「シーズンごとに持つべき服」を提案するWebアプリ。
**日々のコーデ提案ではなく、クローゼットに揃えておくべきアイテムをシーズン単位で計画するツール。**

---

## ユーザー情報（オーナー固有の設定・変更不可）

| 項目 | 値 |
|------|---|
| 年齢 | 38歳 |
| 身長 / 体重 | 178cm / 80kg |
| 体型 | スポーツ体型・太ももが太め（市販パンツがきつくなりやすい） |
| 予算 | こだわりたい（1シーズン予算は気にしない） |
| 家族構成 | 小さい子供あり（未就学〜小学生） |
| 普段の服 | ほぼUNIQLOのみ、ファッション無頓着 |

この情報は `fashion/app.py` の `DEFAULT_PROFILE` 辞書に直接埋め込まれており、
ブラウザの localStorage（キー: `wc_profile`）にも保存される。

---

## リポジトリ情報

| 項目 | 値 |
|------|---|
| リポジトリ | https://github.com/yuki444/test |
| 開発ブランチ | `claude/fashion-coordinator-app-tcNRF` |
| アプリディレクトリ | `fashion/` |

---

## 技術スタック

- **バックエンド**: Python 3.11 + Flask 3.x
- **AI**: Anthropic Claude API（claude-sonnet-4-6）/ ストリーミングレスポンス
- **フロントエンド**: バニラHTML/CSS/JS（フレームワークなし）
- **データ永続化**: ブラウザ localStorage（サーバー側ファイル不要）
- **PWA**: manifest.json + Service Worker（スマホのホーム画面に追加可能）

---

## ファイル構成

```
fashion/
  app.py                  バックエンド本体（Flask + Claude API）
  requirements.txt        python依存関係（flask, anthropic, gunicorn, python-dotenv）
  Procfile                gunicornでの起動設定（Render/Railway用）
  start.bat               Windowsワンクリック起動スクリプト
  start.sh                Mac/Linuxワンクリック起動スクリプト
  templates/
    index.html            シングルページアプリ（2タブ構成）
  static/
    app.js                フロントエンドロジック（localStorage, SSE streaming）
    style.css             モバイルファーストCSS
    manifest.json         PWAマニフェスト
    sw.js                 Service Worker（静的アセットキャッシュ）
    icon.svg              アプリアイコン
    icon-maskable.svg     マスカブルアイコン（Android用）

（リポジトリルート）
railway.json              Railway デプロイ設定
render.yaml               Render デプロイ設定（env: python, plan: free）
.gitignore                fashion/data/ と .env を除外
```

---

## アーキテクチャ上の重要な決定事項

### 1. データはlocalStorageに保存（サーバー不要）
- プロフィール: `localStorage['wc_profile']`
- 手持ちアイテム: `localStorage['wc_wardrobe']`
- `/api/recommend` はリクエストボディで `profile` と `wardrobe_items` を受け取る
- サーバー再起動してもデータが消えない（Render無料枠対応）
- サーバー側ファイル（`fashion/data/`）はgitignoreで除外、バックアップとしてのみ存在

### 2. 手持ち服の入力は任意
- 未入力でも「ゼロから揃える前提」で完結した提案が出る
- 設定タブに任意として記載し、入力不要でメイン機能が使える

### 3. 体型への特別対応（プロンプトエンジニアリング）
- `body_note` フィールドに「スポーツ体型・太ももが太め」を記録
- システムプロンプトで太もも対応を明示：ストレッチ素材必須、ワイド/ストレートシルエット推奨
- パンツ提案時は必ずサイズ感の注意点を添える

### 4. 購入先は7サイト（複数リンク）
UNIQLO / GU / 無印良品 / ZOZOTOWN / Amazon / 楽天ファッション / H&M
各アイテムに複数の購入先リンクを提示。特定ショップに絞らない方針。

### 5. 季節の自動選択
現在月から春夏秋冬を自動判定してアクティブ表示。「今」バッジも表示。

---

## APIエンドポイント

| メソッド | パス | 用途 |
|---------|------|------|
| GET | `/` | メインページ |
| GET | `/sw.js` | Service Worker（ルートから提供必須） |
| GET/POST | `/api/profile` | プロフィール（GET: デフォルト返却, POST: ファイル保存） |
| GET/POST | `/api/wardrobe` | 手持ち服（バックアップ用、主にlocalStorage使用） |
| POST | `/api/recommend` | AI提案生成（SSEストリーミング） |

### `/api/recommend` リクエスト形式
```json
{
  "season": "spring|summer|autumn|winter",
  "profile": { "age":"38", "height":"178", "weight":"80", "budget":"high", "family":"children_small", "body_note":"..." },
  "wardrobe_items": [{"name":"白T","category":"トップス","color":"白"}]
}
```

---

## ローカル起動方法

```bash
# 初回
git clone https://github.com/yuki444/test
cd test
git checkout claude/fashion-coordinator-app-tcNRF

# Windowsの場合
fashion\start.bat

# Mac/Linuxの場合
bash fashion/start.sh
```

初回起動時にAPIキーを対話形式で設定。`fashion/.env` に保存される。
2回目以降は起動スクリプトをダブルクリックするだけ。

---

## デプロイ（スマホアクセス用）

### Render（無料）
1. render.com でGitHubログイン
2. New → Web Service → リポジトリ選択
3. Branch: `claude/fashion-coordinator-app-tcNRF`
4. 環境変数 `ANTHROPIC_API_KEY` を設定
5. Deploy → URLが発行される
6. iPhoneはSafariで開き「ホーム画面に追加」でアイコン化

**注意**: 無料枠は15分非アクティブでスリープ。次回アクセス時30秒待ちあり。

### Railway（月$5/750円・快適）
`railway.json` が設定済み。`ANTHROPIC_API_KEY` を環境変数に設定するだけ。

---

## 現在の状態（引き継ぎ時点）

- [x] アプリ実装完了・動作確認済み
- [x] GitHubへのpush完了（ブランチ: `claude/fashion-coordinator-app-tcNRF`）
- [x] PC起動スクリプト完成（start.bat / start.sh）
- [x] Render/Railway デプロイ設定完了
- [ ] **Renderへのデプロイ未実施**（オーナーがrender.comで操作必要）
- [ ] デプロイ後のURLをスマホのホーム画面に追加

---

## 今後の拡張候補（未実装）

- 過去の提案履歴の保存・参照
- 「購入済み」チェック機能（揃えた服をトラッキング）
- 楽天/Amazon APIによる実在商品の価格表示
- 提案結果のPDF/画像エクスポート
- 家族（妻・子供）向け提案の追加
