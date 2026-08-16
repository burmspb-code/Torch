"""
Модуль представлений (Views) для управления пользователями приложения Users.

Обеспечивает логику обработки HTTP-запросов для просмотра и изменения
персональных данных пользователей системы.
"""

from django.contrib.auth.models import update_last_login
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from rest_framework.filters import OrderingFilter
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.models import Payments, CustomUser
from users.serializers import (
    UserSerializer,
    PaymentSerializer,
    UserRegisterSerializer,
    UserPublicProfileSerializer,
)


@extend_schema(
    summary="Регистрация нового пользователя",
    description=(
            "Создает новый аккаунт пользователя в системе. "
            "Доступ разрешен незарегистрированным пользователям без авторизации."
    ),
    responses={
        201: OpenApiResponse(
            response=UserRegisterSerializer,
            description="Пользователь успешно зарегистрирован."
        ),
        400: OpenApiResponse(
            description="Ошибка валидации данных (например, этот email уже зарегистрирован или слабый пароль)."
        )
    },
    tags=["Пользователи"]  # Объединяем в одну группу с просмотром чужих профилей
)
class UserCreateAPIView(CreateAPIView):
    """
    API-представление для создания пользователя.
    """

    queryset = CustomUser.objects.all()
    serializer_class = UserRegisterSerializer
    # Открываем доступ незарагистривованным пользователям
    permission_classes = [AllowAny]


@extend_schema_view(
    get=extend_schema(
        summary="Получить информацию о пользователе",
        description="Доступно зарегистрированному пользователю для просмотра своей приватной информации."
    ),
    put=extend_schema(
        summary="Полное обновление информации о пользователе",
        description="Доступно зарегистрированному пользователю для изменения своей приватной информации."
    ),
    patch=extend_schema(
        summary="Частичное обновление информации о пользователе",
        description="Доступно зарегистрированному пользователю для изменения своей приватной информации."
    ),
    delete=extend_schema(
        summary="Удаление профиля пользователя",
        responses={204: None},
        description="Удаление текущего профиля пользователя. Доступно зарегистрированному пользователю."
    )
)
@extend_schema(
    responses={
        200: OpenApiResponse(response=UserSerializer, description="Информация о пользователе успешно получена."),
        401: OpenApiResponse(description="Неавторизованный доступ (отсутствует или неверен токен).")
    },
    tags=["Пользователи"]  # Группирует эндпоинты в интерфейсе Redoc в одну вкладку
)
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


@extend_schema(
    summary="Просмотр публичной информации о пользователе.",
    description=(
            "Просматривать информацию могут только авторизованные пользователи."
    ),
    responses={
        200: OpenApiResponse(
            response=UserPublicProfileSerializer,
            description="Публичные данные пользователя успешно получены."
        ),
        401: OpenApiResponse(description="Неавторизованный доступ (отсутствует или неверен токен)."),
        404: OpenApiResponse(description="Пользователь с указанным ID не найден.")
    },
    tags=["Пользователи"]
)
class UserPublicRetrieveAPIView(RetrieveAPIView):
    """
    API для просмотра ПУБЛИЧНОГО профиля любого пользователя платформы по его ID.

    Возвращает только безопасные (открытые) данные пользователя.
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserPublicProfileSerializer  # Всегда отдаем только публичный сериализатор
    permission_classes = (IsAuthenticated,)


@extend_schema(
    summary="История платежей текущего пользователя",
    description=(
            "Возвращает список всех транзакций и оплат, совершенных текущим авторизованным пользователем. "
            "Доступна фильтрация по курсу, уроку и методу оплаты, а также сортировка по дате платежа."
    ),
    responses={
        200: OpenApiResponse(
            response=PaymentSerializer(many=True),
            description="Список платежей успешно получен."
        ),
        401: OpenApiResponse(
            description="Неавторизованный доступ (отсутствует или неверен JWT-токен)."
        )
    },
    tags=["Профиль"]  # Размещаем платежи в блоке личного профиля, рядом с CurrentUserProfileAPIView
)
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


@extend_schema(
    summary="Авторизация пользователя (Получение JWT-токена)",
    description=(
            "Принимает учетные данные пользователя (email и password). "
            "В случае успешной проверки возвращает пару токенов: access (короткоживущий) и refresh (долгоживущий)."
    ),
    responses={
        200: OpenApiResponse(
            description="Успешная аутентификация. Токены успешно сгенерированы."
        ),
        401: OpenApiResponse(
            description="Ошибка авторизации. Неверный email или пароль, либо аккаунт деактивирован."
        ),
    },
    tags=["Авторизация"],
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """Кастомный эндпоинт авторизации для поддержки автодокументации в Redoc."""

    # Simple JWT автоматически подтянет TokenObtainPairSerializer,
    # и drf-spectacular отобразит поля email и password на фронтенде.
    pass


@extend_schema(
    summary="Обновление access-токена",
    description=(
            "Принимает действующий refresh-токен. "
            "Возвращает новый валидный access-токен для продолжения работы с защищенными эндпоинтами API."
    ),
    responses={
        200: OpenApiResponse(
            description="Токен успешно обновлен. Возвращен новый access-токен."
        ),
        401: OpenApiResponse(
            description="Ошибка обновления. Переданный refresh-токен невалиден, изменен или истек."
        ),
    },
    tags=["Авторизация"],
)
class CustomTokenRefreshView(TokenRefreshView):
    """Кастомный эндпоинт обновления токена для поддержки автодокументации в Redoc."""

    # Робот автоматически подтянет TokenRefreshSerializer и отобразит поле refresh.
    pass
