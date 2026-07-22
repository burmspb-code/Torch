"""
Модуль сериализаторов для приложения управления пользователями (Users).

Содержит классы для валидации и преобразования данных пользователей
при взаимодействии через API.
"""

from rest_framework.serializers import ModelSerializer

from users.models import CustomUser


class UserSerializer(ModelSerializer):
    """
        Сериализатор для просмотра и редактирования профиля пользователя.

        Ограничивает доступ к системным полям модели CustomUser, позволяя
        безопасно изменять только личные данные авторизованного пользователя.
    """
    class Meta:
        """Класс метаданных."""
        model = CustomUser
        fields = (
            'email',
            'phone_number',
            'city',
            'avatar'
        )
        read_only_fields = ("email",)
