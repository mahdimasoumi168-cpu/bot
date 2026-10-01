import secrets
from fastapi import FastAPI,Request,HTTPException,Depends
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic,HTTPBasicCredentials
from .config import settings
from .db import init_db,SessionLocal
from .models import Delivery
from .processor import ingest
from .tasks import deliver_task
from .telegram import set_webhook

app=FastAPI(title=settings.app_name)
security=HTTPBasic()

@app.on_event("startup")
def startup():
    try: init_db()
    except Exception: pass

@app.get("/health")
def health(): return {"ok":True,"service":settings.app_name,"database":settings.database_url.split(":")[0]}

@app.post("/webhook/telegram")
async def telegram_webhook(request:Request):
    if settings.telegram_webhook_secret=="CONFIGURE_ME":
        raise HTTPException(503,"Telegram webhook is not configured")
    if not secrets.compare_digest(request.headers.get("X-Telegram-Bot-Api-Secret-Token",""),settings.telegram_webhook_secret):
        raise HTTPException(401,"invalid webhook secret")
    update=await request.json()
    post=update.get("channel_post") or update.get("edited_channel_post")
    if not post: return {"ok":True,"ignored":True}
    mid=await ingest(post)
    if isinstance(mid,int):
        db=SessionLocal()
        ids=[x.id for x in db.query(Delivery).filter(Delivery.message_id==mid).all()]
        db.close()
        for i in ids: deliver_task.delay(i)
    return {"ok":True,"result":mid}

def auth(c:HTTPBasicCredentials=Depends(security)):
    if not (secrets.compare_digest(c.username,settings.admin_username) and secrets.compare_digest(c.password,settings.admin_password)):
        raise HTTPException(401,"invalid credentials",headers={"WWW-Authenticate":"Basic"})
    return c.username

@app.get("/admin",response_class=HTMLResponse)
def admin(_:str=Depends(auth)):
    db=SessionLocal()
    rows=db.query(Delivery).order_by(Delivery.id.desc()).limit(100).all()
    out=["<html><meta charset='utf-8'><title>Cross Poster</title><body dir='rtl'><h2>پنل مدیریت انتقال پیام</h2><table border='1' cellpadding='6'><tr><th>ID</th><th>مقصد</th><th>وضعیت</th><th>تلاش</th><th>خطا</th></tr>"]
    for r in rows: out.append(f"<tr><td>{r.id}</td><td>{r.destination}</td><td>{r.status}</td><td>{r.attempts}</td><td>{r.last_error or ''}</td></tr>")
    out.append("</table></body></html>"); db.close(); return "".join(out)

@app.post("/admin/retry/{delivery_id}")
def retry(delivery_id:int,_:str=Depends(auth)):
    deliver_task.delay(delivery_id); return {"ok":True,"queued":delivery_id}

@app.post("/admin/set-webhook")
async def webhook(_:str=Depends(auth)): return await set_webhook()
