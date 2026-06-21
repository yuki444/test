from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy

# --- カラーパレット ---
C_NAVY   = RGBColor(0x1A, 0x37, 0x5E)   # 紺（タイトル背景）
C_GOLD   = RGBColor(0xC8, 0x9B, 0x3C)   # 金（アクセント）
C_LIGHT  = RGBColor(0xF4, 0xF6, 0xFA)   # 薄青（スライド背景）
C_WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
C_TEXT   = RGBColor(0x1A, 0x1A, 0x2E)   # 本文ダーク
C_GREEN  = RGBColor(0x27, 0x7D, 0x52)   # 強調緑
C_RED    = RGBColor(0xC0, 0x39, 0x2B)   # 強調赤
C_BLUE2  = RGBColor(0x21, 0x6B, 0xAE)   # 青
C_GRAY   = RGBColor(0x6C, 0x75, 0x7D)   # グレー
C_YELLOW = RGBColor(0xFF, 0xF3, 0xCD)   # 薄黄（ハイライト背景）

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]  # 完全ブランク

# ─────────────────────────────────────────
# ユーティリティ
# ─────────────────────────────────────────
def add_rect(slide, l, t, w, h, fill=None, line=None, line_w=None):
    shape = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    shape.line.fill.background()
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = line
        if line_w:
            shape.line.width = line_w
    else:
        shape.line.fill.background()
    return shape

def add_text(slide, text, l, t, w, h, size=18, bold=False, color=C_TEXT,
             align=PP_ALIGN.LEFT, wrap=True, italic=False):
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb

def set_bg(slide, color):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_badge(slide, text, l, t, w=1.1, h=0.32, bg=C_NAVY, fg=C_WHITE, size=10):
    r = add_rect(slide, l, t, w, h, fill=bg)
    tf = r.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = True
    run.font.color.rgb = fg

def slide_header(slide, title, subtitle=None):
    """共通ヘッダーバー"""
    add_rect(slide, 0, 0, 13.33, 1.05, fill=C_NAVY)
    add_rect(slide, 0, 1.05, 13.33, 0.07, fill=C_GOLD)
    add_text(slide, title, 0.4, 0.12, 10, 0.7, size=26, bold=True, color=C_WHITE)
    if subtitle:
        add_text(slide, subtitle, 0.4, 0.68, 10, 0.4, size=12, color=C_GOLD)

# ─────────────────────────────────────────
# SLIDE 1: 表紙
# ─────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
set_bg(sl, C_NAVY)

# 背景装飾ライン
add_rect(sl, 0, 5.8, 13.33, 0.08, fill=C_GOLD)
add_rect(sl, 0, 6.0, 13.33, 1.5, fill=RGBColor(0x10, 0x22, 0x40))

# タイトル
add_text(sl, "正月 親族集まり", 1.2, 1.4, 11, 1.2,
         size=48, bold=True, color=C_WHITE, align=PP_ALIGN.CENTER)
add_text(sl, "プランニング提案書", 1.2, 2.5, 11, 0.9,
         size=36, bold=True, color=C_GOLD, align=PP_ALIGN.CENTER)

# サブ情報
add_text(sl, "2027年 1月3日（日）｜加古川・明石エリア", 1.2, 3.45, 11, 0.55,
         size=18, color=C_WHITE, align=PP_ALIGN.CENTER)
add_text(sl, "大人 10名 ＋ 子供 4名　計 14名", 1.2, 3.95, 11, 0.5,
         size=16, color=RGBColor(0xAA, 0xCC, 0xEE), align=PP_ALIGN.CENTER)

# フッター
add_text(sl, "Confidential – Family Planning Document", 0.5, 6.9, 12.3, 0.4,
         size=10, color=C_GRAY, align=PP_ALIGN.CENTER)

# ─────────────────────────────────────────
# SLIDE 2: 前提・基本条件
# ─────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
set_bg(sl, C_LIGHT)
slide_header(sl, "基本条件・前提", "Planning Conditions")

# 6つの条件カード
cards = [
    ("📅", "日程", "2027年1月3日（仮）"),
    ("👥", "人数", "大人10名・子供4名\n計14名"),
    ("📍", "エリア", "兵庫県\n加古川・明石周辺"),
    ("🏠", "会場", "自前の集まれる場所なし\n会場は別途確保が必要"),
    ("🎵", "やりたいこと", "カラオケ・トランプ等\n食事だけでなく遊びも"),
    ("🚶", "身体条件", "足が悪いメンバーなし\n移動・階段等 問題なし"),
]

for i, (icon, label, body) in enumerate(cards):
    col = i % 3
    row = i // 3
    lx = 0.35 + col * 4.3
    ty = 1.5 + row * 2.5
    add_rect(sl, lx, ty, 4.0, 2.1, fill=C_WHITE, line=C_GOLD, line_w=Pt(1.5))
    add_text(sl, icon + "  " + label, lx+0.15, ty+0.12, 3.7, 0.45,
             size=13, bold=True, color=C_NAVY)
    add_rect(sl, lx, ty+0.52, 4.0, 0.04, fill=C_GOLD)
    add_text(sl, body, lx+0.15, ty+0.65, 3.7, 1.2,
             size=13, color=C_TEXT)

# ─────────────────────────────────────────
# SLIDE 3: プランA 概要
# ─────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
set_bg(sl, C_LIGHT)
slide_header(sl, "プランA　レンタルスペース ＋ テイクアウト", "Plan A – Rental Space + Takeout")

# 左：メリット・デメリット
add_rect(sl, 0.3, 1.3, 4.2, 5.8, fill=C_WHITE, line=C_BLUE2, line_w=Pt(1))
add_text(sl, "特徴", 0.45, 1.4, 3.9, 0.45, size=14, bold=True, color=C_BLUE2)
add_rect(sl, 0.3, 1.82, 4.2, 0.04, fill=C_BLUE2)

pros = [
    "◎ コストが最も安い",
    "◎ 時間を自由に使える",
    "◎ トランプ・ゲームOK",
    "◎ 子供が騒いでも大丈夫",
    "◎ 持込自由",
    "△ 食事・飲み物の手配が必要",
    "△ 準備・片付けが発生",
    "△ 正月の選択肢は限られる",
]
for i, txt in enumerate(pros):
    col = C_GREEN if txt.startswith("◎") else C_GRAY
    add_text(sl, txt, 0.5, 1.95 + i*0.55, 3.8, 0.48,
             size=12, color=col)

# 右：3候補
right_items = [
    {
        "name": "A-1  ジャンカラ キャンプルーム",
        "sub": "加古川駅 徒歩8分 ｜ インスタベース掲載",
        "cap": "最大 20名",
        "price": "12,100円〜 / 時間",
        "note": "カラオケ＋ドリンクバー完備。遊びと食事が1室で完結！",
        "star": True,
    },
    {
        "name": "A-2  レンタルスタジオ Mi Crew",
        "sub": "JR加古川駅 徒歩3分 ｜ インスタベース掲載",
        "cap": "最大 20名",
        "price": "要確認（平均 435円/人/時）",
        "note": "駅近で集合しやすい多目的スペース。持込自由。",
        "star": False,
    },
    {
        "name": "A-3  明石駅前スペース",
        "sub": "JR明石駅 徒歩5分 ｜ スペースマーケット掲載",
        "cap": "最大 15〜20名",
        "price": "1,732〜2,310円 / 時間",
        "note": "子連れOK。明石側に集まる人が多い場合に便利。",
        "star": False,
    },
]

for i, item in enumerate(right_items):
    ty = 1.3 + i * 2.05
    bg = C_YELLOW if item["star"] else C_WHITE
    ln = C_GOLD if item["star"] else RGBColor(0xCC, 0xCC, 0xCC)
    add_rect(sl, 4.75, ty, 8.2, 1.85, fill=bg, line=ln, line_w=Pt(1.5 if item["star"] else 1))
    if item["star"]:
        add_badge(sl, "★ おすすめ", 11.6, ty+0.08, w=1.25, h=0.28, bg=C_GOLD, fg=C_WHITE, size=10)
    add_text(sl, item["name"], 4.9, ty+0.08, 6.5, 0.42, size=13, bold=True, color=C_NAVY)
    add_text(sl, item["sub"], 4.9, ty+0.48, 7.8, 0.3, size=10, color=C_GRAY, italic=True)
    add_text(sl, "収容: " + item["cap"] + "　　料金: " + item["price"],
             4.9, ty+0.78, 7.8, 0.35, size=11, color=C_TEXT)
    add_text(sl, item["note"], 4.9, ty+1.1, 7.8, 0.6, size=11, color=C_TEXT)

# ─────────────────────────────────────────
# SLIDE 4: プランA 食事・費用
# ─────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
set_bg(sl, C_LIGHT)
slide_header(sl, "プランA　食事手配 ＆ 費用概算", "Plan A – Food & Cost")

# 食事
add_rect(sl, 0.3, 1.3, 6.1, 5.8, fill=C_WHITE, line=C_BLUE2, line_w=Pt(1))
add_text(sl, "食事の手配方法", 0.5, 1.4, 5.7, 0.45, size=15, bold=True, color=C_BLUE2)
add_rect(sl, 0.3, 1.83, 6.1, 0.04, fill=C_BLUE2)

food_items = [
    ("おすすめ", "テイクアウト分担方式", C_GREEN),
    ("", "ごんた寿し（加古川）\n　出前・仕出し桶 ／ 正月期間は要事前予約", C_TEXT),
    ("", "はま寿司 テイクアウト\n　桶寿司ネット予約 ／ 大量注文向き", C_TEXT),
    ("", "善乃（加古川）\n　オードブル・揚げ物・仕出し対応", C_TEXT),
    ("補助", "デリバリー（Uber Eats / 出前館）\n　正月は遅延リスクあり。補填用として活用", C_GRAY),
    ("事前", "業務スーパー・コストコで前日調達\n　飲み物・お菓子・紙皿等", C_GRAY),
]
ty = 2.0
for badge, txt, col in food_items:
    if badge:
        add_badge(sl, badge, 0.45, ty, w=0.9, h=0.27,
                  bg=C_GREEN if badge=="おすすめ" else C_GOLD if badge=="補助" else C_BLUE2,
                  fg=C_WHITE, size=9)
        add_text(sl, txt, 1.45, ty-0.05, 4.8, 0.7, size=11, bold=True, color=col)
        ty += 0.42
    else:
        add_text(sl, txt, 0.5, ty, 5.7, 0.7, size=11, color=col)
        ty += 0.75

# 費用
add_rect(sl, 6.65, 1.3, 6.3, 5.8, fill=C_WHITE, line=C_GOLD, line_w=Pt(1))
add_text(sl, "費用概算（14名）", 6.85, 1.4, 5.9, 0.45, size=15, bold=True, color=C_NAVY)
add_rect(sl, 6.65, 1.83, 6.3, 0.04, fill=C_GOLD)

cost_rows = [
    ("レンタルスペース（5〜6時間）", "60,000円〜"),
    ("寿司テイクアウト×3〜4本", "25,000〜35,000円"),
    ("オードブル・揚げ物", "10,000〜15,000円"),
    ("飲み物・お菓子・消耗品", "8,000〜12,000円"),
]
ty2 = 2.05
for label, val in cost_rows:
    add_text(sl, label, 6.85, ty2, 4.2, 0.38, size=12, color=C_TEXT)
    add_text(sl, val, 10.5, ty2, 2.3, 0.38, size=12, color=C_TEXT, align=PP_ALIGN.RIGHT)
    add_rect(sl, 6.65, ty2+0.38, 6.3, 0.02, fill=RGBColor(0xDD,0xDD,0xDD))
    ty2 += 0.5

# 合計
add_rect(sl, 6.65, ty2+0.1, 6.3, 0.75, fill=C_NAVY)
add_text(sl, "合計（推定）", 6.85, ty2+0.18, 4.2, 0.5, size=14, bold=True, color=C_WHITE)
add_text(sl, "95,000〜112,000円", 9.1, ty2+0.18, 3.7, 0.5,
         size=14, bold=True, color=C_GOLD, align=PP_ALIGN.RIGHT)

add_rect(sl, 6.65, ty2+1.0, 6.3, 0.75, fill=C_LIGHT, line=C_GOLD, line_w=Pt(1))
add_text(sl, "1人あたり（概算）", 6.85, ty2+1.08, 4.2, 0.5, size=14, bold=True, color=C_NAVY)
add_text(sl, "約 6,800〜8,000円", 9.1, ty2+1.08, 3.7, 0.5,
         size=14, bold=True, color=C_GREEN, align=PP_ALIGN.RIGHT)

# 持ち物
ty3 = ty2+2.05
add_text(sl, "当日の持ち物", 6.85, ty3, 5.9, 0.38, size=12, bold=True, color=C_NAVY)
items = ["紙皿・紙コップ・割り箸", "ゴミ袋（大）×数枚",
         "トランプ・UNO・ゲーム類", "Bluetoothスピーカー", "延長コード・ウェットティッシュ"]
for j, it in enumerate(items):
    add_text(sl, "✔  " + it, 6.85, ty3+0.42+j*0.42, 5.9, 0.38, size=11, color=C_TEXT)

# ─────────────────────────────────────────
# SLIDE 5: プランB 概要
# ─────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
set_bg(sl, C_LIGHT)
slide_header(sl, "プランB　ホテル宴会場（加古川プラザホテル）", "Plan B – Hotel Banquet Hall")

# ホテル情報カード
add_rect(sl, 0.3, 1.3, 8.0, 3.5, fill=C_WHITE, line=C_NAVY, line_w=Pt(1.5))
add_text(sl, "加古川プラザホテル", 0.5, 1.42, 7.6, 0.55, size=20, bold=True, color=C_NAVY)
add_rect(sl, 0.3, 1.95, 8.0, 0.04, fill=C_GOLD)

hotel_info = [
    ("住所", "加古川市加古川町溝之口800"),
    ("TEL（宴会）", "079-421-6012　（受付 10:00〜17:00）"),
    ("宴会場", "大・中・小（芙蓉の間・牡丹の間 等）"),
    ("雰囲気", "シャンデリアあり／フォーマル〜セミフォーマル"),
    ("駐車場", "あり（台数は要確認）"),
]
for i, (k, v) in enumerate(hotel_info):
    ty = 2.1 + i * 0.52
    add_text(sl, k, 0.5, ty, 2.0, 0.45, size=12, bold=True, color=C_GRAY)
    add_text(sl, v, 2.6, ty, 5.5, 0.45, size=12, color=C_TEXT)

# 右：メリット・デメリット
add_rect(sl, 8.55, 1.3, 4.5, 3.5, fill=C_WHITE, line=RGBColor(0xCC,0xCC,0xCC), line_w=Pt(1))
add_text(sl, "メリット・デメリット", 8.7, 1.42, 4.2, 0.45, size=13, bold=True, color=C_NAVY)
add_rect(sl, 8.55, 1.95, 4.5, 0.04, fill=C_GOLD)
bds = [
    ("◎", "準備・片付けが不要", C_GREEN),
    ("◎", "料理の質・特別感が高い", C_GREEN),
    ("◎", "正月宴会プランあり", C_GREEN),
    ("△", "カラオケは別途手配", C_GRAY),
    ("△", "時間制限あり（〜3時間）", C_GRAY),
    ("△", "費用がやや高い", C_GRAY),
]
for i, (ico, txt, col) in enumerate(bds):
    add_text(sl, ico + "  " + txt, 8.7, 2.1+i*0.52, 4.1, 0.45, size=12, color=col)

# 費用表
add_rect(sl, 0.3, 5.0, 12.7, 2.2, fill=C_WHITE, line=C_GOLD, line_w=Pt(1))
add_text(sl, "費用概算（14名）", 0.5, 5.1, 12.2, 0.4, size=14, bold=True, color=C_NAVY)
add_rect(sl, 0.3, 5.5, 12.7, 0.04, fill=C_GOLD)

plan_rows = [
    ("プランタイプ", "1名あたり", "14名合計", True),
    ("和食コース（料理・飲物込み）", "5,000〜8,000円", "70,000〜112,000円", False),
    ("バイキング形式", "3,000〜5,000円", "42,000〜70,000円", False),
    ("会場のみ（持込）", "1,000〜2,000円", "14,000〜28,000円", False),
]
col_x = [0.5, 5.5, 9.5]
for i, (a, b, c, hdr) in enumerate(plan_rows):
    ty = 5.6 + i * 0.48
    bg = C_NAVY if hdr else (C_YELLOW if i==1 else None)
    if bg:
        add_rect(sl, 0.3, ty-0.06, 12.7, 0.46, fill=bg)
    fc = C_WHITE if hdr else C_TEXT
    fc2 = C_GOLD if i==1 else fc
    add_text(sl, a, col_x[0], ty, 4.8, 0.42, size=11, bold=hdr, color=fc)
    add_text(sl, b, col_x[1], ty, 3.8, 0.42, size=11, bold=hdr, color=fc, align=PP_ALIGN.CENTER)
    add_text(sl, c, col_x[2], ty, 3.3, 0.42, size=11, bold=hdr or i==1, color=fc2, align=PP_ALIGN.CENTER)

# ─────────────────────────────────────────
# SLIDE 6: 比較表
# ─────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
set_bg(sl, C_LIGHT)
slide_header(sl, "プランA vs プランB　比較", "Comparison")

headers = ["比較軸", "A レンタルスペース", "B ホテル宴会場"]
rows = [
    ("費用",         "◎ 安い（1人 6,800〜8,000円）",     "△ やや高い（1人 3,000〜8,000円）"),
    ("準備・片付け", "△ 自分たちで対応",                  "◎ ほぼ不要"),
    ("カラオケ・遊び","◎ A-1なら同室で可能",               "✕ 別途移動が必要"),
    ("子供の自由度", "◎ 騒いでもOK",                       "△ 場所による"),
    ("長居（5h+）", "◎ 時間制限なし",                      "△ 2〜3時間が目安"),
    ("料理の質",     "△ テイクアウト依存",                  "◎ ホテル料理"),
    ("特別感",       "○ 自分たちらしく",                    "◎ 正月らしい格式"),
    ("予約のしやすさ","○ オンライン即予約可",                "△ 電話 & 早期確認が必要"),
]

col_w = [3.5, 4.6, 4.6]
col_x = [0.3, 3.95, 8.7]
# ヘッダー行
for j, (hd, cx, cw) in enumerate(zip(headers, col_x, col_w)):
    bg = C_NAVY if j == 0 else (C_BLUE2 if j == 1 else C_GREEN)
    add_rect(sl, cx, 1.3, cw, 0.52, fill=bg)
    add_text(sl, hd, cx+0.1, 1.36, cw-0.2, 0.42, size=13, bold=True,
             color=C_WHITE, align=PP_ALIGN.CENTER)

for i, row in enumerate(rows):
    ty = 1.82 + i * 0.62
    bg_row = C_WHITE if i % 2 == 0 else RGBColor(0xEB, 0xEF, 0xF5)
    add_rect(sl, 0.3, ty, 12.95, 0.6, fill=bg_row)
    for j, (val, cx, cw) in enumerate(zip(row, col_x, col_w)):
        col = C_NAVY if j == 0 else (C_GREEN if "◎" in val else (C_RED if "✕" in val else C_TEXT))
        bold = j == 0
        add_text(sl, val, cx+0.1, ty+0.1, cw-0.2, 0.42, size=11,
                 bold=bold, color=col, align=PP_ALIGN.CENTER if j > 0 else PP_ALIGN.LEFT)

# 結論バナー
add_rect(sl, 0.3, 6.85, 12.95, 0.5, fill=C_NAVY)
add_text(sl, "コスト・自由度 重視 → プランA（A-1 ジャンカラ キャンプルーム）　　　　"
             "準備なし・特別感 重視 → プランB（加古川プラザホテル）",
         0.5, 6.88, 12.7, 0.44, size=12, bold=True, color=C_GOLD, align=PP_ALIGN.CENTER)

# ─────────────────────────────────────────
# SLIDE 7: 次のアクション
# ─────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
set_bg(sl, C_LIGHT)
slide_header(sl, "今すぐやること　Next Actions", "Action Plan")

steps = [
    {
        "no": "01",
        "who": "幹事",
        "title": "加古川プラザホテルへ電話",
        "body": "TEL: 079-421-6012（10:00〜17:00）\n1月3日・14名・小宴会場の空きと料金プランを確認",
        "dead": "今週中",
    },
    {
        "no": "02",
        "who": "幹事",
        "title": "ジャンカラ キャンプルーム 空き確認",
        "body": "インスタベース（https://www.instabase.jp/space/6255281347）\nにアクセスし1月3日の空き状況・料金を確認",
        "dead": "今週中",
    },
    {
        "no": "03",
        "who": "幹事",
        "title": "プランを1本に絞って予約",
        "body": "AまたはBどちらかに決定し即予約\n（正月3日は人気日・早い者勝ち）",
        "dead": "今月中",
    },
    {
        "no": "04",
        "who": "全員",
        "title": "親族へ日程案内・出欠確認",
        "body": "確定人数を把握（子供の年齢も確認）\nLINEグループ等で確認",
        "dead": "今月中",
    },
    {
        "no": "05",
        "who": "幹事",
        "title": "食事の手配（プランAの場合）",
        "body": "ごんた寿し・はま寿司テイクアウト予約\n正月テイクアウトは11月〜12月に早めに予約",
        "dead": "11〜12月",
    },
]

for i, s in enumerate(steps):
    col = i % 2
    row = i // 2
    lx = 0.3 + col * 6.55
    ty = 1.35 + row * 2.1
    if i == 4:  # 最後は中央
        lx = 3.57

    add_rect(sl, lx, ty, 6.2, 1.9, fill=C_WHITE,
             line=C_GOLD if i < 2 else RGBColor(0xCC,0xCC,0xCC), line_w=Pt(1.5 if i<2 else 1))

    # NO バッジ
    add_rect(sl, lx, ty, 0.52, 0.52, fill=C_NAVY)
    add_text(sl, s["no"], lx, ty+0.06, 0.52, 0.38, size=13, bold=True,
             color=C_WHITE, align=PP_ALIGN.CENTER)

    # DEADLINE バッジ
    add_badge(sl, s["dead"], lx+4.75, ty+0.1, w=1.35, h=0.3,
              bg=C_RED if i < 2 else C_BLUE2, fg=C_WHITE, size=9)

    add_text(sl, s["title"], lx+0.6, ty+0.08, 4.0, 0.42, size=13, bold=True, color=C_NAVY)
    add_text(sl, "担当: " + s["who"], lx+0.6, ty+0.48, 4.0, 0.28, size=10,
             color=C_GRAY, italic=True)
    add_text(sl, s["body"], lx+0.1, ty+0.82, 5.9, 0.98, size=11, color=C_TEXT)

# 下部メモ
add_rect(sl, 0.3, 6.85, 12.95, 0.48, fill=C_NAVY)
add_text(sl, "⚠  1月3日は正月繁忙期のため、場所確保は早期に。決まったらすぐ食事の手配へ進む。",
         0.5, 6.88, 12.7, 0.42, size=12, bold=True, color=C_GOLD, align=PP_ALIGN.CENTER)

# ─────────────────────────────────────────
# 保存
# ─────────────────────────────────────────
out = "/home/user/test/正月集まり_プランニング提案書.pptx"
prs.save(out)
print("Done:", out)
