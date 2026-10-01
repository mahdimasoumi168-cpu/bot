import json
from sqlalchemy.exc import IntegrityError
from .db import SessionLocal
from .models import Message, Delivery
from .adapters import ADAPTERS
from .telegram import download_file
from .config import settings

def extract(msg):
    kind="text"; file_id=None; filename=None
    if msg.get("photo"): kind="photo"; file_id=msg["photo"][-1]["file_id"]
    elif msg.get("video"): kind="video"; file_id=msg["video"]["file_id"]
    elif msg.get("document"): kind="document"; file_id=msg["document"]["file_id"]; filename=msg["document"].get("file_name")
    elif msg.get("audio"): kind="audio"; file_id=msg["audio"]["file_id"]
    elif msg.get("voice"): kind="voice"; file_id=msg["voice"]["file_id"]
    elif msg.get("animation"): kind="animation"; file_id=msg["animation"]["file_id"]
    return kind,file_id,filename

async def ingest(post):
    if str(post.get("chat",{}).get("id")) != str(settings.telegram_source_chat_id): return "ignored"
    kind,file_id,filename=extract(post)
    db=SessionLocal()
    try:
        m=Message(source_chat_id=str(post["chat"]["id"]),source_message_id=post["message_id"],media_group_id=post.get("media_group_id"),kind=kind,payload_json=json.dumps(post,ensure_ascii=False))
        db.add(m); db.flush()
        for name in ADAPTERS: db.add(Delivery(message_id=m.id,destination=name))
        db.commit(); return m.id
    except IntegrityError:
        db.rollback(); return "duplicate"
    finally: db.close()

async def deliver(delivery_id):
    db=SessionLocal(); d=db.get(Delivery,delivery_id)
    if not d: db.close(); return
    m=db.get(Message,d.message_id); payload=json.loads(m.payload_json)
    d.status="PROCESSING"; d.attempts+=1; db.commit()
    try:
        _,file_id,filename=extract(payload)
        media=None
        if file_id: filename,media=await download_file(file_id)
        d.remote_message_id=await ADAPTERS[d.destination].send(payload,media,filename)
        d.status="SUCCESS"; d.last_error=None
    except Exception as e:
        d.status="FAILED"; d.last_error=str(e)[:4000]
    db.commit(); db.close()
