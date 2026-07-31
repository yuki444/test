# 日本株推奨・自律運用システム

対象30銘柄を毎日スコアリングし、TOP10を仮想ポートフォリオで自動売買、
ダッシュボードをGitHub Pagesに公開する自律運用シミュレーションシステム。

**実資金の売買は一切行いません。** すべて仮想ポートフォリオ（初期資金500万円）でのシミュレーションです。

## パイプライン全体像

```
① データ取得   fetch_data.py    → Yahoo Finance（日次株価・財務情報、認証不要）
② スコアリング score_stocks.py  → 4軸スコア（テクニカル/ファンダメンタル/モメンタム/ニュース）
③ 仮想売買     auto_trade.py    → TOP10均等配分・売却ルール評価
④ ダッシュボード generate_dashboard.py → docs/index.html（GitHub Pages）
⑤ 週次振り返り  weekly_reflect.py → 予測精度検証・スコア重み自動調整
```

## セットアップ

### 1. Python依存関係インストール（ローカル実行する場合）

```bash
pip install -r requirements_stock.txt
```

Yahoo Financeはアカウント登録・APIキーが不要なため、GitHub Secretsの設定は不要です。

### 2. GitHub Pages を有効化

Settings → Pages → Source を `main` ブランチの `/docs` フォルダに設定。

公開URL: `https://yuki444.github.io/test/`

## 手動実行

```bash
python scripts/fetch_data.py
python scripts/score_stocks.py
python scripts/auto_trade.py
python scripts/generate_dashboard.py
```

週次振り返り（重み調整）は単独でも実行可能:

```bash
python scripts/weekly_reflect.py
```

GitHub Actions からの手動実行: Actions タブ → `Daily Stock Pipeline` または `Weekly Reflection` → Run workflow。

## 自動実行スケジュール

| ワークフロー | 実行タイミング | 内容 |
|---|---|---|
| `daily_stock.yml` | 毎日 00:00 UTC（09:00 JST） | データ取得→スコアリング→仮想売買→ダッシュボード生成→コミット |
| `weekly_reflect.yml` | 毎週月曜 23:00 UTC（火曜 08:00 JST） | 先週の予測精度を検証しスコア重みを自動調整→コミット |

## ファイル構成

```
scripts/
  fetch_data.py         ← ①Yahoo Financeからデータ取得
  yahoo_client.py       ← Yahoo Financeクライアント（yfinance）
  score_stocks.py       ← ②4軸スコアリング
  scoring.py            ← スコアリングロジック（stock-app/src/utils/scoring.ts と同一ロジック）
  technicals.py          ← テクニカル指標計算（stock-app/src/utils/technicals.ts と同一ロジック）
  universe.py            ← 対象30銘柄リスト
  auto_trade.py          ← ③仮想売買（TOP10均等配分・売却ルール評価）
  generate_dashboard.py  ← ④ダッシュボード生成（docs/index.html）
  weekly_reflect.py      ← ⑤週次振り返り・重み自動調整
  templates/
    dashboard.html.j2    ← ダッシュボードテンプレート
    reflection.html.j2   ← 振り返りレポートテンプレート

config/
  scoring_weights.json  ← 4軸の重み係数（weekly_reflect.pyが自動調整）
  trade_rules.json      ← デフォルト売却ルール（損切/利確/トレーリング/保有日数）

data/
  YYYY-MM-DD/
    raw/{code}_quotes.json       ← 日次株価
    raw/{code}_statements.json   ← 財務情報
    scores.json                  ← 全銘柄スコア（根拠付き）
    portfolio.json               ← その日時点の仮想ポートフォリオ
    trades.json                  ← その日の売買記録（理由付き）

docs/
  index.html             ← 最新ダッシュボード（GitHub Pages公開用）
  reports/                ← 過去ダッシュボードのPages公開用コピー

reports/
  YYYY-MM-DD_dashboard.html    ← 日次ダッシュボードの履歴
  YYYY-MM-DD_reflection.html   ← 週次振り返りレポート

.github/workflows/
  daily_stock.yml         ← 毎日自動実行
  weekly_reflect.yml      ← 毎週自動実行
```

## スコアリング（4軸）

| 軸 | 満点 | 主な評価項目 |
|---|---|---|
| テクニカル | 90pt | MA5>MA25(+20) / MA25>MA50(+30) / RSI30-55(+20) / MACDゴールデンクロス(+20) / 出来高急増(+10) |
| ファンダメンタル | 75pt | PBR<1(+20) / PER<12(+20) / EPS黒字(+15) / 配当利回り3%超(+20) |
| モメンタム | 45pt | 5日リターン>0(+15) / 20日リターン>5%(+20) / 60日リターン>0(+10) |
| ニュース | 45pt | 7日以内決算開示(+20) / EPS上振れ10%超(+25) |

各軸のスコアに `config/scoring_weights.json` の重みを乗算して合計スコアを算出。
重みは `weekly_reflect.py` が先週の予測精度（相関係数）に応じて±0.2の範囲で自動調整する。

## 対象30銘柄

トヨタ自動車, ソニーグループ, キーエンス, ソフトバンクグループ, 三菱UFJ, 任天堂,
ダイキン工業, KDDI, 東京エレクトロン, ファーストリテイリング, リクルートHD, 第一三共,
村田製作所, 信越化学工業, NTT, 本田技研工業, HOYA, デンソー, 中外製薬, オリエンタルランド,
三井住友FG, 東京海上HD, ファナック, テルモ, 三菱電機, ブリヂストン, 味の素,
セブン&アイHD, 富士フイルムHD, 武田薬品（`scripts/universe.py` で管理）

## データソースについて（Yahoo Finance）

`yfinance` ライブラリ経由でYahoo Financeの非公式エンドポイントから取得している。
APIキー・登録不要な代わりに、以下の制約がある:

- 決算の「開示日」はYahoo Financeが正確に提供しないため、実績決算日（取得できた場合）→ 直近四半期末日の順で代用している。J-Quantsほど厳密な「7日以内の決算開示」判定にはならない。
- 非公式スクレイピングのためレート制限に敏感。`fetch_data.py` は1銘柄ごとに0.5秒待機している。頻繁にエラーになる場合は間隔を広げること。
- ティッカーは `{証券コード}.T`（東証）形式で固定。

## 注意事項

- `stock-app/`（React Nativeアプリ）はこのパイプラインとは独立して実装済み。変更しない。
- Suno音楽プロジェクト関連（`lyrics/`, `config/styles.json`, `.github/workflows/daily_generate.yml` 等）も変更しない。
- 本システムは仮想ポートフォリオによるシミュレーションであり、実際の株式売買・投資助言を行うものではありません。
