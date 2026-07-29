"""
Модуль представлений (Views) для управления пользователями приложения Users.

Обеспечивает логику обработки HTTP-запросов для просмотра и изменения
персональных данных пользователей системы.
"""

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import update_last_login

from users.serializers import UserSerializer


class UserProfileAPIView(RetrieveUpdateAPIView):
    """
    API-представление для просмотра и безопасного редактирования профиля текущего пользователя.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Возвращает объект пользователя, выполняющего текущий запрос."""
        return self.request.user

    # Переопределяем метод успешного выполнения PATCH/PUT запроса:
    def perform_update(self, serializer):
        """Сохраняет данные и принудительно обновляет last_login пользователя."""
        super().perform_update(serializer)
        # Вызываем встроенную функцию Django для обновления таймстампа
        update_last_login(None, self.request.user)
