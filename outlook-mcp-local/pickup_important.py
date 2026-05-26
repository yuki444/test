#!/usr/bin/env python3
"""
重要・要返信の未読メールをピックアップするスクリプト
使い方: python pickup_important.py
依存: pip install pywin32
"""

import win32com.client
import re
from datetime import datetime

# 広告判定（mark_ads_read.py と同じ）
AD_SUBJECT_KEYWORDS = [
    "広告", "キャンペーン", "セール", "SALE", "クーポン", "割引",
    "特別価格", "限定", "お得", "無料", "メルマガ", "ニュースレター",
    "新着", "おすすめ", "ポイント", "会員限定", "先着", "期間限定",
    "タイムセール", "新商品", "入荷", "再入荷", "% off", "% discount",
    "free shipping", "special offer", "limited time", "unsubscribe",
]
AD_SENDER_PATTERNS = [
    r"no[-_]?reply@", r"noreply@", r"newsletter@", r"campaign@",
    r"promo@", r"marketing@", r"notification@", r"notify@",
    r"bulletin@", r"updates@", r"digest@",
]

def is_ad(msg):
    subject = (msg.Subject or "").lower()
    sender_email = (msg.SenderEmailAddress or "").lower()
    for kw in AD_SUBJECT_KEYWORDS:
        if kw.lower() in subject:
            return True
    for p in AD_SENDER_PATTERNS:
        if re.search(p, sender_email):
            return True
    try:
        headers = msg.PropertyAccessor.GetProperty(
            "http://schemas.microsoft.com/mapi/proptag/0x007D001E"
        )
        if headers and "list-unsubscribe" in headers.lower():
            return True
    except Exception:
        pass
    return False

def response_score(msg):
    """返信・対応が必要そうか採点（高いほど重要）"""
    score = 0
    hints = []

    subject = (msg.Subject or "").lower()
    body = (msg.Body or "")[:1000].lower()
    sender_email = (msg.SenderEmailAddress or "").lower()

    # 件名の重要シグナル
    urgent_words = ["urgent", "緊急", "至急", "重要", "確認", "お願い",
                    "依頼", "ご確認", "ご返信", "返信", "回答", "承認",
                    "承諾", "deadline", "期限", "締め切り", "要対応"]
    for w in urgent_words:
        if w in subject:
            score += 3
            hints.append(f"件名: 「{w}」")

    # 本文の質問・依頼シグナル
    question_patterns = ["？", "?", "いかがでしょうか", "いただけますか",
                         "お願いします", "よろしくお願い", "ご確認ください",
                         "教えてください", "いつまでに", "できますか",
                         "please", "could you", "would you", "let me know"]
    for p in question_patterns:
        if p in body:
            score += 2
            hints.append(f"本文: 質問・依頼あり")
            break

    # 個人からのメール（ドメインが会社っぽい）
    if not re.search(r"@(gmail|yahoo|hotmail|outlook|icloud)\.com", sender_email):
        if "@" in sender_email:
            score += 1
            hints.append("送信者: 企業・組織")

    # Re: / Fwd: は会話中
    if subject.startswith("re:") or subject.startswith("fw:") or subject.startswith("fwd:"):
        score += 2
        hints.append("返信スレッド")

    # 自分宛て（TO に自分）
    try:
        recipients = (msg.To or "").lower()
        if "@" in recipients and len(recipients.split(";")) <= 3:
            score += 1
            hints.append("少人数宛て")
    except Exception:
        pass

    return score, list(dict.fromkeys(hints))  # 重複除去


def main():
    print("Outlook に接続しています...")
    try:
        outlook = win32com.client.Dispatch("Outlook.Application")
        ns = outlook.GetNamespace("MAPI")
    except Exception as e:
        print(f"エラー: Outlook を起動してください。\n{e}")
        return

    inbox = ns.GetDefaultFolder(6)
    messages = inbox.Items
    messages.Sort("[ReceivedTime]", True)

    print("未読メールを分析しています...\n")

    important = []
    ad_count = 0
    limit = 200

    for i, msg in enumerate(messages):
        if i >= limit:
            break
        try:
            if not msg.UnRead:
                continue
            if is_ad(msg):
                ad_count += 1
                continue

            score, hints = response_score(msg)
            important.append({
                "subject": msg.Subject or "(件名なし)",
                "from": msg.SenderName or msg.SenderEmailAddress or "",
                "from_email": msg.SenderEmailAddress or "",
                "received": str(msg.ReceivedTime)[:16] if msg.ReceivedTime else "",
                "body_preview": (msg.Body or "")[:200].replace("\n", " ").strip(),
                "score": score,
                "hints": hints,
            })
        except Exception:
            continue

    # スコア順にソート
    important.sort(key=lambda x: x["score"], reverse=True)

    print("=" * 60)
    print(f"【重要・要対応 未読メール ピックアップ】")
    print(f"  広告メール（除外）: {ad_count} 件")
    print(f"  要確認メール: {len(important)} 件")
    print("=" * 60)

    if not important:
        print("\n要対応の未読メールはありませんでした。")
    else:
        for idx, m in enumerate(important, 1):
            priority = "🔴 緊急" if m["score"] >= 6 else "🟡 要確認" if m["score"] >= 3 else "⚪ 参考"
            print(f"\n[{idx}] {priority}")
            print(f"  件名  : {m['subject']}")
            print(f"  送信者: {m['from']} <{m['from_email']}>")
            print(f"  受信  : {m['received']}")
            if m["hints"]:
                print(f"  理由  : {', '.join(m['hints'])}")
            print(f"  本文  : {m['body_preview'][:120]}...")

    print("\n" + "=" * 60)
    print("この結果を Claude Code のチャットに貼り付けると、内容を整理・返信案を提案します。")
    print("=" * 60)


if __name__ == "__main__":
    main()
    input("\nEnter キーで終了...")
