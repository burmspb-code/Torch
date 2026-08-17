"""
Модуль представлений (Views) для управления пользователями приложения Users.

Обеспечивает логику обработки HTTP-запросов для просмотра и изменения
персональных данных пользователей системы.
"""

from django.contrib.auth.models import update_last_login
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiExample,
)
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.models import Payments, CustomUser
from users.serializers import (
    UserSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    UserRegisterSerializer,
    UserPublicProfileSerializer,
)
from .services import StripePaymentService

# Создаем один экземпляр сервиса для работы
stripe_service = StripePaymentService()


@extend_schema(
    summary="Регистрация нового пользователя",
    description=(
        "Создает новый аккаунт пользователя в системе. "
        "Доступ разрешен незарегистрированным пользователям без авторизации."
    ),
    responses={
        201: OpenApiResponse(
            response=UserRegisterSerializer,
            description="Пользователь успешно зарегистрирован.",
        ),
        400: OpenApiResponse(
            description="Ошибка валидации данных (например, этот email уже зарегистрирован или слабый пароль)."
        ),
    },
    tags=["Пользователи"],  # Объединяем в одну группу с просмотром чужих профилей
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
        description="Доступно зарегистрированному пользователю для просмотра своей приватной информации.",
    ),
    put=extend_schema(
        summary="Полное обновление информации о пользователе",
        description="Доступно зарегистрированному пользователю для изменения своей приватной информации.",
    ),
    patch=extend_schema(
        summary="Частичное обновление информации о пользователе",
        description="Доступно зарегистрированному пользователю для изменения своей приватной информации.",
    ),
    delete=extend_schema(
        summary="Удаление профиля пользователя",
        responses={204: None},
        description="Удаление текущего профиля пользователя. Доступно зарегистрированному пользователю.",
    ),
)
@extend_schema(
    responses={
        200: OpenApiResponse(
            response=UserSerializer,
            description="Информация о пользователе успешно получена.",
        ),
        401: OpenApiResponse(
            description="Неавторизованный доступ (отсутствует или неверен токен)."
        ),
    },
    tags=["Пользователи"],  # Группирует эндпоинты в интерфейсе Redoc в одну вкладку
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
    description=("Просматривать информацию могут только авторизованные пользователи."),
    responses={
        200: OpenApiResponse(
            response=UserPublicProfileSerializer,
            description="Публичные данные пользователя успешно получены.",
        ),
        401: OpenApiResponse(
            description="Неавторизованный доступ (отсутствует или неверен токен)."
        ),
        404: OpenApiResponse(description="Пользователь с указанным ID не найден."),
    },
    tags=["Пользователи"],
)
class UserPublicRetrieveAPIView(RetrieveAPIView):
    """
    API для просмотра ПУБЛИЧНОГО профиля любого пользователя платформы по его ID.

    Возвращает только безопасные (открытые) данные пользователя.
    """

    queryset = CustomUser.objects.all()
    serializer_class = (
        UserPublicProfileSerializer  # Всегда отдаем только публичный сериализатор
    )
    permission_classes = (IsAuthenticated,)


@extend_schema(
    summary="Создание нового платежа",
    description=(
        "Создает запись платежа в базе данных Авроры со статусом 'pending' "
        "и генерирует живую ссылку 'payment_url' на защищенную форму Stripe Checkout."
    ),
    responses={
        201: OpenApiResponse(
            response=PaymentCreateSerializer,  # ИСПРАВЛЕНО: возвращаем схему платежа, а не юзера!
            description="Платеж успешно создан. В ответе содержится payment_url для редиректа.",
        ),
        400: OpenApiResponse(description="Ошибка валидации входных данных."),
        401: OpenApiResponse(
            description="Пользователь не авторизован (отсутствует JWT-токен)."
        ),
    },
    tags=["Профиль"],  # Объединено в одну группу с профилями, как в вашем условии
)
class PaymentCreateAPIView(CreateAPIView):
    """
    API-представление для создания платежа.
    Генерирует ссылку Stripe Checkout и сохраняет данные в базу.
    """

    serializer_class = PaymentCreateSerializer
    queryset = Payments.objects.all()
    permission_classes = (IsAuthenticated,)

    payment_url = None

    def perform_create(self, serializer):
        # Сохраняем черновик платежа в базу со статусом ожидания
        payment_record = serializer.save(
            user=self.request.user, status="pending", payment_method="stripe"
        )

        try:
            # Передаем объект платежа в наш сервис Stripe
            session_id, payment_url = stripe_service.create_checkout_session(
                payment_record
            )

            # Дописываем полученный session_id в модель и сохраняем изменения
            payment_record.session_id = session_id
            payment_record.save()

            # Сохраняем ссылку в инстанс view для метода create
            self.payment_url = payment_url

            # ВОЗВРАЩАЕМ обновленный объект из базы, чтобы использовать его в методе create
            return payment_record

        except RuntimeError as e:
            raise ValidationError({"error": str(e)})

    def create(self, request, *args, **kwargs):
        """Переопределяем метод ответа, чтобы добавить в JSON живую ссылку на оплату."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Перехватываем обновленный инстанс из perform_create
        payment_instance = self.perform_create(serializer)

        # Создаем НОВЫЙ сериализатор на основе актуального объекта из базы данных Aurora
        final_serializer = self.get_serializer(payment_instance)

        headers = self.get_success_headers(final_serializer.data)

        # Теперь здесь будут все актуальные поля: и status, и session_id
        response_data = final_serializer.data
        response_data["payment_url"] = getattr(self, "payment_url", None)

        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema(
    exclude=True
)  # Эта строчка полностью скроет вебхук из Swagger-документации!
class StripeWebhookView(APIView):
    """
    API эндпоинт для приема уведомлений (вебхуков) от Stripe.
    Проверяет подпись запроса и автоматически обновляет статусы платежей.
    """

    # Доступ открыт для всех (AllowAny), так как запросы шлет автоматический сервер Stripe,
    # а не авторизованный пользователь. Безопасность проверяется внутри сервиса по ключу подписи.
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        payload = request.body
        # Получаем заголовок с криптографической подписью Stripe
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        if not sig_header:
            return HttpResponse("Missing signature", status=status.HTTP_400_BAD_REQUEST)

        # Передаем сырые данные и подпись в сервисный слой для проверки и обработки
        success = stripe_service.verify_and_process_webhook(payload, sig_header)

        # Если проверка подписи прошла успешно и статус обновлен
        if success:
            return HttpResponse(
                "Webhook processed successfully", status=status.HTTP_200_OK
            )

        # Если подпись подделана или произошла ошибка
        return HttpResponse(
            "Invalid payload or signature", status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    summary="Проверка статуса платежа",
    description=(
        "Принудительно запрашивает актуальный статус сессии из Stripe API по её идентификатору. "
        "В случае подтверждения оплаты автоматически переводит статус платежа в базе Aurora в 'succeeded'."
    ),
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,  # Кастомный JSON-объект
            description="Статус платежа успешно проверен и обновлен.",
            examples=[
                OpenApiExample(
                    name="Успешный ответ",
                    value={
                        "status": "succeeded",
                        "message": "Статус успешно обновлен на Оплачено.",
                    },
                    response_only=True,  # Указываем, что этот пример только для ответа
                )
            ],
        ),
        400: OpenApiResponse(
            description="Ошибка: у данного платежа отсутствует сессия Stripe или платеж не найден."
        ),
        401: OpenApiResponse(
            description="Пользователь не авторизован (отсутствует JWT-токен)."
        ),
    },
    tags=["Профиль"],
)
class PaymentStatusCheckAPIView(APIView):
    """
    Эндпоинт для ручной/принудительной проверки статуса платежной сессии в Stripe.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request, pk, *args, **kwargs):
        # Находим платеж текущего пользователя в базе данных
        payment = get_object_or_404(Payments, id=pk, user=request.user)

        # Если платеж уже зафиксирован как успешный, сразу отдаем статус
        if payment.status == "succeeded":
            return Response(
                {"status": "succeeded", "message": "Платеж уже успешно проведен."}
            )

        # Если у платежа нет session_id (например, платили наличными)
        if not payment.session_id:
            return Response(
                {"error": "Для данного платежа не найдена сессия Stripe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Запрашиваем актуальный статус у Stripe API через наш сервис
            stripe_status = stripe_service.retrieve_checkout_session(payment.session_id)

            # Если Stripe подтверждает, что сессия оплачена ('paid')
            if stripe_status == "paid":
                payment.status = "succeeded"
                payment.save()

                # Здесь также можно продублировать вызов автоматической подписки,
                # если вебхук вдруг не сработал ранее:
                # if payment.paid_course:
                #     Subscribe.objects.get_or_create(user=payment.user, course=payment.paid_course)

                return Response(
                    {
                        "status": "succeeded",
                        "message": "Статус успешно обновлен на Оплачено.",
                    }
                )

            # Если сессия все еще не оплачена
            return Response(
                {
                    "status": "pending",
                    "message": "Платеж все еще ожидает оплаты в Stripe.",
                }
            )

        except RuntimeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="История платежей текущего пользователя",
    description=(
        "Возвращает список всех транзакций и оплат, совершенных текущим авторизованным пользователем. "
        "Доступна фильтрация по курсу, уроку и методу оплаты, а также сортировка по дате платежа."
    ),
    responses={
        200: OpenApiResponse(
            response=PaymentSerializer(many=True),
            description="Список платежей успешно получен.",
        ),
        401: OpenApiResponse(
            description="Неавторизованный доступ (отсутствует или неверен JWT-токен)."
        ),
    },
    tags=[
        "Профиль"
    ],  # Размещаем платежи в блоке личного профиля, рядом с CurrentUserProfileAPIView
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
