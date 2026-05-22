#!/usr/bin/env python3
"""
広告・プロモーションメールを一括既読にするスクリプト
使い方: python mark_ads_read.py
依存: pip install pywin32
"""

import win32com.client
import re

# 広告メール判定ルール
AD_SUBJECT_KEYWORDS = [
    # 日本語
    "広告", "PR", "プロモーション", "キャンペーン", "セール", "SALE",
    "クーポン", "割引", "特別価格", "限定", "お得", "無料",
    "メルマガ", "ニュースレター", "お知らせ", "新着", "おすすめ",
    "ポイント", "会員限定", "先着", "期間限定", "タイムセール",
    "ご案内", "のご紹介", "新商品", "入荷", "再入荷",
    # 英語
    "[newsletter]", "[promo]", "[sale]", "[ad]", "unsubscribe",
    "% off", "% discount", "free shipping", "special offer",
    "limited time", "exclusive", "don't miss",
]

AD_SENDER_PATTERNS = [
    r"no[-_]?reply@", r"noreply@", r"newsletter@", r"news@",
    r"info@", r"mail@", r"campaign@", r"promo@", r"marketing@",
    r"notification@", r"notify@", r"bulletin@", r"updates@",
    r"digest@", r"alert@", r"support@.*\.(com|jp|net)$",
]

def is_advertising(msg):
    """広告メールかどうか判定"""
    try:
        subject = (msg.Subject or "").lower()
        sender_email = (msg.SenderEmailAddress or "").lower()

        # 件名キーワードチェック
        for kw in AD_SUBJECT_KEYWORDS:
            if kw.lower() in subject:
                return True, f"件名キーワード: {kw}"

        # 送信者パターンチェック
        for pattern in AD_SENDER_PATTERNS:
            if re.search(pattern, sender_email):
                return True, f"送信者パターン: {sender_email}"

        # List-Unsubscribe ヘッダー（マーケティングメールの標準）
        try:
            headers = msg.PropertyAccessor.GetProperty(
                "http://schemas.microsoft.com/mapi/proptag/0x007D001E"
            )
            if headers and "list-unsubscribe" in headers.lower():
                return True, "List-Unsubscribeヘッダーあり"
        except Exception:
            pass

    except Exception:
        pass

    return False, ""


def main():
    print("Outlook に接続しています...")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")
    except Exception as e:
        print(f"エラー: Outlook に接続できません。Outlook を起動してください。\n{e}")
        return

    inbox = ns.GetDefaultFolder(6)  # olFolderInbox
    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)

    print(f"受信トレイを確認しています...\n")

    marked = 0
    checked = 0
    limit = 500  # 最大チェック件数

    for i, msg in enumerate(messages):
        if i >= limit:
            break
        try:
            if not msg.UnRead:
                continue  # 既に既読はスキップ

            checked += 1
            is_ad, reason = is_advertising(msg)

            if is_ad:
                subject = msg.Subject or "(件名なし)"
                sender = msg.SenderName or msg.SenderEmailAddress or ""
                print(f"  既読: [{sender}] {subject[:50]}  ← {reason}")
                msg.UnRead = False
                marked += 1

        except Exception:
            continue

    print(f"\n完了: 未読 {checked} 件をチェックし、{marked} 件の広告メールを既読にしました。")


if __name__ == "__main__":
    main()
    input("\nEnter キーで終了...")
