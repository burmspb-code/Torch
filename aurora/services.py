"""Бизнес-логика управления процессами для приложения Aurora."""

import logging
from aurora.models import Subscribe, Course

from aurora.tasks import send_course_subscription_email

logger = logging.getLogger(__name__)

def process_course_update(course_id: int) -> None:
    """Вызываем задачу для рассылки информации пользователям, которые подписаны на курс.

    Args:
         course_id (int): ID курса
    """
    # Получаем активные подписки
    subscribes = Subscribe.objects.filter(course=course_id, is_archived=False).select_related("user")
    # Получаем наименование курса
    try:
        course_title = Course.objects.values_list("title", flat=True).get(id=course_id)  # Получаем наименование курса
    except Course.DoesNotExist:
        logger.warning(f"Попытка обновить несуществующий курс с ID {course_id}")
        return

    # Проверяем, что подписки существуют
    if not subscribes:
        return

    # Вызываем рассылку в цикле
    for subscribe in subscribes:
        user_email = subscribe.user.email # Получаем почту пользователя для рассылки
        send_course_subscription_email.delay(user_email, course_title) # Вызываем задачу для рассылки
