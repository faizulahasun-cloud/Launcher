#!/usr/bin/env python3
"""Private Telegram-to-local-ChatGPT-Web bridge.

Uses the HTTP API exposed by a separately installed ChatGPT browser bridge.
This does not use the official OpenAI API. Browser automation is unofficial,
fragile, and may conflict with the service's terms. Use at your own discretion.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
ALLOWED_USER_ID = os.environ.get("TELEGRAM_ALLOWED_USER_ID", "").strip()
CHATGPT_BRIDGE_URL = os.environ.get("CHATGPT_BRIDGE_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "180"))
POLL_TIMEOUT = 25

if not BOT_TOKEN:
    raise SystemExit("Set TELEGRAM_BOT_TOKEN before starting.")
if not ALLOWED_USER_ID or not ALLOWED_USER_ID.isdigit():
    raise SystemExit("Set TELEGRAM_ALLOWED_USER_ID to your numeric Telegram user ID. Refusing to run without an owner allowlist.")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/"


def api(method: str, payload: dict | None = None, timeout: int = 40) -> dict:
    body = json.dumps(payload or {}).encode("utf-8")
    request = urllib.request.Request(
        TELEGRAM_API + method,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API {method} failed: {result}")
    return result


def send_message(chat_id: int, text: str) -> None:
    # Telegram limits message text to 4096 characters. Split conservatively.
    chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)] or ["(Empty reply)"]
    for chunk in chunks:
        api("sendMessage", {"chat_id": chat_id, "text": chunk}, timeout=40)


def ask_chatgpt(prompt: str) -> str:
    payload = json.dumps({"prompt": prompt, "startNewChat": False}).encode("utf-8")
    request = urllib.request.Request(
        CHATGPT_BRIDGE_URL + "/query",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("status") != "success" or not isinstance(result.get("response"), str):
        raise RuntimeError("ChatGPT bridge returned an unexpected response.")
    return result["response"].strip() or "(ChatGPT returned an empty response.)"


def main() -> None:
    me = api("getMe")["result"]
    print(f"Telegram bridge running as @{me.get('username', 'unknown')}. Owner allowlist enabled.")
    print(f"ChatGPT browser bridge: {CHATGPT_BRIDGE_URL}")
    offset = 0

    while True:
        try:
            updates = api("getUpdates", {
                "offset": offset,
                "timeout": POLL_TIMEOUT,
                "allowed_updates": ["message"],
            }, timeout=POLL_TIMEOUT + 10).get("result", [])

            for update in updates:
                offset = max(offset, int(update["update_id"]) + 1)
                message = update.get("message") or {}
                sender = message.get("from") or {}
                chat = message.get("chat") or {}
                text = message.get("text")

                if chat.get("type") != "private" or not isinstance(text, str):
                    continue
                if str(sender.get("id", "")) != ALLOWED_USER_ID:
                    # Do not reveal whether this bot is connected to an AI.
                    continue

                prompt = text.strip()
                if not prompt:
                    continue
                if prompt.startswith("/start") or prompt.startswith("/help"):
                    send_message(chat["id"], "Send a text message and I will forward it to your connected ChatGPT browser session. Use /new to start a fresh ChatGPT chat.")
                    continue

                start_new_chat = prompt == "/new"
                if start_new_chat:
                    prompt = "Start a fresh conversation. Reply only: Ready."
                try:
                    send_message(chat["id"], "Working…")
                    payload = json.dumps({
                        "prompt": prompt,
                        "startNewChat": start_new_chat,
                    }).encode("utf-8")
                    request = urllib.request.Request(
                        CHATGPT_BRIDGE_URL + "/query",
                        data=payload,
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                        result = json.loads(response.read().decode("utf-8"))
                    if result.get("status") != "success" or not isinstance(result.get("response"), str):
                        raise RuntimeError("Unexpected response from local ChatGPT bridge.")
                    send_message(chat["id"], result["response"].strip() or "(Empty reply)")
                except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError) as exc:
                    print(f"Request failed: {exc}")
                    send_message(chat["id"], "I couldn't get a reply from the local ChatGPT browser bridge. Check that Chrome is signed in, the extension is connected, and the bridge server is running.")
        except KeyboardInterrupt:
            print("Stopped.")
            return
        except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError, KeyError) as exc:
            print(f"Polling error: {exc}")
            time.sleep(3)


if __name__ == "__main__":
    main()
