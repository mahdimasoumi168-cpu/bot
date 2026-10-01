import httpx
from .config import settings

API="https://api.telegram.org/bot"+settings.telegram_bot_token

async def tg(method,payload=None):
    async with httpx.AsyncClient(timeout=settings.request_timeout) as c:
        r=await c.post(API+"/"+method,data=payload or {})
        r.raise_for_status()
        body=r.json()
        if not body.get("ok"): raise RuntimeError(body.get("description","Telegram API error"))
        return body["result"]

async def set_webhook():
    if not settings.public_base_url: raise RuntimeError("PUBLIC_BASE_URL is missing")
    return await tg("setWebhook",{"url":settings.public_base_url.rstrip("/")+"/webhook/telegram","secret_token":settings.telegram_webhook_secret,"allowed_updates":'["channel_post","edited_channel_post"]'})

async def download_file(file_id):
    info=await tg("getFile",{"file_id":file_id})
    async with httpx.AsyncClient(timeout=settings.request_timeout) as c:
        r=await c.get("https://api.telegram.org/file/bot"+settings.telegram_bot_token+"/"+info["file_path"])
        r.raise_for_status()
        return info["file_path"].split("/")[-1],r.content
