from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import anthropic
import json
from pathlib import Path

app = Flask(__name__)
client = anthropic.Anthropic()

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PROFILE_FILE = DATA_DIR / "profile.json"
WARDROBE_FILE = DATA_DIR / "wardrobe.json"

SYSTEM_PROMPT = """あなたは、ファッションに無頓着な普通の家族持ち男性専属の、プロのワードローブコンサルタントです。

あなたの使命：
「ファッションに全く興味がなくても、清潔感があって家族と一緒にいても恥ずかしくない」を実現すること。

提案スタンス：
- 難しいことは言わない。「これを買えばOK」のシンプルな提案
- 合わせやすいベーシックカラー（白・黒・グレー・ネイビー・ベージュ）中心
- 「なぜこれが必要か」を短く明確に説明
- 手持ち服が不明な場合でも、ゼロから揃える前提で完結した提案をする

購入先と検索URL形式（アイテムごとに複数の購入先を案内すること）：
- UNIQLO: https://www.uniqlo.com/jp/ja/search/?q=キーワード
- GU: https://www.gu-global.com/jp/ja/search/?q=キーワード
- 無印良品: https://www.muji.com/jp/ja/search?query=キーワード
- ZOZOTOWN: https://zozo.jp/search/?p=キーワード
- Amazon: https://www.amazon.co.jp/s?k=キーワード
- 楽天ファッション: https://search.rakuten.co.jp/search/mall/キーワード/?genreId=558885
- H&M: https://www2.hm.com/ja_jp/search-results.html?q=キーワード

回答は必ず日本語で、マークダウン形式で書いてください。"""

SEASON_NAMES = {
    "spring": "春（3〜5月）",
    "summer": "夏（6〜8月）",
    "autumn": "秋（9〜11月）",
    "winter": "冬（12〜2月）",
}

BUDGET_LABELS = {
    "low": "節約モード（できれば1シーズン1万円以内）",
    "medium": "普通（1シーズン2〜3万円程度）",
    "high": "こだわりたい（予算はあまり気にしない）",
}

FAMILY_LABELS = {
    "single": "独身・一人暮らし",
    "partner": "パートナーと2人",
    "children_small": "小さい子供がいる（未就学〜小学生）",
    "children_teen": "中高生の子供がいる",
}


def load_json(filepath, default):
    if filepath.exists():
        return json.loads(filepath.read_text(encoding="utf-8"))
    return default


def save_json(filepath, data):
    filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@app.route("/")
def index():
    return render_template("index.html")


# Service worker must be served from root to control the whole app
@app.route("/sw.js")
def sw():
    response = app.send_static_file("sw.js")
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@app.route("/api/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        save_json(PROFILE_FILE, request.json)
        return jsonify({"status": "ok"})
    return jsonify(load_json(PROFILE_FILE, {
        "age": "", "height": "", "weight": "",
        "budget": "medium", "family": "children_small",
    }))


@app.route("/api/wardrobe", methods=["GET", "POST"])
def wardrobe():
    if request.method == "POST":
        save_json(WARDROBE_FILE, request.json)
        return jsonify({"status": "ok"})
    return jsonify(load_json(WARDROBE_FILE, {"items": []}))


@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.json
    season = data.get("season", "spring")
    profile = load_json(PROFILE_FILE, {})
    wardrobe = load_json(WARDROBE_FILE, {"items": []})

    wardrobe_items = wardrobe.get("items", [])
    if wardrobe_items:
        wardrobe_text = "\n".join(
            f"- {item['name']}（{item.get('category', 'その他')}・{item.get('color', '色未設定')}）"
            for item in wardrobe_items
        )
    else:
        wardrobe_text = "なし（ゼロから揃える前提で提案してください）"

    age = profile.get("age", "")
    height = profile.get("height", "")
    weight = profile.get("weight", "")
    body_text = f"身長{height}cm / 体重{weight}kg" if height or weight else "未設定"
    age_text = f"{age}歳" if age else "未設定"

    prompt = f"""以下のユーザー情報をもとに、{SEASON_NAMES.get(season, season)}のワードローブ提案をお願いします。

【ユーザー基本情報】
- 年齢: {age_text}
- 体型: {body_text}
- 予算感: {BUDGET_LABELS.get(profile.get('budget', 'medium'), '普通（1シーズン2〜3万円程度）')}
- 家族構成: {FAMILY_LABELS.get(profile.get('family', 'children_small'), '小さい子供がいる')}
- 普段の服: ほぼUNIQLOのみ、ファッションには無頓着

【現在の手持ちアイテム】
{wardrobe_text}

以下の構成で提案してください：

## {SEASON_NAMES.get(season, season)}ワードローブ提案

### まず揃えたい「絶対必要アイテム」
これだけあれば基本的なシーンをカバーできる3〜5点。各アイテムを以下の形式で：

**[アイテム名]**
- 用途: （どんなシーンで使うか1行）
- おすすめ: 商品名 / 価格帯
- 購入先: [UNIQLO](URL) / [GU](URL) / [無印](URL) / [ZOZOTOWN](URL) など複数

---

### あると格上がりする「プラスアルファアイテム」
2〜3点を同じ形式で

---

### 手持ちを活かしたコーデ例
（手持ちがない場合は「絶対必要アイテム」だけで完結するコーデ例を2〜3パターン）

---

### 今シーズンの買い物優先順位
1. ...（一言理由）
2. ...（一言理由）
3. ...（一言理由）
"""

    @stream_with_context
    def generate():
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'text': text}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
