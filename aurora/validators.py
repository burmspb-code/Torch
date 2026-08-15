"""Валидаторы приложения aurora."""

from rest_framework.serializers import ValidationError

ALLOWED_WORDS = "youtube.com"


def validator_allowed_words(value):
    """Проверка на разрешенные слова."""
    # Если ссылка пустое значение, пропускаем проверку
    if not value:
        return

    if value not in ALLOWED_WORDS.lower():
        raise ValidationError("Ссылка может быть только на ресурс youtube.com")
