from celery import Celery
from app.config import settings

celery_app = Celery(
    "green_taxo",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.document_analysis']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Paris',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max par tâche
    task_soft_time_limit=25 * 60,  # avertissement après 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)