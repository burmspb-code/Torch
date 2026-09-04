import logging
from typing import Optional
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from aurora.services import process_course_updates_cron

# Настройка логгера для отслеживания фоновых задач
logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="emails",
)
def send_subscription_email(
    self, email: str, certain_data_name: Optional[str] = None
) -> bool:
    """Отправляет уведомление пользователю об успешном оформлении подписки.

    Args:
        self (Task): объект задачи
        email (str): Адрес электронной почты получателя.
        certain_data_name (Optional[str]): Наименование оплаченного продукта.
            Если не указано, используется значение по умолчанию.

    Returns:
        bool: True, если письмо успешно отправлено.

    Raises:
        self.retry: Если отправка почты завершилась сетевой ошибкой
            (задача перезапустится автоматически).
    """
    data_name = certain_data_name or "на сервис"

    try:
        send_mail(
            subject="Уведомление о подписке",
            message=(
                f"Подписка «{data_name}» оформлена успешно. "
                "Спасибо за выбор нашего сервиса!"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Email successfully sent to {email}")
        return True

    except Exception as exc:
        logger.error(f"Failed to send email to {email}: {exc}")
        # Автоматический перезапуск задачи при сбое почтового сервера
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="emails",
)
def send_course_subscription_email(self, email: str, course_title: str) -> bool:
    """Отправляет уведомление пользователю об обновлении курса, на который он подписан.

    Args:
        self (Task): Объект задачи Celery.
        email (str): Адрес электронной почты получателя.
        course_title (str): Наименование обновленного курса.

    Returns:
        bool: True, если письмо успешно отправлено.

    Raises:
        self.retry: Если отправка почты завершилась сетевой ошибкой
            (задача перезапустится автоматически).
    """
    try:
        send_mail(
            subject="Уведомление об обновлении курса",
            message=(
                f"Курс «{course_title}» обновился. "
                "Для ознакомления перейдите к материалам курса."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info(f"Email successfully sent to {email}")
        return True

    except Exception as exc:
        logger.error(f"Failed to send email to {email}: {exc}")
        # Автоматический перезапуск задачи при сбое почтового сервера
        raise self.retry(exc=exc)


@shared_task(queue="default")
def check_course_updates_beat_task():
    """Периодическая задача Celery Beat, которая дергает сервисный слой."""
    process_course_updates_cron()
