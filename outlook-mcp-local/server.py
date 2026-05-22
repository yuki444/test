#!/usr/bin/env python3
"""
Outlook Desktop MCP Server
Azure登録不要 - ローカルOutlookにCOM経由で直接接続
依存: pip install mcp pywin32
"""

import json
import sys
import asyncio
from datetime import datetime, timedelta

try:
    import win32com.client
except ImportError:
    print("Error: pywin32が必要です。pip install pywin32 を実行してください", file=sys.stderr)
    sys.exit(1)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

server = Server("outlook-desktop")


def get_outlook():
    try:
        return win32com.client.Dispatch("Outlook.Application")
    except Exception as e:
        raise RuntimeError(f"Outlookに接続できません（起動しているか確認してください）: {e}")


def get_namespace():
    return get_outlook().GetNamespace("MAPI")


@server.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="list_emails",
            description="Outlookの受信トレイからメール一覧を取得",
            inputSchema={
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "description": "取得件数（デフォルト: 20）",
                        "default": 20,
                    }
                },
            },
        ),
        types.Tool(
            name="read_email",
            description="メールの本文を読む",
            inputSchema={
                "type": "object",
                "properties": {
                    "entry_id": {
                        "type": "string",
                        "description": "list_emailsで取得したentry_id",
                    }
                },
                "required": ["entry_id"],
            },
        ),
        types.Tool(
            name="search_emails",
            description="メールを検索",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "検索キーワード（件名・送信者・本文）",
                    },
                    "count": {
                        "type": "integer",
                        "description": "最大件数（デフォルト: 10）",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="send_email",
            description="Outlook経由でメールを送信",
            inputSchema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "宛先メールアドレス"},
                    "subject": {"type": "string", "description": "件名"},
                    "body": {"type": "string", "description": "本文"},
                    "cc": {
                        "type": "string",
                        "description": "CC（省略可）",
                        "default": "",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        ),
        types.Tool(
            name="list_calendar_events",
            description="Outlookカレンダーの予定一覧を取得",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "何日先まで取得するか（デフォルト: 7）",
                        "default": 7,
                    }
                },
            },
        ),
        types.Tool(
            name="create_calendar_event",
            description="Outlookカレンダーに予定を作成",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "件名"},
                    "start": {
                        "type": "string",
                        "description": "開始日時（例: 2024-01-15 14:00）",
                    },
                    "end": {
                        "type": "string",
                        "description": "終了日時（例: 2024-01-15 15:00）",
                    },
                    "body": {
                        "type": "string",
                        "description": "詳細・メモ（省略可）",
                        "default": "",
                    },
                    "location": {
                        "type": "string",
                        "description": "場所（省略可）",
                        "default": "",
                    },
                },
                "required": ["subject", "start", "end"],
            },
        ),
        types.Tool(
            name="reply_email",
            description="メールに返信",
            inputSchema={
                "type": "object",
                "properties": {
                    "entry_id": {
                        "type": "string",
                        "description": "返信対象メールのentry_id",
                    },
                    "body": {"type": "string", "description": "返信本文"},
                },
                "required": ["entry_id", "body"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "list_emails":
            ns = get_namespace()
            count = arguments.get("count", 20)
            inbox = ns.GetDefaultFolder(6)  # olFolderInbox
            messages = inbox.Items
            messages.Sort("[ReceivedTime]", True)

            results = []
            for i, msg in enumerate(messages):
                if i >= count:
                    break
                try:
                    results.append(
                        {
                            "no": i + 1,
                            "entry_id": msg.EntryID,
                            "subject": msg.Subject or "(件名なし)",
                            "from": msg.SenderName or "",
                            "from_email": msg.SenderEmailAddress or "",
                            "received": str(msg.ReceivedTime)[:16]
                            if msg.ReceivedTime
                            else "",
                            "unread": bool(msg.UnRead),
                            "preview": (msg.Body or "")[:80].replace("\n", " "),
                        }
                    )
                except Exception:
                    continue

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(results, ensure_ascii=False, indent=2),
                )
            ]

        elif name == "read_email":
            ns = get_namespace()
            msg = ns.GetItemFromID(arguments["entry_id"])
            result = {
                "subject": msg.Subject or "(件名なし)",
                "from": msg.SenderName or "",
                "from_email": msg.SenderEmailAddress or "",
                "to": msg.To or "",
                "cc": msg.CC or "",
                "received": str(msg.ReceivedTime)[:16] if msg.ReceivedTime else "",
                "body": msg.Body or "",
            }
            msg.UnRead = False
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2),
                )
            ]

        elif name == "search_emails":
            ns = get_namespace()
            query = arguments["query"].lower()
            count = arguments.get("count", 10)
            inbox = ns.GetDefaultFolder(6)
            messages = inbox.Items
            messages.Sort("[ReceivedTime]", True)

            results = []
            for msg in messages:
                if len(results) >= count:
                    break
                try:
                    subject = (msg.Subject or "").lower()
                    sender = (msg.SenderName or "").lower()
                    body_preview = (msg.Body or "")[:500].lower()
                    if query in subject or query in sender or query in body_preview:
                        results.append(
                            {
                                "entry_id": msg.EntryID,
                                "subject": msg.Subject or "(件名なし)",
                                "from": msg.SenderName or "",
                                "received": str(msg.ReceivedTime)[:16]
                                if msg.ReceivedTime
                                else "",
                                "unread": bool(msg.UnRead),
                                "preview": (msg.Body or "")[:100].replace("\n", " "),
                            }
                        )
                except Exception:
                    continue

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(results, ensure_ascii=False, indent=2),
                )
            ]

        elif name == "send_email":
            outlook = get_outlook()
            mail = outlook.CreateItem(0)  # olMailItem
            mail.To = arguments["to"]
            mail.CC = arguments.get("cc", "")
            mail.Subject = arguments["subject"]
            mail.Body = arguments["body"]
            mail.Send()
            return [types.TextContent(type="text", text="メールを送信しました")]

        elif name == "reply_email":
            ns = get_namespace()
            msg = ns.GetItemFromID(arguments["entry_id"])
            reply = msg.Reply()
            reply.Body = arguments["body"] + "\n\n" + reply.Body
            reply.Send()
            return [types.TextContent(type="text", text="返信しました")]

        elif name == "list_calendar_events":
            ns = get_namespace()
            days = arguments.get("days", 7)
            calendar = ns.GetDefaultFolder(9)  # olFolderCalendar
            items = calendar.Items
            items.IncludeRecurrences = True
            items.Sort("[Start]")

            now = datetime.now()
            end_dt = now + timedelta(days=days)
            start_str = now.strftime("%m/%d/%Y %H:%M %p")
            end_str = end_dt.strftime("%m/%d/%Y %H:%M %p")
            items = items.Restrict(
                f"[Start] >= '{start_str}' AND [Start] <= '{end_str}'"
            )

            results = []
            for item in items:
                try:
                    results.append(
                        {
                            "subject": item.Subject or "(タイトルなし)",
                            "start": str(item.Start)[:16],
                            "end": str(item.End)[:16],
                            "location": item.Location or "",
                            "organizer": item.Organizer or "",
                            "body": (item.Body or "")[:200],
                        }
                    )
                except Exception:
                    continue

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(results, ensure_ascii=False, indent=2),
                )
            ]

        elif name == "create_calendar_event":
            outlook = get_outlook()
            appt = outlook.CreateItem(1)  # olAppointmentItem
            appt.Subject = arguments["subject"]
            appt.Start = arguments["start"]
            appt.End = arguments["end"]
            appt.Body = arguments.get("body", "")
            appt.Location = arguments.get("location", "")
            appt.Save()
            return [
                types.TextContent(
                    type="text",
                    text=f"予定「{arguments['subject']}」を作成しました",
                )
            ]

        else:
            return [types.TextContent(type="text", text=f"不明なツール: {name}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"エラー: {str(e)}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
