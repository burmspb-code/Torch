"""
Модуль представлений (Views) для управления пользователями приложения Users.

Обеспечивает логику обработки HTTP-запросов для просмотра и изменения
персональных данных пользователей системы.
"""
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from users.serializers import UserSerializer


class CustomUserUpdateAPIView(UpdateAPIView):
    """
    API-представление для безопасного редактирования профиля текущего пользователя.

    Доступно только авторизованным пользователям. Автоматически определяет
    целевого пользователя по его токену/сессии, не требуя передачи ID в URL.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """Возвращает объект пользователя, выполняющего текущий запрос."""
        return self.request.user
