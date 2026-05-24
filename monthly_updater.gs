/**
 * ポケモンカード投資 月次テンプレート自動生成
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
const LOTTERY_DB_ID    = "2c190fd4164042dab27319020cc7501e"; // 抽選管理DB
const CARD_DB_ID       = "8bdbbad309f642f5b2983ba28bd0b6c7"; // 注目カードDB
const PACK_DB_ID       = "668ab474daaf40b5a472c40f72a82638"; // 最新パック情報DB
const CALENDAR_ID      = "mossan72.tsubaki@gmail.com";

const LOTTERY_SITES = [
  { name: "ポケモンセンターオンライン", url: "https://www.pokemon.co.jp/shop/pokemoncenter/" },
  { name: "ヨドバシ.com",               url: "https://www.yodobashi.com/" },
  { name: "ビックカメラ.com",           url: "https://www.biccamera.com/" },
  { name: "Amazon（先行予約）",         url: "https://www.amazon.co.jp/" },
  { name: "楽天市場",                   url: "https://www.rakuten.co.jp/" },
  { name: "古本市場",                   url: "https://www.furuhon-ichiba.com/" },
];

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

  Logger.log(`🎉 ${label} の月次テンプレート作成が完了しました！`);
}

// ─────────────────────────────────────────────
// Notion：月次ページ作成
// ─────────────────────────────────────────────

function createNotionMonthlyPage(token, label, year, month) {
  const lastDay  = new Date(year, month, 0).getDate();
  const startStr = `${year}-${String(month).padStart(2, "0")}-01`;
  const endStr   = `${year}-${String(month).padStart(2, "0")}-${lastDay}`;

  // 各サイトのチェックリスト行を生成
  const siteChecklist = LOTTERY_SITES.map(s =>
    `- [ ] [${s.name}](${s.url})`
  ).join("\n");

  const content = `## 📋 今月のアクション

### 1. 抽選サイト巡回チェック
${siteChecklist}

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
- [カードラッシュ買取](https://www.cardrush-pokemon.jp/buylist)
- [トレカMOLT 相場](https://www.torecamolt.com/)
- [メルカリ（売れた順）](https://www.mercari.com/jp/)
- [カードトレード](https://cardtrader.jp/)

- [ ] SAR・ACE SPECカードの相場を記録
- [ ] 大きく動いたカードがあればNotionの推定相場を更新

---

### 4. 新パック情報 確認
> [最新パック情報DB](https://www.notion.so/${PACK_DB_ID}) に新パックを追加

- [ ] [公式サイト](https://www.pokemon-card.com/products/) で新パック発表を確認
- [ ] 新パックがあれば「最新パック情報DB」に追加
- [ ] 注目カードがあれば「注目カードDB」にも追加

---

### 5. 今月の投資活動まとめ

| 項目 | 内容 |
|---|---|
| 応募した抽選 |  |
| 当選した商品 |  |
| 今月の出費 |  |
| 今月の売却益 |  |
| 保有カード変動 |  |
| 来月の狙い目 |  |

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
  const siteLinks = LOTTERY_SITES.map(s => `■ ${s.name}\n${s.url}`).join("\n\n");

  const desc = `${label} のポケモンカード投資チェックリストです。\n\n` +
    `📋 Notionチェックリスト:\n${notionUrl}\n\n` +
    `【抽選サイト巡回】\n${siteLinks}\n\n` +
    `【今月のやること】\n` +
    `① 各サイトの新着抽選を確認・応募\n` +
    `② 応募済み抽選の結果確認\n` +
    `③ 注目カードの相場チェック & Notion更新\n` +
    `④ 新パック情報の確認 & Notion追加`;

  const startDate = new Date(year, month - 1, 1, 9, 0, 0);  // 月初1日 9:00
  const endDate   = new Date(year, month - 1, 1, 10, 0, 0); // 月初1日 10:00

  const calendar = CalendarApp.getCalendarById(CALENDAR_ID);
  const event = calendar.createEvent(
    `🎴【ポケモンカード】${label} 月次チェック`,
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
// テスト用：手動実行でその場でページ作成を確認
// ─────────────────────────────────────────────

function testRun() {
  createMonthlyTemplate();
}
