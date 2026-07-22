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
