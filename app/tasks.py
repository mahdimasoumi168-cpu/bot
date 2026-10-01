from celery import Celery
from .config import settings
celery=Celery("crossposter",broker=settings.redis_url,backend=settings.redis_url)
celery.conf.update(task_serializer="json",accept_content=["json"],result_serializer="json",timezone="UTC",task_acks_late=True,worker_prefetch_multiplier=1)

@celery.task(bind=True,max_retries=5)
def deliver_task(self,delivery_id):
    import asyncio
    try:
        from .processor import deliver
        asyncio.run(deliver(delivery_id))
    except Exception as exc:
        raise self.retry(exc=exc,countdown=min(600,10*(2**self.request.retries)))
