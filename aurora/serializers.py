"""
Модуль сериализаторов приложения Aurora.

Содержит классы преобразования данных моделей Course и Lesson
в JSON-формат (сериализация) и обратно в Python-объекты (десериализация)
с валидацией входящих параметров.
"""

from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from aurora.models import Lesson, Course, Subscribe
from aurora.validators import validator_allowed_words


class LessonBulkCreateListSerializer(serializers.ListSerializer):
    """Кастомный класс для обработки списка при массовом создании уроков."""

    def create(self, validated_data):
        # Автор уже находится внутри validated_data благодаря View.
        lessons = [Lesson(**item) for item in validated_data]

        # Сохраняем в базу за один SQL-запрос внутри транзакции.
        # Во время генерации схемы Redoc этот метод не вызывается,
        # поэтому база данных защищена от ошибок.
        with transaction.atomic():
            return Lesson.objects.bulk_create(lessons)


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    # Назначаем валидатор на поле для внешней ссылки
    external_link = serializers.URLField(
        validators=[validator_allowed_words],
        required=False,
        allow_null=True,
        allow_blank=True,
    )

    # Явно указываем min_value на уровне сериализатора для корректного Swagger
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal(
            "0.00"
        ),  # Это уберет знак минус из регулярного выражения в схеме!
    )

    class Meta:
        """Конфигурация полей сериализатора."""

        model = Lesson
        fields = (
            "id",
            "title",
            "description",
            "preview",
            "external_link",
            "price",
            "is_archived",
            "course",
            "author",
        )
        list_serializer_class = LessonBulkCreateListSerializer
        extra_kwargs = {
            "author": {"required": False}  # Поле 'author' не обязательно в JSON
        }


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор курса, включающий агрегированные данные о количестве уроков."""

    # DRF автоматически вызовет метод @property price из модели Course
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    # Просто указываем поле как IntegerField, Django сам возьмет его из annotate
    quantity_lessons = serializers.IntegerField(read_only=True)

    # Для информации об уроках используем готовый сериализатор
    lesson_information = LessonSerializer(source="lessons", many=True, read_only=True)

    # Выводим информацию о подписке
    course_subscription = serializers.SerializerMethodField()

    def get_course_subscription(self, obj) -> bool:
        """Возвращаем True если у пользователя есть подписка на курс, иначе False."""

        # Безопасно получаем request из контекста
        request = self.context.get("request")

        if (
            not request or request.user.is_anonymous
        ):  # Проверка на незарегистрированного пользователя
            return False

        # Получаем флаг подписки есть/нет
        is_subscribe = obj.subscribes.filter(
            user=request.user, is_archived=False
        ).exists()

        return True if is_subscribe else False

    class Meta:
        """Конфигурация полей сериализатора."""

        model = Course
        fields = (
            "id",
            "title",
            "preview",
            "description",
            "price",
            "course_subscription",
            "is_archived",
            "author",
            "quantity_lessons",
            "lesson_information",
        )


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализтор для работы с подписками пользователя."""

    class Meta:
        """Класс метаданных."""

        model = Subscribe
        fields = ["id", "user", "course", "is_archived"]
        # Делаем поля доступными только на чтение, чтобы Swagger не требовал их в POST-запросе
        read_only_fields = ["user", "course", "is_archived"]


# class CourseSerializer(serializers.ModelSerializer):
#     """Сериализатор курса, включающий агрегированные данные о количестве уроков."""
#
#     # Для количества уроков поле автоматически ищет метод get_quantity_lessons
#     quantity_lessons = serializers.SerializerMethodField()
#
#     # Для информации об уроках используем готовый сериализатор
#     lesson_information = LessonSerializer(source="lessons", many=True, read_only=True)
#
#     class Meta:
#         """Конфигурация полей сериализатора."""
#
#         model = Course
#         fields = (
#             "id",
#             "title",
#             "preview",
#             "description",
#             "is_archived",
#             "author",
#             "quantity_lessons",
#             "lesson_information",
#         )
#
#     def get_quantity_lessons(self, obj):
#         """Возвращает количество уроков для курса."""
#         if hasattr(obj, "quantity_lessons"):
#             return obj.quantity_lessons
#
#         # Если анотации нет (сериализатор используется в другой логике) делаем запрос к БД
#         return obj.lessons.count()
