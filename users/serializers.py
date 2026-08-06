"""
Модуль сериализаторов для приложения управления пользователями (Users).

Содержит классы для валидации и преобразования данных пользователей
при взаимодействии через API.
"""

from rest_framework import serializers

from users.models import CustomUser, Payments


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализотор для вывода списка платежей (только для чтения)."""

    class Meta:
        """Класс метаданных."""

        model = Payments
        fields = "__all__"
        read_only_fields = (
            "id",
            "user",
            "payment_date",
            "paid_course",
            "paid_lesson",
            "payment_amount",
            "payment_method",
        )


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра и редактирования профиля пользователя."""

    # Вложенный сериализатор для истории платежей
    payments_information = PaymentSerializer(
        source="payments", many=True, read_only=True
    )

    class Meta:
        """Класс метаданных."""

        model = CustomUser
        fields = (
            "id",
            "email",
            "phone_number",
            "city",
            "avatar",
            "payments_information",
        )
        read_only_fields = ("email", "payments_information")


class UserRegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового пльзователя."""

    # Защита от пустых паролей
    password = serializers.CharField(
        write_only=True,  # Скрваем пароль в ответах
        required=True,  # Поле обязательно
        allow_blank=False,  # Поле не может быть пустым
    )

    # ОБЯЗАТЕЛЬНО ДОБАВЛЯЕМ ЭТОТ МЕТОД:
    def create(self, validated_data):
        """Используем кастомный менеджер для безопасного хэширования пароля."""
        # Метод create_user автоматически захеширует пароль перед сохранением
        return CustomUser.objects.create_user(**validated_data)

    class Meta:
        """Класс метаданных."""

        model = CustomUser
        # ЯВНО перечисляем только безопасные поля:
        fields = ("email", "password", "phone_number", "city", "avatar")


class UserPublicProfileSerializer(serializers.ModelSerializer):
    """Публичный профиль (для чужих): видны только базовые поля."""

    class Meta:
        """Класс метаданных."""

        model = CustomUser
        fields = (
            "id",
            "email",
            "city",
            "avatar",
        )  # Только разрешенные поля
