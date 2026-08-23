"""
Модуль представлений (Views) для приложения Aurora.

Обеспечивает бизнес-логику и обработку HTTP-запросов для API:
- Управление курсами (Course) реализовано через комплексный ModelViewSet.
- Управление уроками (Lesson) разделено по отдельным классам Generic Views
  для гибкой настройки каждой CRUD-операции.
- Управление подписками (Subscribe) реализовано через APIView.
"""

from django.db import transaction
from django.db.models import Count
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    OpenApiParameter,
)
from rest_framework import status
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_bulk import BulkCreateModelMixin

from aurora.models import Course, Lesson, Subscribe
from aurora.paginators import CoursePagination, LessonPagination
from aurora.serializers import CourseSerializer, LessonSerializer, SubscribeSerializer
from aurora.services import process_course_update
from aurora.tasks import send_subscription_email
from users.permissions import IsModerPermission, IsOwnerPermission

# Выносим повторяющиеся схемы ответов для читаемости кода
COMMON_ERRORS = {
    401: OpenApiResponse(
        description="Пользователь не аутентифицирован (Токен отсутствует или невалиден)"
    ),
    403: OpenApiResponse(
        description="Недостаточно прав для выполнения данной операции"
    ),
}

VALIDATION_ERROR = {
    400: OpenApiResponse(
        description="Ошибка валидации переданных данных (Неверный формат полей)"
    )
}

NOT_FOUND_ERROR = {
    404: OpenApiResponse(description="Запрашиваемый курс не найден в системе")
}


@extend_schema_view(
    list=extend_schema(
        summary="Получить список курсов",
        description="Возвращает список курсов. Администраторы и модераторы видят все курсы, обычные пользователи — только созданные ими.",
        responses={
            200: CourseSerializer(many=True),
            **COMMON_ERRORS,  # Добавляет 401 и 403 ошибки
        },
        tags=["Курсы"],
    ),
    create=extend_schema(
        summary="Создать новый курс",
        description="Создает новый обучающий курс. Доступно администраторам и обычным пользователям (модераторам доступ запрещен). Текущий пользователь автоматически становится автором.",
        responses={
            201: CourseSerializer,
            **VALIDATION_ERROR,  # Добавляет 400
            **COMMON_ERRORS,  # Добавляет 401 и 403
        },
        tags=["Курсы"],
    ),
    retrieve=extend_schema(
        summary="Просмотреть детали курса",
        description="Возвращает подробную информацию о конкретном курсе по его ID. Доступно модераторам или автору курса.",
        responses={
            200: CourseSerializer,
            **NOT_FOUND_ERROR,  # Добавляет 404
            **COMMON_ERRORS,  # Добавляет 401 и 403
        },
        tags=["Курсы"],
    ),
    update=extend_schema(
        summary="Полностью обновить курс",
        description="Полное обновление всех полей курса. Доступно модераторам или автору курса.",
        responses={
            200: CourseSerializer,
            **VALIDATION_ERROR,  # Добавляет 400
            **NOT_FOUND_ERROR,  # Добавляет 404
            **COMMON_ERRORS,  # Добавляет 401 и 403
        },
        tags=["Курсы"],
    ),
    partial_update=extend_schema(
        summary="Частично обновить курс",
        description="Изменение отдельных полей курса (PATCH). Доступно модераторам или автору курса.",
        responses={
            200: CourseSerializer,
            **VALIDATION_ERROR,  # Добавляет 400
            **NOT_FOUND_ERROR,  # Добавляет 404
            **COMMON_ERRORS,  # Добавляет 401 и 403
        },
        tags=["Курсы"],
    ),
    destroy=extend_schema(
        summary="Удалить курс",
        description="Удаляет курс из системы. Операция доступна только администраторам или автору курса.",
        responses={
            204: OpenApiResponse(description="Курс успешно удален"),
            **NOT_FOUND_ERROR,  # Добавляет 404
            **COMMON_ERRORS,  # Добавляет 401 и 403
        },
        tags=["Курсы"],
    ),
)
class CourseViewSet(ModelViewSet):
    """
    ViewSet для управления курсами платформы Aurora.

    Оптимизирован для предотвращения проблемы N+1 запросов: количество связанных
    уроков агрегируется на уровне базы данных для всех операций вывода.
    """

    serializer_class = CourseSerializer
    pagination_class = CoursePagination

    def get_permissions(self):
        """Динамические права по ТЗ с учетом специфики DRF:
        - Создание (create): Администраторы и обычные пользователи (Модераторам нельзя),
        - Удаление (destroy): Только Админ или Автор объекта,
        - Редактирование и просмотр одного курса (update, retrieve): Только Модератор или Автор,
        - Просмотр списка (list): Админ, Модератор, Автор видит только свои курсы.
        """
        if self.action == "create":
            permission_classes = (IsAuthenticated & ~IsModerPermission,)
        elif self.action == "destroy":
            permission_classes = (IsAdminUser | IsOwnerPermission,)
        elif self.action in ["update", "partial_update", "retrieve"]:
            permission_classes = (IsModerPermission | IsOwnerPermission,)
        else:
            permission_classes = (IsAuthenticated,)

        # Просмотр списка настраивается в get_queryset()

        return tuple(permission() for permission in permission_classes)

    def get_queryset(self):
        # ЗАЩИТА ДЛЯ SWAGGER: если схему генерирует робот, отдаем пустой кверисет
        if getattr(self, "swagger_fake_view", False) or "spectacular" in str(
            self.request
        ):
            return Course.objects.none()

        # Базовый кверисет с решенной проблемой N+1
        base_queryset = Course.objects.annotate(
            quantity_lessons=Count("lessons")
        ).order_by("-id")
        user = self.request.user

        if user.is_staff or user.is_moderator:
            return base_queryset

        # Обычные пользователи видят только свои курсы
        return base_queryset.filter(author=user)

    def perform_create(self, serializer):
        """Автоматически назначает текущего пользователя автором курса при создании."""
        serializer.save(author=self.request.user)

# ============================ CRUD для Уроков через Generics ==========================================


@extend_schema(
    summary="Создание урока или массовое создание списка уроков",
    description=(
        "Позволяет создать как один урок, так и список уроков (массив JSON) за один запрос. "
        "Доступно только авторизованным пользователям, кроме модераторов. "
        "Текущий пользователь автоматически назначается автором для всех создаваемых уроков."
    ),
    responses={
        201: OpenApiResponse(
            response=LessonSerializer(many=True),
            description="Урок(и) успешно создан(ы). Возвращает список созданных объектов.",
        ),
        401: OpenApiResponse(
            description="Неавторизованный доступ (отсутствует или неверен токен)."
        ),
        403: OpenApiResponse(
            description="Доступ запрещен (модераторам запрещено создавать уроки)."
        ),
    },
    tags=["Уроки"],
)
class LessonCreateAPIView(BulkCreateModelMixin, CreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated & ~IsModerPermission]

    def perform_create(self, serializer):
        # DRF автоматически применит self.request.user как для одиночного объекта,
        # так и для каждого элемента в массовом создании (bulk),
        # при этом генератор документации Redoc отработает идеально.
        serializer.save(author=self.request.user)


@extend_schema(
    summary="Получить список уроков",
    description=(
        "Возвращает список всех уроков, доступных пользователю. "
        "Модераторы видят абсолютно все уроки в системе. "
        "Обычные авторизованные пользователи видят только те уроки, где они являются авторами."
    ),
    responses={
        200: LessonSerializer(many=True),
        401: OpenApiResponse(
            description="Неавторизованный доступ (отсутствует или неверен токен)"
        ),
    },
    tags=["Уроки"],  # Группирует эндпоинты в интерфейсе Redoc в одну вкладку
)
class LessonListAPIView(ListAPIView):
    """Эндпоинт для просмотра списка всех уроков."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = LessonPagination
    # Просматривать список могут ВСЕ авторизованные пользователи (включая модераторов)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Фильтруем список уроков под конкретного пользователя."""
        # ЗАЩИТА ДЛЯ REDOC: если метод вызван роботом-генератором,
        # сразу возвращаем пустой кверисет, не двигаясь дальше по коду.
        if getattr(self, "swagger_fake_view", False) or "spectacular" in str(
            self.request
        ):
            return Lesson.objects.none()

        user = self.request.user

        if user.is_moderator or user.is_superuser:
            return Lesson.objects.all()

        return Lesson.objects.filter(author=user)


@extend_schema(
    summary="Просмотр детальной информации об уроке.",
    description=("Просматривать информацию об уроке могут авторы и модераторы."),
    responses={
        200: OpenApiResponse(
            response=LessonSerializer,
            description="Информаци об уроке успешно получена.",
        ),
        401: OpenApiResponse(
            description="Неавторизованный доступ (отсутствует или неверен токен)."
        ),
        403: OpenApiResponse(
            description="Доступ запрещен (вы не являетесь автором этого урока или модератором)."
        ),
        404: OpenApiResponse(description="Урок с указанным ID не найден."),
    },
    tags=["Уроки"],  # Группирует эндпоинты в интерфейсе Redoc в одну вкладку
)
class LessonRetrieveAPIView(RetrieveAPIView):
    """Эндпоинт для просмотра детальной информации об одном уроке."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Просматривать детали могут Авторы и Модераторы
    permission_classes = [IsAuthenticated & (IsModerPermission | IsOwnerPermission)]


@extend_schema_view(
    update=extend_schema(
        summary="Полностью обновить урок",
        description="Полное обновление всех параметров урока (PUT). Доступно только автору урока или модератору.",
    ),
    partial_update=extend_schema(
        summary="Частично обновить урок",
        description="Изменение отдельных полей урока (PATCH). Доступно только автору урока или модератору.",
    ),
)
@extend_schema(
    summary="Редактирование информации об уроке.",
    description=("Редактировать информацию об уроке могут авторы и модераторы."),
    responses={
        200: LessonSerializer,
        401: OpenApiResponse(
            description="Неавторизованный доступ (отсутствует или неверен токен)."
        ),
        403: OpenApiResponse(
            description="Доступ запрещен (вы не являетесь автором этого урока или модератором)."
        ),
        404: OpenApiResponse(description="Урок с указанным ID не найден."),
    },
    tags=["Уроки"],  # Группирует эндпоинты в интерфейсе Redoc в одну вкладку
)
class LessonUpdateAPIView(UpdateAPIView):
    """Эндпоинт для редактирования параметров урока."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Редактировать уроки могут только Авторы и Модераторы
    permission_classes = [IsAuthenticated & (IsModerPermission | IsOwnerPermission)]


@extend_schema(
    summary="Удаление урока.",
    description=("Удалить урок может только администратор."),
    responses={
        204: LessonSerializer,
        401: OpenApiResponse(
            description="Неавторизованный доступ (отсутствует или неверен токен)."
        ),
        403: OpenApiResponse(
            description="Доступ запрещен (вы не являетесь администратором)."
        ),
        404: OpenApiResponse(description="Урок с указанным ID не найден."),
    },
    tags=["Уроки"],  # Группирует эндпоинты в интерфейсе Redoc в одну вкладку
)
class LessonDestroyAPIView(DestroyAPIView):
    """Эндпоинт для удаления урока из системы."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Удалять уроки может только Админ
    permission_classes = [IsAdminUser]


class SubscribeAPIView(APIView):
    """
    API-представление для создания/удаления подписки пользователя.
    Реализован сценарий мягкого удаления (перенос в архив) для
    возможной последующей аналитики данных.
    """

    serializer_class = SubscribeSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Управление подпиской на курс (Toggle / Мягкое удаление)",
        description=(
            "Переключает состояние подписки текущего пользователя на указанный курс. "
            "Если подписки не было — она создается. Если она была активна — переводится в архив "
            "(мягкое удаление). Если находилась в архиве — восстанавливается."
        ),
        parameters=[
            OpenApiParameter(
                name="course_id",
                type=int,
                location=OpenApiParameter.PATH,
                description="Уникальный идентификатор курса",
                required=True,
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Статус подписки успешно изменен",
                examples={
                    "application/json": {
                        "message": "Подписка успешно добавлена",
                        "is_subscribed": True,
                    }
                },
            ),
            401: OpenApiResponse(description="Пользователь не авторизован"),
            404: OpenApiResponse(description="Указанный курс не найден"),
        },
    )
    def post(self, request, *args, **kwargs):
        user = self.request.user  # Получаем пользователя
        course_id = kwargs.get("course_id")  # Получаем курс
        subscribe_obj = Subscribe.objects.filter(
            user=user, course_id=course_id
        ).first()  # Получаем подписку
        # Выставляем флаг активности подсписки
        is_active = True if not subscribe_obj else subscribe_obj.is_archived

        obj, created = Subscribe.objects.update_or_create(
            user=user, course_id=course_id, defaults={"is_archived": not is_active}
        )

        if created:
            message = "Подписка успешно добавлена"
            send_email_flag = True
        else:
            if is_active:
                message = "Подписка восстановлена"
                send_email_flag = True  # Отправляем письмо и при восстановлении
            else:
                message = "Подписка успешно удалена"
                send_email_flag = False

        # Отправляем письмо асинхронно, если подписка создана или восстановлена
        if send_email_flag:
            try:
                course_title = Course.objects.get(id=course_id).title
                # ВАЖНО: Используем .delay() для отправки в очередь Celery
                send_subscription_email.delay(user.email, course_title)
            except Course.DoesNotExist:
                pass  # Защита на случай, если курс успели удалить

        return Response(
            {"message": message, "is_subscribed": is_active}, status=status.HTTP_200_OK
        )
