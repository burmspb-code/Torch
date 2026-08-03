"""
Конфигурация URL-маршрутов для приложения Users.

Определяет эндпоинты для управления профилями пользователей, включая
безопасное обновление персональных данных без передачи ID в URL.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.apps import UsersConfig
from users.views import UserProfileAPIView, PaymentsListAPIView

app_name = UsersConfig.name

urlpatterns = [
    # Маршрут для просмотра и редактирования профиля текущего пользователя
    path("profile/", UserProfileAPIView.as_view(), name="user_profile"),
    # Маршрут для вывода списка платежей текущего пользователя
    path("payments/", PaymentsListAPIView.as_view(), name="payments"),
    # Маршруты для работы с токенами
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
