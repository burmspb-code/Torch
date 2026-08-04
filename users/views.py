"""
Модуль представлений (Views) для управления пользователями приложения Users.

Обеспечивает логику обработки HTTP-запросов для просмотра и изменения
персональных данных пользователей системы.
"""

from django.contrib.auth.models import update_last_login
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, CreateAPIView, DestroyAPIView
from rest_framework.permissions import AllowAny

from users.models import Payments, CustomUser
from users.serializers import UserSerializer, PaymentSerializer, UserRegisterSerializer


class UserCreateAPIView(CreateAPIView):
    """
    API-представление для создания пользователя.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    # Открываем доступ незарагистривованным пользователям
    permission_classes = [AllowAny]


class UserProfileAPIView(RetrieveUpdateAPIView):
    """
    API-представление для просмотра и безопасного редактирования профиля текущего пользователя.
    """

    serializer_class = UserSerializer

    def get_object(self):
        """Возвращает объект пользователя, выполняющего текущий запрос."""
        return self.request.user

    # Переопределяем метод успешного выполнения PATCH/PUT запроса:
    def perform_update(self, serializer):
        """Сохраняет данные и принудительно обновляет last_login пользователя."""
        super().perform_update(serializer)
        # Вызываем встроенную функцию Django для обновления таймстампа
        update_last_login(None, self.request.user)


class UserDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления текущего пользователя.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer

    def get_object(self):
        """Возвращает объект текущего пользователя для удаления."""
        # Благодаря этому, юзер удалит именно себя, а не кого-то другого по ID
        return self.request.user


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
        # Оптимизирует запрос, подгружая данные пользователя за один SQL-запрос
        return Payments.objects.filter(user=self.request.user).select_related("user")
