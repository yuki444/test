/**
 * カードゲーム投資 月次テンプレート自動生成
 * 対象: ポケモンカード / ワンピースカード / ドラゴンボールカード
 * Google Apps Script
 *
 * 【セットアップ手順】
 * 1. https://script.google.com/ を開く
 * 2. 「新しいプロジェクト」→ このコードを貼り付けて保存
 * 3. 上部の「設定」アイコン → スクリプトのプロパティ に以下を追加:
 *      NOTION_TOKEN  → Notionインテグレーションのsecretトークン
 * 4. 「トリガー」（時計アイコン）→「トリガーを追加」
 *      実行する関数: createMonthlyTemplate
 *      イベントのソース: 時間主導型
 *      時間ベースのトリガー: 月タイマー → 月の初め → 午前9時〜10時
 * 5. 初回は手動で createMonthlyTemplate() を実行して動作確認
 */

// ─────────────────────────────────────────────
// 設定（変更不要 — スクリプトプロパティで管理）
// ─────────────────────────────────────────────
const HUB_PAGE_ID      = "36825aa13432819b9cbcc9a3c83cdc39"; // ポケモンカード投資ハブ
const LOTTERY_DB_ID    = "d17825aa54f947b790ff1342face83d4"; // 抽選管理（ハブ内インライン）
const CARD_DB_ID       = "8bdbbad309f642f5b2983ba28bd0b6c7"; // 注目カードDB
const PACK_DB_ID       = "668ab474daaf40b5a472c40f72a82638"; // 最新パック情報DB
const CALENDAR_ID      = "mossan72.tsubaki@gmail.com";

// ポケモンカード 抽選サイト
const POKEMON_SITES = [
  { name: "ポケモンセンターオンライン", url: "https://www.pokemon.co.jp/shop/pokemoncenter/" },
  { name: "ヨドバシ.com",               url: "https://www.yodobashi.com/" },
  { name: "ビックカメラ.com",           url: "https://www.biccamera.com/" },
  { name: "Amazon（招待販売）",         url: "https://www.amazon.co.jp/" },
  { name: "楽天市場",                   url: "https://www.rakuten.co.jp/" },
  { name: "古本市場",                   url: "https://www.furuhon-ichiba.com/" },
];

// ワンピースカード 抽選サイト
const ONEPIECE_SITES = [
  { name: "プレミアムバンダイ",         url: "https://p-bandai.jp/item/item-1000108591/" },
  { name: "ヨドバシ.com",               url: "https://www.yodobashi.com/" },
  { name: "ビックカメラ.com",           url: "https://www.biccamera.com/" },
  { name: "Amazon（招待販売）",         url: "https://www.amazon.co.jp/" },
  { name: "楽天市場",                   url: "https://www.rakuten.co.jp/" },
  { name: "バンダイナムコ Cross Store", url: "https://bandainamco-am.co.jp/official_shop/onepiece-cardgame/" },
];

// ドラゴンボールカード 抽選サイト
const DRAGONBALL_SITES = [
  { name: "プレミアムバンダイ",         url: "https://p-bandai.jp/" },
  { name: "ヨドバシ.com",               url: "https://www.yodobashi.com/" },
  { name: "ビックカメラ.com",           url: "https://www.biccamera.com/" },
  { name: "Amazon",                     url: "https://www.amazon.co.jp/" },
  { name: "楽天市場",                   url: "https://www.rakuten.co.jp/" },
];

// 後方互換（旧コードから参照している場合のため）
const LOTTERY_SITES = POKEMON_SITES;

// 投資魅力度評価基準
const ATTRACTION_GUIDE = `【投資魅力度基準】
S: 定価3倍超確実 / 記念・周年弾 / 新レアリティ初登場 → 必ず応募
A: 定価2倍超見込み / 超人気キャラ/超高レアリティ封入 → 強く推奨
B: 定価1.3〜2倍見込み / 標準クラス弾 → 応募推奨
C: 定価割れリスクあり → 任意`;

// ─────────────────────────────────────────────
// メイン：月次テンプレート作成
// ─────────────────────────────────────────────

function createMonthlyTemplate() {
  const token = PropertiesService.getScriptProperties().getProperty("NOTION_TOKEN");
  if (!token) {
    Logger.log("❌ NOTION_TOKEN が設定されていません。スクリプトのプロパティを確認してください。");
    return;
  }

  const now   = new Date();
  const year  = now.getFullYear();
  const month = now.getMonth() + 1;
  const label = `${year}年${month}月`;

  Logger.log(`📅 ${label} のテンプレートを作成します...`);

  // Notionにページを作成
  const pageId = createNotionMonthlyPage(token, label, year, month);
  Logger.log(`✅ Notion作成完了: https://www.notion.so/${pageId.replace(/-/g, "")}`);

  // Googleカレンダーにも今月分のチェックイベントを追加
  createMonthlyCalendarEvent(year, month, label, pageId);
  Logger.log(`✅ カレンダー追加完了`);

  // 投資魅力度A以上のエントリーを取得してカレンダーにリマインド登録
  const addedCount = syncHighAttractionLotteriesToCalendar(token);
  Logger.log(`✅ A以上の抽選リマインド登録: ${addedCount}件`);

  Logger.log(`🎉 ${label} の月次テンプレート作成が完了しました！`);
}

// ─────────────────────────────────────────────
// Notion：月次ページ作成
// ─────────────────────────────────────────────

function createNotionMonthlyPage(token, label, year, month) {
  const lastDay  = new Date(year, month, 0).getDate();
  const startStr = `${year}-${String(month).padStart(2, "0")}-01`;
  const endStr   = `${year}-${String(month).padStart(2, "0")}-${lastDay}`;

  // 各カードゲームのチェックリスト行を生成
  const pokemonChecklist  = POKEMON_SITES.map(s  => `- [ ] [${s.name}](${s.url})`).join("\n");
  const onepieceChecklist = ONEPIECE_SITES.map(s => `- [ ] [${s.name}](${s.url})`).join("\n");
  const dbChecklist       = DRAGONBALL_SITES.map(s => `- [ ] [${s.name}](${s.url})`).join("\n");

  const content = `## 📋 今月のアクション

### 1. 抽選サイト巡回チェック

#### 🎴 ポケモンカード
${pokemonChecklist}

#### 🏴‍☠️ ワンピースカード
${onepieceChecklist}

#### 🐉 ドラゴンボールカード
${dbChecklist}

---

### 2. 応募中の抽選 結果確認
> [抽選管理DB](https://www.notion.so/${LOTTERY_DB_ID}) を開いてステータスが「結果待ち」のものを確認
- [ ] 全サイトのマイページで当落を確認
- [ ] 当選 → ステータスを「当選」に更新し決済期限をカレンダーへ追加
- [ ] 落選 → ステータスを「落選」に更新

---

### 3. 注目カード 相場チェック
> [注目カードDB](https://www.notion.so/${CARD_DB_ID}) の推定相場を更新する

参考サイト:
- [カードラッシュ買取(ポケカ)](https://www.cardrush-pokemon.jp/buylist)
- [カードラッシュ買取(ワンピース)](https://www.cardrush-onepiece.jp/buylist)
- [スニーカーダンク 相場](https://snkrdunk.com/)
- [メルカリ（売れた順）](https://www.mercari.com/jp/)

ポケモンカード注目レアリティ: MUR(~50BOX/枚) / FUR / BWR / SAR
ワンピースカード注目レアリティ: TR(~456BOX/枚) / コミックパラレル / SAR
ドラゴンボールカード注目レアリティ: SCR スーパーパラレル版

- [ ] 各ゲームの超高レアリティカードの相場を記録
- [ ] 大きく動いたカードがあればNotionの推定相場を更新

---

### 4. 新パック情報 確認

#### ポケモンカード
- [ ] [公式サイト](https://www.pokemon-card.com/products/) で新パック発表を確認
- [ ] MEGAシリーズ次回弾の抽選スケジュール確認

#### ワンピースカード
- [ ] [公式サイト](https://onepiece-cardgame.bandai.co.jp/) で次回OP弾を確認
- [ ] プレミアムバンダイ抽選スケジュール確認

#### ドラゴンボールカード
- [ ] [公式サイト](https://dbs-cardgame.com/fw/) で次回FB弾を確認
- [ ] プレミアムバンダイ / バンダイナムコ店舗抽選確認

---

### 5. 今月の投資活動まとめ

| 項目 | ポケモン | ワンピース | ドラゴンボール |
|---|---|---|---|
| 応募した抽選 |  |  |  |
| 当選した商品 |  |  |  |
| 今月の出費 |  |  |  |
| 今月の売却益 |  |  |  |
| 来月の狙い目 |  |  |  |

---

## 📝 メモ
`;

  const body = {
    parent: { page_id: HUB_PAGE_ID },
    icon: { type: "emoji", emoji: "📅" },
    properties: {
      title: {
        title: [{ type: "text", text: { content: `${label} 投資チェックリスト` } }]
      }
    },
    children: buildNotionBlocks(content)
  };

  const res = notionRequest(token, "POST", "/v1/pages", body);
  return res.id;
}

// ─────────────────────────────────────────────
// Notion：Markdown → ブロック変換（簡易版）
// ─────────────────────────────────────────────

function buildNotionBlocks(markdown) {
  const lines  = markdown.split("\n");
  const blocks = [];

  for (const raw of lines) {
    const line = raw.trimEnd();

    if (line.startsWith("## ")) {
      blocks.push(heading(2, line.slice(3)));
    } else if (line.startsWith("### ")) {
      blocks.push(heading(3, line.slice(4)));
    } else if (line.startsWith("- [ ] ")) {
      blocks.push(todo(line.slice(6)));
    } else if (line.startsWith("- ")) {
      blocks.push(bullet(line.slice(2)));
    } else if (line.startsWith("> ")) {
      blocks.push(quote(line.slice(2)));
    } else if (line.startsWith("---")) {
      blocks.push({ object: "block", type: "divider", divider: {} });
    } else if (line.startsWith("|")) {
      // テーブル行はそのままパラグラフとして扱う
      blocks.push(paragraph(line));
    } else if (line.trim() === "") {
      blocks.push(paragraph(""));
    } else {
      blocks.push(paragraph(line));
    }
  }

  return blocks;
}

function richText(str) {
  // [テキスト](URL) 形式のリンクをパース
  const linkRe = /\[([^\]]+)\]\(([^)]+)\)/g;
  const result  = [];
  let last = 0;
  let m;
  while ((m = linkRe.exec(str)) !== null) {
    if (m.index > last) result.push({ type: "text", text: { content: str.slice(last, m.index) } });
    result.push({ type: "text", text: { content: m[1], link: { url: m[2] } } });
    last = m.index + m[0].length;
  }
  if (last < str.length) result.push({ type: "text", text: { content: str.slice(last) } });
  return result.length ? result : [{ type: "text", text: { content: str } }];
}

function heading(level, text) {
  const type = `heading_${level}`;
  return { object: "block", type, [type]: { rich_text: richText(text) } };
}

function paragraph(text) {
  return { object: "block", type: "paragraph", paragraph: { rich_text: richText(text) } };
}

function bullet(text) {
  return { object: "block", type: "bulleted_list_item", bulleted_list_item: { rich_text: richText(text) } };
}

function todo(text) {
  return { object: "block", type: "to_do", to_do: { rich_text: richText(text), checked: false } };
}

function quote(text) {
  return { object: "block", type: "quote", quote: { rich_text: richText(text) } };
}

// ─────────────────────────────────────────────
// Google Calendar：月次チェックイベント追加
// ─────────────────────────────────────────────

function createMonthlyCalendarEvent(year, month, label, notionPageId) {
  const notionUrl = `https://www.notion.so/${notionPageId.replace(/-/g, "")}`;
  const pokeSites = POKEMON_SITES.map(s => `■ ${s.name}\n${s.url}`).join("\n\n");
  const opSites   = ONEPIECE_SITES.map(s => `■ ${s.name}\n${s.url}`).join("\n\n");
  const dbSites   = DRAGONBALL_SITES.map(s => `■ ${s.name}\n${s.url}`).join("\n\n");

  const desc = `${label} のカードゲーム投資チェックリストです。\n\n` +
    `📋 Notionチェックリスト:\n${notionUrl}\n\n` +
    `${ATTRACTION_GUIDE}\n\n` +
    `🎴【ポケモンカード 抽選サイト】\n${pokeSites}\n\n` +
    `🏴‍☠️【ワンピースカード 抽選サイト】\n${opSites}\n\n` +
    `🐉【ドラゴンボールカード 抽選サイト】\n${dbSites}\n\n` +
    `【今月のやること】\n` +
    `① 各サイトの新着抽選を確認・応募（魅力度S/Aを最優先）\n` +
    `② 応募済み抽選の結果確認\n` +
    `③ 注目カードの相場チェック & Notion更新\n` +
    `④ 各カードゲームの新弾情報確認 & Notion追加`;

  const startDate = new Date(year, month - 1, 1, 9, 0, 0);  // 月初1日 9:00
  const endDate   = new Date(year, month - 1, 1, 10, 0, 0); // 月初1日 10:00

  const calendar = CalendarApp.getCalendarById(CALENDAR_ID);
  const event = calendar.createEvent(
    `🃏【カードゲーム投資】${label} 月次チェック`,
    startDate,
    endDate,
    { description: desc }
  );
  event.setColor(CalendarApp.EventColor.BLUEBERRY);
  event.addEmailReminder(60);  // 1時間前にメール
  event.addPopupReminder(0);   // 当日ポップアップ
}

// ─────────────────────────────────────────────
// Notion API ヘルパー
// ─────────────────────────────────────────────

function notionRequest(token, method, path, body) {
  const options = {
    method,
    headers: {
      "Authorization": `Bearer ${token}`,
      "Notion-Version": "2022-06-28",
      "Content-Type": "application/json",
    },
    muteHttpExceptions: true,
  };
  if (body) options.payload = JSON.stringify(body);

  const res  = UrlFetchApp.fetch(`https://api.notion.com${path}`, options);
  const code = res.getResponseCode();
  const json = JSON.parse(res.getContentText());

  if (code >= 400) {
    Logger.log(`❌ Notion API エラー [${code}]: ${JSON.stringify(json)}`);
    throw new Error(`Notion API error ${code}`);
  }
  return json;
}

// ─────────────────────────────────────────────
// 投資魅力度A以上の抽選をカレンダーに自動同期
// ─────────────────────────────────────────────

function syncHighAttractionLotteriesToCalendar(token) {
  // 抽選管理DBからS/Aエントリーを取得
  const body = {
    filter: {
      and: [
        {
          property: "投資魅力度",
          select: { is_not_empty: true },
        },
        {
          or: [
            { property: "投資魅力度", select: { equals: "S" } },
            { property: "投資魅力度", select: { equals: "A" } },
          ],
        },
        {
          // 応募前・応募済みのみ対象（結果待ち/当選/落選は除外）
          or: [
            { property: "ステータス", select: { equals: "応募前" } },
            { property: "ステータス", select: { equals: "応募済み" } },
          ],
        },
      ],
    },
    page_size: 50,
  };

  const res = notionRequest(token, "POST", `/v1/databases/${LOTTERY_DB_ID}/query`, body);
  if (!res.results) return 0;

  const calendar = CalendarApp.getCalendarById(CALENDAR_ID);
  let added = 0;

  for (const page of res.results) {
    const props = page.properties;
    const name  = props["商品名"]?.title?.[0]?.plain_text || "（名称不明）";
    const site  = props["サイト"]?.select?.name || "";
    const rank  = props["投資魅力度"]?.select?.name || "";
    const url   = props["URL"]?.url || "";
    const memo  = props["メモ"]?.rich_text?.[0]?.plain_text || "";

    const startStr = props["応募開始日"]?.date?.start;
    const endStr   = props["応募締切日"]?.date?.start;
    const resultStr = props["結果確認日"]?.date?.start;

    const calTitle = `【抽選${rank}】${name}（${site}）`;

    // 重複登録防止：同名イベントが既に存在するかチェック（±3日の範囲）
    if (startStr) {
      const startDate = new Date(startStr);
      const searchStart = new Date(startDate); searchStart.setDate(searchStart.getDate() - 3);
      const searchEnd   = new Date(startDate); searchEnd.setDate(searchEnd.getDate() + 3);
      const existing = calendar.getEvents(searchStart, searchEnd, { search: name });
      if (existing.length > 0) continue; // 既に登録済み

      const endDate = new Date(startDate); endDate.setHours(startDate.getHours() + 1);
      const desc = `投資魅力度: ${rank}\nサイト: ${site}\nURL: ${url}\n\n${memo}\n\nNotion抽選管理: https://www.notion.so/${LOTTERY_DB_ID.replace(/-/g, "")}`;
      const ev = calendar.createEvent(`⚡【応募開始】${name}`, startDate, endDate, { description: desc });
      ev.setColor(CalendarApp.EventColor.BLUEBERRY);
      ev.addPopupReminder(0);
      added++;
    }

    if (endStr) {
      const endDate  = new Date(endStr);
      const evEnd    = new Date(endDate); evEnd.setHours(endDate.getHours() + 1);
      const desc = `⚠️ 本日が締切！\n投資魅力度: ${rank}\nサイト: ${site}\nURL: ${url}\n\n${memo}`;
      const ev = calendar.createEvent(`⏰【締切】${name}`, endDate, evEnd, { description: desc });
      ev.setColor(CalendarApp.EventColor.TANGERINE);
      ev.addEmailReminder(60);
      ev.addPopupReminder(0);
      added++;
    }

    if (resultStr) {
      const rDate = new Date(resultStr);
      const rEnd  = new Date(rDate); rEnd.setHours(rDate.getHours() + 1);
      const desc = `当落確認！\n投資魅力度: ${rank}\nサイト: ${site}\nURL: ${url}\n\nNotion抽選管理: https://www.notion.so/${LOTTERY_DB_ID.replace(/-/g, "")}`;
      const ev = calendar.createEvent(`🏆【結果確認】${name}`, rDate, rEnd, { description: desc });
      ev.setColor(CalendarApp.EventColor.TOMATO);
      ev.addEmailReminder(60);
      ev.addPopupReminder(0);
      added++;
    }
  }

  return added;
}

// ─────────────────────────────────────────────
// テスト用：手動実行でその場でページ作成を確認
// ─────────────────────────────────────────────

function testRun() {
  createMonthlyTemplate();
}
