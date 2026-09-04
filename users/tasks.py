from celery import shared_task
from .services import UserActivityService


@shared_task(queue="default")
def block_inactive_users_beat_task():
    """Фоновая задача для ежесуточной блокировки неактивных пользователей."""
    service = UserActivityService(inactivity_days=30)
    service.enable_blocking()
