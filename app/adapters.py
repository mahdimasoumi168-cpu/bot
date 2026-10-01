import httpx
from abc import ABC, abstractmethod
from .config import settings

class Adapter(ABC):
    name="base"
    @abstractmethod
    async def send(self,msg,media,filename): ...

class EitaaAdapter(Adapter):
    name="eitaa"
    async def send(self,msg,media,filename):
        if not settings.eitaa_token or not settings.eitaa_chat_id: raise RuntimeError("Eitaa is not configured")
        if media is None:
            url="https://eitaayar.ir/api/app/sendMessage"
            data={"token":settings.eitaa_token,"chat_id":settings.eitaa_chat_id,"text":msg.get("text") or msg.get("caption") or ""}
            files=None
        else:
            url="https://eitaayar.ir/api/app/sendFile"
            data={"token":settings.eitaa_token,"chat_id":settings.eitaa_chat_id,"caption":msg.get("caption") or ""}
            files={"file":(filename or "file.bin",media)}
        async with httpx.AsyncClient(timeout=settings.request_timeout) as c:
            r=await c.post(url,data=data,files=files)
        r.raise_for_status(); body=r.json()
        if body.get("ok") is False: raise RuntimeError(str(body))
        return str(body.get("result","ok"))

class BaleAdapter(Adapter):
    name="bale"
    async def send(self,msg,media,filename):
        if not settings.bale_token or not settings.bale_chat_id: raise RuntimeError("Bale is not configured")
        method="sendMessage" if media is None else "sendDocument"
        url="https://tapi.bale.ai/bot"+settings.bale_token+"/"+method
        async with httpx.AsyncClient(timeout=settings.request_timeout) as c:
            if media is None:
                r=await c.post(url,json={"chat_id":settings.bale_chat_id,"text":msg.get("text") or msg.get("caption") or ""})
            else:
                r=await c.post(url,data={"chat_id":settings.bale_chat_id,"caption":msg.get("caption") or ""},files={"document":(filename or "file.bin",media)})
        r.raise_for_status(); body=r.json()
        if body.get("ok") is False: raise RuntimeError(str(body))
        return str(body.get("result",{}).get("message_id","ok"))

class GenericAdapter(Adapter):
    def __init__(self,name,endpoint,token,chat_id):
        self.name,self.endpoint,self.token,self.chat_id=name,endpoint,token,chat_id
    async def send(self,msg,media,filename):
        if not self.endpoint or not self.token or not self.chat_id: raise RuntimeError(self.name+" is not configured")
        data={"token":self.token,"chat_id":self.chat_id,"text":msg.get("text") or "","caption":msg.get("caption") or ""}
        async with httpx.AsyncClient(timeout=settings.request_timeout) as c:
            if media: r=await c.post(self.endpoint,data=data,files={"file":(filename or "file.bin",media)})
            else: r=await c.post(self.endpoint,json=data)
        r.raise_for_status()
        return str(r.json().get("result","ok"))

ADAPTERS={
 "eitaa":EitaaAdapter(),
 "bale":BaleAdapter(),
 "rubika":GenericAdapter("rubika",settings.rubika_endpoint,settings.rubika_token,settings.rubika_chat_id),
 "soroush":GenericAdapter("soroush",settings.soroush_endpoint,settings.soroush_token,settings.soroush_chat_id),
}
