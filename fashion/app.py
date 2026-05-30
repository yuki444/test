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
- UNIQLOとGUを軸に、コスパ最優先
- 合わせやすいベーシックカラー（白・黒・グレー・ネイビー・ベージュ）中心
- 「なぜこれが必要か」を短く明確に説明
- 具体的な商品名、価格帯、購入URLを必ず含める
- UNIQLO検索URL形式: https://www.uniqlo.com/jp/ja/search/?q=キーワード
- GU検索URL形式: https://www.gu-global.com/jp/ja/search/?q=キーワード

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
        wardrobe_text = "（まだ登録されていません）"

    prompt = f"""以下のユーザー情報をもとに、{SEASON_NAMES.get(season, season)}のワードローブ提案をお願いします。

【ユーザー基本情報】
- 年齢: {profile.get('age', '未設定')}歳
- 体型: 身長{profile.get('height', '未設定')}cm / 体重{profile.get('weight', '未設定')}kg
- 予算感: {BUDGET_LABELS.get(profile.get('budget', 'medium'), '普通')}
- 家族構成: {FAMILY_LABELS.get(profile.get('family', 'children_small'), '未設定')}
- 普段の服: ほぼUNIQLOのみ、ファッションには無頓着

【現在の手持ちアイテム】
{wardrobe_text}

以下の構成で提案してください：

## {SEASON_NAMES.get(season, season)}ワードローブ提案

### まず揃えたい「絶対必要アイテム」
これだけあれば基本的なシーンをカバーできる3〜5点を、以下の形式で：

**[アイテム名]**
- 用途: （どんなシーンで使うか1行）
- おすすめ: 商品名 / 価格帯
- 購入: [UNIQLO](URL) / [GU](URL)

---

### あると格上がりする「プラスアルファアイテム」
2〜3点を同じ形式で

---

### 手持ちアイテムとの組み合わせ
手持ちを活かした具体的なコーデ例を2〜3パターン（手持ちが未登録の場合はUNIQLO基本アイテムでの組み合わせ例）

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
