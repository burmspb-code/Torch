"""
Модуль сериализаторов для приложения управления пользователями (Users).

Содержит классы для валидации и преобразования данных пользователей
при взаимодействии через API.
"""

from rest_framework import serializers

from users.models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для просмотра и редактирования профиля пользователя.
    """

    class Meta:
        """Класс метаданных."""

        model = CustomUser
        fields = ("email", "phone_number", "city", "avatar")
        read_only_fields = ("email",)

    def __init__(self, *args, **kwargs):
        """
        Динамически настраиваем валидаторы уникальности для корректной
        работы при частичном обновлении (PATCH) профиля.
        """
        super().__init__(*args, **kwargs)

        # Если мы обновляем существующего пользователя (есть instance)
        if self.instance and "phone_number" in self.fields:
            # Связываем валидатор уникальности с текущим объектом,
            # чтобы он игнорировал номер самого этого пользователя
            for validator in self.fields["phone_number"].validators:
                if hasattr(validator, "set_context"):
                    validator.set_context(self)
