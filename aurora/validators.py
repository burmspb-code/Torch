"""Валидаторы приложения aurora."""

from urllib.parse import urlparse
from rest_framework.serializers import ValidationError

ALLOWED_DOMAIN = {"youtube.com", "www.youtube.com", "youtu.be"}


def validator_allowed_words(value):
    """Проверка на разрешенные слова."""
    # Если ссылка пустое значение, пропускаем проверку
    if not value:
        return

    try:
        parse_url = urlparse(str(value).strip()) # Парсим ссылку

        host_name = parse_url.hostname # Получаем домен

        if not host_name:
            raise ValidationError("Передана не корректная ссылка")

        if host_name.lower() not in ALLOWED_DOMAIN:
            raise ValidationError("Ссылка может быть только на ресурс youtube.com")

    except ValueError:
        raise ValidationError("Не удалось распознать формат ссылки")
