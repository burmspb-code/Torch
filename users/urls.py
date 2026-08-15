"""
Конфигурация URL-маршрутов для приложения Users.

Определяет эндпоинты для управления профилями пользователей, включая
безопасное обновление персональных данных без передачи ID в URL.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.apps import UsersConfig
from users.views import (
    UserProfileAPIView,
    PaymentsListAPIView,
    UserCreateAPIView,
    UserDeleteAPIView,
    UserRetrieveAPIView,
)

app_name = UsersConfig.name

urlpatterns = [
    # Маршрут для регистрации пользователя
    path("register/", UserCreateAPIView.as_view(), name="register"),
    # Маршрут для просмотра и редактирования профиля текущего пользователя
    path("profile/", UserProfileAPIView.as_view(), name="user_profile"),
    # Маршрут для просмотра профиля любого пользователя
    path("profile/<int:pk>/", UserRetrieveAPIView.as_view(), name="user_profile_pk"),
    # Маршрут для вывода списка платежей текущего пользователя
    path("payments/", PaymentsListAPIView.as_view(), name="payments"),
    # ЛОГИН: Получение токена (передаем email и password)
    # TokenObtainPairView и TokenRefreshView) уже имеют настройку AllowAny внутри себя из коробки
    path("login/", TokenObtainPairView.as_view(), name="login"),
    # ОБНОВЛЕНИЕ: Получение нового access-токена через refresh-токен
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Маршрут для удаления пользователя
    path("delete/", UserDeleteAPIView.as_view(), name="user_delete"),
]
