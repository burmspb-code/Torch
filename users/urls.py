"""
Конфигурация URL-маршрутов для приложения Users.

Определяет эндпоинты для управления профилями пользователей, включая
безопасное обновление персональных данных без передачи ID в URL.
"""

from django.urls import path

from users.apps import UsersConfig
from users.views import (
    PaymentsListAPIView,
    UserCreateAPIView,
    CurrentUserProfileAPIView,
    UserPublicRetrieveAPIView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    PaymentCreateAPIView,
    PaymentStatusCheckAPIView,
    StripeWebhookView,
)

app_name = UsersConfig.name

urlpatterns = [
    # Маршрут для регистрации пользователя
    path("register/", UserCreateAPIView.as_view(), name="register"),
    # Маршрут для просмотра, редактирования и удаления профиля текущего пользователя
    path("profile/", CurrentUserProfileAPIView.as_view(), name="my_profile"),
    # Маршрут для просмотра чужого публичного профиля пользователя
    path(
        "profiles/<int:pk>/",
        UserPublicRetrieveAPIView.as_view(),
        name="user_public_detail",
    ),
    # ЛОГИН: Получение токена (передаем email и password)
    # TokenObtainPairView и TokenRefreshView) уже имеют настройку AllowAny внутри себя из коробки
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    # ОБНОВЛЕНИЕ: Получение нового access-токена через refresh-токен
    path("token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh"),
    # Маршрут для вывода списка платежей текущего пользователя
    path("payments/", PaymentsListAPIView.as_view(), name="payments"),
    # Эндпоинт для создания платежа и получения ссылки (вызывается фронтендом/Postman)
    path(
        "payments/create-link/",
        PaymentCreateAPIView.as_view(),
        name="create_payment_link",
    ),
    # Эндпоинт для приема сигналов от Stripe (сюда мы направляли Stripe CLI командой listen)
    path("payments/webhook/", StripeWebhookView.as_view(), name="stripe_webhook"),
    # Маршрут для проверки статуса платежа
    path(
        "payments/<int:pk>/check-status/",
        PaymentStatusCheckAPIView.as_view(),
        name="check_payment_status",
    ),
]
