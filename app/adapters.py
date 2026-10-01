import httpx
from abc import ABC, abstractmethod
from .config import settings

class Adapter(ABC):
    name="base"
    @abstractmethod
    async def send(self,msg,media,filename): ...

def caption(msg): return msg.get("caption") or msg.get("text") or ""

class EitaaAdapter(Adapter):
    name="eitaa"
    async def send(self,msg,media,filename):
        if not settings.eitaa_token or not settings.eitaa_chat_id: raise RuntimeError("Eitaa is not configured")
        async with httpx.AsyncClient(timeout=settings.request_timeout) as c:
            if media is None:
                r=await c.post("https://eitaayar.ir/api/app/sendMessage",data={"token":settings.eitaa_token,"chat_id":settings.eitaa_chat_id,"text":caption(msg)})
            else:
                r=await c.post("https://eitaayar.ir/api/app/sendFile",data={"token":settings.eitaa_token,"chat_id":settings.eitaa_chat_id,"caption":msg.get("caption") or ""},files={"file":(filename or "file.bin",media)})
        r.raise_for_status(); body=r.json()
        if body.get("ok") is False: raise RuntimeError(str(body))
        return str(body.get("result","ok"))

class BaleAdapter(Adapter):
    name="bale"
    async def send(self,msg,media,filename):
        if not settings.bale_token or not settings.bale_chat_id: raise RuntimeError("Bale is not configured")
        kind=msg.get("_crossposter_kind","document")
        methods={"photo":"sendPhoto","video":"sendVideo","audio":"sendAudio","voice":"sendVoice","animation":"sendAnimation","document":"sendDocument"}
        method="sendMessage" if media is None else methods.get(kind,"sendDocument")
        url=f"https://tapi.bale.ai/bot{settings.bale_token}/{method}"
        async with httpx.AsyncClient(timeout=settings.request_timeout) as c:
            if media is None: r=await c.post(url,json={"chat_id":settings.bale_chat_id,"text":caption(msg)})
            else:
                field={"photo":"photo","video":"video","audio":"audio","voice":"voice","animation":"animation","document":"document"}.get(kind,"document")
                r=await c.post(url,data={"chat_id":settings.bale_chat_id,"caption":msg.get("caption") or ""},files={field:(filename or "file.bin",media)})
        r.raise_for_status(); body=r.json()
        if body.get("ok") is False: raise RuntimeError(str(body))
        return str(body.get("result",{}).get("message_id","ok"))

class RubikaAdapter(Adapter):
    name="rubika"
    async def api(self,method,payload):
        if not settings.rubika_token or not settings.rubika_chat_id: raise RuntimeError("Rubika is not configured")
        url=f"https://botapi.rubika.ir/v3/{settings.rubika_token}/{method}"
        async with httpx.AsyncClient(timeout=settings.request_timeout) as c:
            r=await c.post(url,json=payload); r.raise_for_status(); body=r.json()
        if isinstance(body,dict) and body.get("status") not in (None,"OK","ok"): raise RuntimeError(str(body))
        return body
    async def send(self,msg,media,filename):
        if media is None:
            body=await self.api("sendMessage",{"chat_id":settings.rubika_chat_id,"text":caption(msg)})
            return str(body.get("data",{}).get("message_id") or body.get("message_id") or "ok")
        kind=msg.get("_crossposter_kind","document")
        media_type={"photo":"Image","video":"Video","audio":"File","voice":"Voice","animation":"Gif","document":"File"}.get(kind,"File")
        req=await self.api("requestSendFile",{"type":media_type})
        upload_url=req.get("data",{}).get("upload_url") or req.get("upload_url")
        if not upload_url: raise RuntimeError("Rubika upload URL was not returned")
        async with httpx.AsyncClient(timeout=settings.request_timeout) as c:
            up=await c.post(upload_url,files={"file":(filename or "file.bin",media)}); up.raise_for_status(); ub=up.json()
        file_id=ub.get("data",{}).get("file_id") or ub.get("file_id")
        if not file_id: raise RuntimeError("Rubika file_id was not returned")
        body=await self.api("sendFile",{"chat_id":settings.rubika_chat_id,"file_id":file_id,"text":msg.get("caption") or ""})
        return str(body.get("data",{}).get("message_id") or body.get("message_id") or "ok")

class GenericAdapter(Adapter):
    def __init__(self,name,endpoint,token,chat_id): self.name,self.endpoint,self.token,self.chat_id=name,endpoint,token,chat_id
    async def send(self,msg,media,filename):
        if not self.endpoint or not self.token or not self.chat_id: raise RuntimeError(f"{self.name} is not configured")
        data={"token":self.token,"chat_id":self.chat_id,"text":msg.get("text") or "","caption":msg.get("caption") or ""}
        async with httpx.AsyncClient(timeout=settings.request_timeout) as c:
            r=await c.post(self.endpoint,data=data,files={"file":(filename or "file.bin",media)} if media else None)
        r.raise_for_status(); body=r.json()
        if isinstance(body,dict) and body.get("ok") is False: raise RuntimeError(str(body))
        return str(body.get("result","ok")) if isinstance(body,dict) else "ok"

ADAPTERS={"eitaa":EitaaAdapter(),"bale":BaleAdapter(),"rubika":RubikaAdapter(),"soroush":GenericAdapter("soroush",settings.soroush_endpoint,settings.soroush_token,settings.soroush_chat_id)}
