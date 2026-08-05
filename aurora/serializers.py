"""
Модуль сериализаторов приложения Aurora.

Содержит классы преобразования данных моделей Course и Lesson
в JSON-формат (сериализация) и обратно в Python-объекты (десериализация)
с валидацией входящих параметров.
"""

from django.db import transaction
from rest_framework import serializers

from aurora.models import Lesson, Course


class LessonBulkCreateListSerializer(serializers.ListSerializer):
    """Кастомный класс для обработки списка при массовом создании уроков."""

    def create(self, validated_data):
        """Создание списка уроков с заполнением автора."""

        # Автоматически берем текущего юзера из контекста запроса
        user = self.context["request"].user

        # Заполняем автора для каждого урока в списке
        for item in validated_data:
            if not item.get("author"):
                item["author"] = user

        # Создаем объекты в памяти
        lessons = [Lesson(**item) for item in validated_data]

        # Сохраняем в базу за один SQL-запрос внутри транзакции
        with transaction.atomic():
            return Lesson.objects.bulk_create(lessons)


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    class Meta:
        """Конфигурация полей сериализатора."""

        model = Lesson
        fields = "__all__"
        list_serializer_class = LessonBulkCreateListSerializer
        extra_kwargs = {
            "author": {"required": False}  # Поле 'author' не обязательно в JSON
        }

    def create(self, validated_data):
        """Логика для одиночного создания (если пришел один JSON-объект)."""
        user = self.context["request"].user

        if not validated_data.get("author"):
            validated_data["author"] = user

        return super().create(validated_data)


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор курса, включающий агрегированные данные о количестве уроков."""

    # Просто указываем поле как IntegerField, Django сам возьмет его из annotate
    quantity_lessons = serializers.IntegerField(read_only=True)

    # Для информации об уроках используем готовый сериализатор
    lesson_information = LessonSerializer(source="lessons", many=True, read_only=True)

    class Meta:
        """Конфигурация полей сериализатора."""

        model = Course
        fields = (
            "id",
            "title",
            "preview",
            "description",
            "is_archived",
            "author",
            "quantity_lessons",
            "lesson_information",
        )


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
