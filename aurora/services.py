"""Бизнес-логика управления процессами для приложения Aurora."""

import logging
from datetime import timedelta

from django.utils import timezone

from aurora.models import Course, Subscribe


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


def process_course_updates_cron() -> None:
    """Сканирует базу данных и отправляет рассылку по всем курсам,

    которые были изменены более 4 часов назад.
    """
    # Задаем временную точку (на 4 часа назад от текущего момента)
    four_hours_ago = timezone.now() - timedelta(hours=4)

    # Выбираем курсы, измененные > 4 часов назад, по которым еще не было рассылки
    courses_to_notify = Course.objects.filter(
        updated_at__lte=four_hours_ago,
        notification_sent=False
    )

    if not courses_to_notify.exists():
        logger.info("Нет курсов для отправки уведомлений.")
        return

    # Обрабатываем каждый курс
    from aurora.tasks import send_course_subscription_email

    for course in courses_to_notify:
        # Получаем активные подписки на этот курс с предзагрузкой пользователей
        subscribes = Subscribe.objects.filter(
            course_id=course.id,
            is_archived=False
        ).select_related("user")

        # Если подписчиков нет, просто закрываем отправку для этого курса
        if not subscribes.exists():
            course.notification_sent = True
            course.save(update_fields=['notification_sent'])
            continue

        # Запускаем рассылку веером через Celery .delay()
        for subscribe in subscribes:
            user_email = subscribe.user.email
            if user_email:
                # Вызываем вашу протестированную задачу
                send_course_subscription_email.delay(user_email, course.title)

        # Защищаем пользователей от спама: ставим флаг успешной отправки.
        # Метод save(update_fields=...) обновит ТОЛЬКО флаг и НЕ изменит updated_at.
        course.notification_sent = True
        course.save(update_fields=['notification_sent'])

        logger.info(f"Запущена рассылка для курса «{course.title}» ({subscribes.count()} писем).")
