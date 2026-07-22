"""
Модуль сериализаторов приложения Aurora.

Содержит классы преобразования данных моделей Course и Lesson
в JSON-формат (сериализация) и обратно в Python-объекты (десериализация)
с валидацией входящих параметров.
"""

from rest_framework.serializers import ModelSerializer

from aurora.models import Lesson, Course


class LessonSerializer(ModelSerializer):
    class Meta:
        """Класс метаданных."""
        model = Lesson
        fields = '__all__'

class CourseSerializer(ModelSerializer):
    class Meta:
        """Класс метадонных."""
        model = Course
        fields = '__all__'
