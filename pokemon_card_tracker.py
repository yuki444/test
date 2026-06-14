#!/usr/bin/env python3
"""
カードゲーム投資トラッカー（ポケモン / ワンピース / ドラゴンボール）
各主要サイトの抽選情報をNotion・Googleカレンダーに自動登録するスクリプト。

セットアップ:
  pip install notion-client google-auth google-api-python-client requests
  cp config.json.example config.json  # 認証情報を設定
  python pokemon_card_tracker.py --help
"""

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from notion_client import Client as NotionClient
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

JST = timezone(timedelta(hours=9))

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "google_token.json")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# ────────────────────────────────────────────────
# 設定読み込み
# ────────────────────────────────────────────────

def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


# ────────────────────────────────────────────────
# Google Calendar 認証
# ────────────────────────────────────────────────

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                load_config()["google_credentials_path"], SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


# ────────────────────────────────────────────────
# カレンダーイベント追加
# ────────────────────────────────────────────────

def create_lottery_calendar_events(
    service,
    calendar_id: str,
    product_name: str,
    site: str,
    url: str,
    apply_start: Optional[datetime] = None,
    apply_end: Optional[datetime] = None,
    result_date: Optional[datetime] = None,
) -> list[str]:
    """抽選の応募開始・締切・結果確認をカレンダーに登録する。"""

    created_ids = []
    base_desc = f"商品: {product_name}\nサイト: {site}\nURL: {url}\n\nNotion抽選管理（投資ハブ内）:\nhttps://www.notion.so/36825aa13432819b9cbcc9a3c83cdc39"

    events = []
    if apply_start:
        events.append({
            "summary": f"🎴【抽選開始】{product_name}（{site}）",
            "start": apply_start,
            "end": apply_start + timedelta(hours=1),
            "color": "9",  # Blueberry
            "desc": f"⚡ 本日から応募受付開始！\n\n{base_desc}",
        })
    if apply_end:
        events.append({
            "summary": f"⏰【抽選締切】{product_name}（{site}）",
            "start": apply_end,
            "end": apply_end + timedelta(hours=1),
            "color": "6",  # Tangerine
            "desc": f"⚠️ 本日が応募締切日！まだの場合は今すぐ応募を。\n\n{base_desc}",
        })
    if result_date:
        events.append({
            "summary": f"🏆【結果確認】{product_name}（{site}）",
            "start": result_date,
            "end": result_date + timedelta(hours=1),
            "color": "11",  # Tomato
            "desc": f"当落結果を確認し、Notionのステータスを更新してください。\n\n当選 → 決済期限をカレンダーに追加 → 相場確認後 保持/即売を判断\n落選 → 次の抽選へ\n\n{base_desc}",
        })

    for ev in events:
        body = {
            "summary": ev["summary"],
            "description": ev["desc"],
            "start": {"dateTime": ev["start"].isoformat(), "timeZone": "Asia/Tokyo"},
            "end":   {"dateTime": ev["end"].isoformat(),   "timeZone": "Asia/Tokyo"},
            "colorId": ev["color"],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email",  "minutes": 60},
                    {"method": "popup",  "minutes": 0},
                ],
            },
        }
        result = service.events().insert(calendarId=calendar_id, body=body).execute()
        created_ids.append(result["id"])
        print(f"  ✅ カレンダー追加: {ev['summary']}")

    return created_ids


# ────────────────────────────────────────────────
# Notion 操作
# ────────────────────────────────────────────────

def add_lottery_to_notion(
    notion: NotionClient,
    lottery_db_id: str,
    product_name: str,
    site: str,
    url: str,
    box_price: Optional[int] = None,
    resale_price: Optional[int] = None,
    apply_start: Optional[datetime] = None,
    apply_end: Optional[datetime] = None,
    result_date: Optional[datetime] = None,
    memo: str = "",
    attraction: str = "",
) -> str:
    """抽選管理DBに新しいエントリを追加する。"""

    SITE_MAP = {
        "ポケモンセンター": "ポケモンセンター",
        "ヨドバシ": "ヨドバシ",
        "ビックカメラ": "ビックカメラ",
        "Amazon": "Amazon",
        "楽天": "楽天",
        "古本市場": "古本市場",
        "プレミアムバンダイ": "プレミアムバンダイ",
        "その他": "その他",
    }

    props: dict = {
        "商品名": {"title": [{"text": {"content": product_name}}]},
        "ステータス": {"select": {"name": "応募前"}},
        "URL": {"url": url},
    }

    site_name = SITE_MAP.get(site, "その他")
    props["サイト"] = {"select": {"name": site_name}}

    if box_price:
        props["BOX定価(円)"] = {"number": box_price}
    if resale_price:
        props["当選時二次流通価格(円)"] = {"number": resale_price}
    if apply_start:
        props["応募開始日"] = {"date": {"start": apply_start.strftime("%Y-%m-%d")}}
    if apply_end:
        props["応募締切日"] = {"date": {"start": apply_end.strftime("%Y-%m-%d")}}
    if result_date:
        props["結果確認日"] = {"date": {"start": result_date.strftime("%Y-%m-%d")}}
    if memo:
        props["メモ"] = {"rich_text": [{"text": {"content": memo}}]}
    if attraction in ("S", "A", "B", "C"):
        props["投資魅力度"] = {"select": {"name": attraction}}

    page = notion.pages.create(
        parent={"database_id": lottery_db_id},
        properties=props,
    )
    print(f"  ✅ Notion追加: {product_name} ({site})")
    return page["id"]


def add_card_to_notion(
    notion: NotionClient,
    card_db_id: str,
    card_name: str,
    pack: str,
    rarity: str,
    enc_rate: str,
    price: int,
    rating: str,
    note: str = "",
) -> str:
    """注目カードDBにカードを追加する。"""

    RATING_MAP = {
        "SSS": "★★★ 強く推奨",
        "SS": "★★★ 強く推奨",
        "S": "★★★ 強く推奨",
        "A": "★★ 推奨",
        "B": "★ 様子見",
        "C": "対象外",
    }

    props = {
        "カード名": {"title": [{"text": {"content": card_name}}]},
        "収録パック": {"rich_text": [{"text": {"content": pack}}]},
        "レアリティ": {"select": {"name": rarity}},
        "封入率(目安)": {"rich_text": [{"text": {"content": enc_rate}}]},
        "推定相場(円)": {"number": price},
        "投資評価": {"select": {"name": RATING_MAP.get(rating, "★ 様子見")}},
    }
    if note:
        props["備考"] = {"rich_text": [{"text": {"content": note}}]}

    page = notion.pages.create(
        parent={"database_id": card_db_id},
        properties=props,
    )
    print(f"  ✅ カード追加: {card_name} ({pack})")
    return page["id"]


# ────────────────────────────────────────────────
# 抽選情報をまとめて登録
# ────────────────────────────────────────────────

def register_lottery(
    config: dict,
    product_name: str,
    site: str,
    url: str,
    box_price: Optional[int] = None,
    resale_price: Optional[int] = None,
    apply_start_str: Optional[str] = None,
    apply_end_str: Optional[str] = None,
    result_date_str: Optional[str] = None,
    memo: str = "",
    skip_calendar: bool = False,
    attraction: str = "",
) -> None:
    """
    抽選情報をNotion + Google Calendarに同時登録するメイン関数。

    使用例:
        python pokemon_card_tracker.py register \\
          --name "超電ブレイカー 5BOXセット" \\
          --site ポケモンセンター \\
          --url https://www.pokemon.co.jp/... \\
          --apply-start 2026-05-25 \\
          --apply-end 2026-05-31 \\
          --result 2026-06-05 \\
          --box-price 27500 \\
          --resale 35000
    """

    def parse_dt(s: Optional[str]) -> Optional[datetime]:
        return datetime.fromisoformat(s).replace(tzinfo=JST) if s else None

    apply_start = parse_dt(apply_start_str)
    apply_end   = parse_dt(apply_end_str)
    result_date = parse_dt(result_date_str)

    notion = NotionClient(auth=config["notion_token"])
    add_lottery_to_notion(
        notion,
        config["lottery_db_id"],
        product_name, site, url,
        box_price, resale_price,
        apply_start, apply_end, result_date,
        memo, attraction,
    )

    # A以上のみカレンダー登録対象（B/Cはスキップ）
    if attraction in ("B", "C") and not skip_calendar:
        print(f"  ℹ️  投資魅力度{attraction}のためカレンダー登録をスキップ（対象はA以上のみ）")
        skip_calendar = True

    if not skip_calendar:
        service = get_calendar_service()
        create_lottery_calendar_events(
            service,
            config["calendar_id"],
            product_name, site, url,
            apply_start, apply_end, result_date,
        )


# ────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ポケモンカード投資トラッカー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 抽選を登録（Notion + カレンダー）
  python pokemon_card_tracker.py register \\
    --name "SV最新弾 1BOX" --site ポケモンセンター \\
    --url https://... --apply-start 2026-06-01 \\
    --apply-end 2026-06-07 --result 2026-06-14

  # Notionだけ登録（カレンダー不要な場合）
  python pokemon_card_tracker.py register --skip-calendar \\
    --name "..." --site ヨドバシ --url https://...

  # カードを注目カードDBに追加
  python pokemon_card_tracker.py add-card \\
    --name "リザードン ex SAR" --pack "SV最新弾" \\
    --rarity SAR --price 50000 --rating S
        """,
    )

    sub = parser.add_subparsers(dest="cmd")

    # register サブコマンド
    reg = sub.add_parser("register", help="抽選をNotionとカレンダーに登録")
    reg.add_argument("--name",          required=True, help="商品名")
    reg.add_argument("--site",          required=True,
                     choices=["ポケモンセンター","ヨドバシ","ビックカメラ","Amazon","楽天","古本市場","プレミアムバンダイ","その他"],
                     help="販売サイト")
    reg.add_argument("--url",           required=True, help="抽選ページURL")
    reg.add_argument("--apply-start",   metavar="YYYY-MM-DD", help="応募開始日")
    reg.add_argument("--apply-end",     metavar="YYYY-MM-DD", help="応募締切日")
    reg.add_argument("--result",        metavar="YYYY-MM-DD", help="結果確認日")
    reg.add_argument("--box-price",     type=int, help="BOX定価（円）")
    reg.add_argument("--resale",        type=int, help="当選時想定二次流通価格（円）")
    reg.add_argument("--memo",          default="", help="メモ")
    reg.add_argument("--attraction",     default="",
                     choices=["S","A","B","C",""], help="投資魅力度 S=必須/A=強推奨/B=推奨/C=任意")
    reg.add_argument("--skip-calendar", action="store_true", help="カレンダー登録をスキップ")

    # add-card サブコマンド
    card = sub.add_parser("add-card", help="注目カードDBにカードを追加")
    card.add_argument("--name",     required=True, help="カード名")
    card.add_argument("--pack",     required=True, help="収録パック名")
    card.add_argument("--rarity",   required=True,
                      choices=["MUR","FUR","BWR","TR","SCR","SAR","ACE SPEC","SR","HR","UR","AR","RRR","RR","R"],
                      help="レアリティ (MUR=メガウルトラレア/FUR=フューチャリスティックレア/BWR=B&Wレア/TR=トレジャーレア/SCR=シークレット)")
    card.add_argument("--enc-rate", default="不明", help="封入率（例: 約1/8BOX）")
    card.add_argument("--price",    type=int, required=True, help="推定相場（円）")
    card.add_argument("--rating",   default="B",
                      choices=["S","A","B","C"], help="投資評価")
    card.add_argument("--note",     default="", help="備考")

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
        return

    config = load_config()

    if args.cmd == "register":
        register_lottery(
            config,
            product_name=args.name,
            site=args.site,
            url=args.url,
            box_price=args.box_price,
            resale_price=args.resale,
            apply_start_str=args.apply_start,
            apply_end_str=args.apply_end,
            result_date_str=args.result,
            memo=args.memo,
            skip_calendar=args.skip_calendar,
            attraction=args.attraction,
        )

    elif args.cmd == "add-card":
        notion = NotionClient(auth=config["notion_token"])
        add_card_to_notion(
            notion,
            config["card_db_id"],
            card_name=args.name,
            pack=args.pack,
            rarity=args.rarity,
            enc_rate=args.enc_rate,
            price=args.price,
            rating=args.rating,
            note=args.note,
        )


if __name__ == "__main__":
    main()
