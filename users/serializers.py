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
        read_only_fields = ("id", "user", "payment_date", "paid_course", "paid_lesson", "payment_amount", "payment_method")


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра и редактирования профиля пользователя."""

    # Вложенный сериализатор для истории платежей
    payments_information = PaymentSerializer(source="payments", many=True, read_only=True)

    class Meta:
        """Класс метаданных."""
        model = CustomUser
        fields = ("id", "email", "phone_number", "city", "avatar", "payments_information")
        read_only_fields = ("email", "payments_information")
