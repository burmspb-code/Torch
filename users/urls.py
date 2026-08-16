"""
Конфигурация URL-маршрутов для приложения Users.

Определяет эндпоинты для управления профилями пользователей, включая
безопасное обновление персональных данных без передачи ID в URL.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.apps import UsersConfig
from users.views import (
    PaymentsListAPIView,
    UserCreateAPIView,
    CurrentUserProfileAPIView,
    UserPublicRetrieveAPIView,
)

app_name = UsersConfig.name

urlpatterns = [
    # Маршрут для регистрации пользователя
    path("register/", UserCreateAPIView.as_view(), name="register"),
    # Маршрут для просмотра, редактирования и удаления профиля текущего пользователя
    path("profile/", CurrentUserProfileAPIView.as_view(), name="my_profile"),
    # Маршрут для просмотра чужого публичного профиля пользователя
    path("profiles/<int:pk>/", UserPublicRetrieveAPIView.as_view(), name="user_public_detail"),
    # Маршрут для вывода списка платежей текущего пользователя
    path("payments/", PaymentsListAPIView.as_view(), name="payments"),
    # ЛОГИН: Получение токена (передаем email и password)
    # TokenObtainPairView и TokenRefreshView) уже имеют настройку AllowAny внутри себя из коробки
    path("login/", TokenObtainPairView.as_view(), name="login"),
    # ОБНОВЛЕНИЕ: Получение нового access-токена через refresh-токен
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
