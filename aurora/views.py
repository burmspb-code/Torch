"""
Модуль представлений (Views) для приложения Aurora.

Обеспечивает бизнес-логику и обработку HTTP-запросов для API:
- Управление курсами (Course) реализовано через комплексный ModelViewSet.
- Управление уроками (Lesson) разделено по отдельным классам Generic Views
  для гибкой настройки каждой CRUD-операции.
"""

from django.db.models import Count
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet

from aurora.models import Course, Lesson
from aurora.serializers import CourseSerializer, LessonSerializer


# CRUD для Курса через ViewSet (Автоматически: Create, Retrieve, Update, Destroy, List)
class CourseViewSet(ModelViewSet):
    """
    ViewSet для управления курсами платформы Aurora.

    Оптимизирован для предотвращения проблемы N+1 запросов: количество связанных
    уроков агрегируется на уровне базы данных для всех операций вывода.
    """

    # Перенесли annotate сюда — теперь проблема N+1 решена для всех курсов!
    queryset = Course.objects.annotate(quantity_lessons=Count("lessons"))
    serializer_class = CourseSerializer


# CRUD для Урока через Generic Views
class LessonCreateAPIView(CreateAPIView):
    """
    Эндпоинт для создания одного урока или массового создания списка уроков.

    Поддерживает как ручное указание ID автора в JSON-запросе, так и автоматическую
    подстановку текущего авторизованного пользователя, если автор не указан.
    """

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def create(self, request, *args, **kwargs):
        """Обрабатывает POST-запрос с поддержкой списков и гибкой валидацией автора."""
        # Автоматически определяем структуру входящих данных (массив или объект)
        is_many = isinstance(request.data, list)

        serializer = self.get_serializer(data=request.data, many=is_many)
        serializer.is_valid(raise_exception=True)

        # Настройка гибкого заполнения автора
        if is_many:
            for lesson_data in serializer.validated_data:
                # Если автор не передан руками в Postman — подставляем текущего юзера
                if not lesson_data.get("author"):
                    lesson_data["author"] = self.request.user
        else:
            if not serializer.validated_data.get("author"):
                serializer.validated_data["author"] = self.request.user

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LessonListAPIView(ListAPIView):
    """Эндпоинт для просмотра списка всех уроков."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonRetrieveAPIView(RetrieveAPIView):
    """Эндпоинт для просмотра детальной информации об одном уроке."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonUpdateAPIView(UpdateAPIView):
    """Эндпоинт для редактирования параметров урока."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class LessonDestroyAPIView(DestroyAPIView):
    """Эндпоинт для удаления урока из системы."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
