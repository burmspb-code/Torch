"""
Конфигурация URL-маршрутов для приложения Users.

Определяет эндпоинты для управления профилями пользователей, включая
безопасное обновление персональных данных без передачи ID в URL.
"""

from django.urls import path

from users.apps import UsersConfig
from users.views import CustomUserUpdateAPIView

app_name = UsersConfig.name

urlpatterns = [
    path("update/", CustomUserUpdateAPIView.as_view(), name="user_update"),
]
