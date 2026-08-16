"""
Модуль представлений (Views) для управления пользователями приложения Users.

Обеспечивает логику обработки HTTP-запросов для просмотра и изменения
персональных данных пользователей системы.
"""

from django.contrib.auth.models import update_last_login
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.models import Payments, CustomUser
from users.serializers import (
    UserSerializer,
    PaymentSerializer,
    UserRegisterSerializer,
    UserPublicProfileSerializer,
)


class UserCreateAPIView(CreateAPIView):
    """
    API-представление для создания пользователя.
    """

    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    # Открываем доступ незарагистривованным пользователям
    permission_classes = [AllowAny]


class CurrentUserProfileAPIView(RetrieveUpdateDestroyAPIView):
    """
    API для работы с ЛИЧНЫМ профилем текущего пользователя.

    Поддерживает:
    - GET: Просмотр своих приватных данных.
    - PUT/PATCH: Безопасное редактирование своего профиля.
    - DELETE: Удаление собственного аккаунта.

    ID в URL не требуется, все операции идут строго через сессию/JWT токен.
    """
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        """Возвращает объект пользователя, выполняющего текущий запрос."""
        return self.request.user

    def perform_update(self, serializer):
        """Сохраняет данные и обновляет last_login пользователя."""
        super().perform_update(serializer)
        # Обновляем логин при каждом редактировании
        update_last_login(None, self.request.user)


class UserPublicRetrieveAPIView(RetrieveAPIView):
    """
    API для просмотра ПУБЛИЧНОГО профиля любого пользователя платформы по его ID.

    Возвращает только безопасные (открытые) данные пользователя.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserPublicProfileSerializer  # Всегда отдаем только публичный сериализатор
    permission_classes = (IsAuthenticated,)


class PaymentsListAPIView(ListAPIView):
    """
    API-представления для вывода списка платежей текущего пользователя.
    """

    serializer_class = PaymentSerializer

    # Подключаем бэкенд фильтрации
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    # Указываем поля, по которым можно фильтровать список
    filterset_fields = (
        "paid_course",
        "paid_lesson",
        "payment_method",
    )

    # Указываем, по каким полям разрешено сортировать
    ordering_fields = ["payment_date"]
    # Задаем сортировку по умолчанию, если параметр не передан в URL
    ordering = ["-payment_date"]

    def get_queryset(self):
        """Возвращает все платежи польщователя."""
        # ЗАЩИТА ДЛЯ SWAGGER: Если схему генерирует робот, возвращаем пустую выборку
        if getattr(self, "swagger_fake_view", False):
            return Payments.objects.none()

        # Оптимизирует запрос, подгружая данные пользователя за один SQL-запрос
        return Payments.objects.filter(user=self.request.user).select_related("user")
