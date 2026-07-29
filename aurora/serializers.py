"""
Модуль сериализаторов приложения Aurora.

Содержит классы преобразования данных моделей Course и Lesson
в JSON-формат (сериализация) и обратно в Python-объекты (десериализация)
с валидацией входящих параметров.
"""

from rest_framework import serializers

from aurora.models import Lesson, Course


class LessonBulkCreateListSerializer(serializers.ListSerializer):
    """Кастомный класс для обработки списка при массовом создании."""

    def create(self, validated_data):
        """
        Выполняет массовое создание уроков одним SQL-запросом.

        Принимает список словарей с валидированными данными, создает объекты
        в памяти и сохраняет их в базу данных через метод bulk_create().
        """
        lessons = [Lesson(**item) for item in validated_data]
        return Lesson.objects.bulk_create(lessons)


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор урока."""

    class Meta:
        """Конфигурация полей сериализатора."""

        model = Lesson
        fields = "__all__"

        # Указываем DRF использовать наш кастомный класс для списков
        list_serializer_class = LessonBulkCreateListSerializer


# ====================+++++++++++++++++++++++++++++++======================================================
# class CourseSerializer(serializers.ModelSerializer):
#     """Сериализатор курса, включающий агрегированные данные о количестве уроков."""
#
#     # Просто указываем поле как IntegerField, Django сам возьмет его из annotate
#     quantity_lessons = serializers.IntegerField(read_only=True)
#
#     # Для информации об уроках используем готовый сериализатор
#     lesson_information = LessonSerializer(source="lessons", many=True, read_only=True)
#
#     class Meta:
#         """Конфигурация полей сериализатора."""
#         model = Course
#         fields = ("id", "title", "preview", "description", "is_archived", "author", "quantity_lessons")
# =====================+++++++++++++++++++++++++++++++++++=================================================

class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор курса, включающий агрегированные данные о количестве уроков."""

    # Для количества уроков поле автоматически ищет метод get_quantity_lessons
    quantity_lessons = serializers.SerializerMethodField()

    # Для информации об уроках используем готовый сериализатор
    lesson_information = LessonSerializer(source="lessons", many=True, read_only=True)


    class Meta:
        """Конфигурация полей сериализатора."""
        model = Course
        fields = ("id", "title", "preview", "description", "is_archived", "author", "quantity_lessons", "lesson_information")

    def get_quantity_lessons(self, obj):
        """Возвращает количество уроков для курса."""
        if hasattr(obj, "quantity_lessons"):
            return obj.quantity_lessons

        # Если анотации нет (сериализатор используется в другой логике) делаем запрос к БД
        return obj.lessons.count()

