# 開発ルール（Claude Code 必読）

---

## ⚠️ Financial Planner — 確定済み設定値（絶対に勝手に変えない）

### ファイル
`financial-planner/index.html` — シングルファイルSPA。データは `localStorage('fp-data')` に保存。

### データ管理の仕組み
- `user-data.json` を GitHub（またはローカル fetch）から取得後、`Object.assign(data, parsed)` でマージ
- **その直後に必ず `applyMigrations(data)` を呼ぶ**（これをしないと古い値で上書きされる）
- `applyMigrations()` は `init()` と fallback fetch handler の両方で呼ばれている

### settings（migration で強制固定）
| フィールド | 正しい値 | 備考 |
|-----------|---------|------|
| retireAge | 55 | 早期退職 |
| retireAgeSpouse | 50 | 配偶者退職年齢 |
| salaryGrowth | 5.0 | 昇給率5% |
| selfIncomeCap | 13,000,000 | 年収上限1300万 |
| inflation | 1.5 | |
| endAge | ユーザー設定値を保持 | 100（強制変更禁止） |
| investReturn | ユーザー設定値を保持 | 強制変更禁止 |

### savings（migration で強制固定）
| フィールド | 正しい値 |
|-----------|---------|
| pensionSelf | 170,000円/月 |
| pensionSpouse | 110,000円/月 |
| invest | 200,000円/月 |
| deposit | 100,000円/月 |

### 主要イベント金額（全プラン共通、migration で修正）
| イベント名 | 金額 | 年齢 | 備考 |
|-----------|-----|------|------|
| 企業型DC退職金（本人） | +17,700,000 | 55 | |
| メットライフ②解約・払戻 | +6,500,000 | 55 | |
| メットライフ①解約・払戻 | +11,350,000 | 70 | |
| 老人ホーム入居一時金 | -26,000,000 | 75 | |
| 老人ホーム居住（月額） | 700,000/月 | 75〜 | 26年間、夫婦2人 |
| 配偶者の葬儀費用 | -3,000,000 | **100** | 絶対に88歳にしない |
| 本人の葬儀費用 | -3,000,000 | **100** | 絶対に90歳にしない |

### expenseSteps（migration で追加）
| fromAge | delta | 内容 |
|---------|-------|------|
| 55 | +60,000 | 退職後健康保険料（国保/任意継続） |
| 65 | -40,000 | 後期高齢者医療移行 |

### プラン構成
- **plan1**: 住み続ける（ローン完済）
- **plan2**: 20年後売却→賃貸 → 火災保険終了（age58）あり
- **plan3**: 8年ごとに新築 → 新築④住替（age70: 売6,500万→新築6,500万）あり

### 新規追加済みイベント（全プラン）
私立高校入学金×2、成人式×2、夫婦旅行×5、孫お祝い×4、住宅建築お祝い×2

### 資産・holdings 自動同期
- `applyMigrations()` 末尾で holdings の `value` フィールドから `assets.stocks/other/ideco/insurance` を自動更新
- cash/fixedDeposit/home は holdings 対象外なので手動入力値を保持
- 株価は GitHub Actions (`update-prices.yml`) が平日16:00 JST に prices.json を自動更新
- holdings の `shares` フィールドが必要（`refreshHoldingPrices` が price × shares → value を計算）

### 参考：2026-06-11 時点の実測値
| 資産 | 値 |
|-----|---|
| assets.cash | 300万 |
| assets.fixedDeposit | 200万 |
| assets.stocks (holdings由来) | 約2,060万 |
| assets.other (crypto+ESPP) | 約55万 |
| assets.home | 7,000万 |
| 株式比率（金融資産ベース） | 約79% |

---

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
