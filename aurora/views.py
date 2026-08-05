"""
Модуль представлений (Views) для приложения Aurora.

Обеспечивает бизнес-логику и обработку HTTP-запросов для API:
- Управление курсами (Course) реализовано через комплексный ModelViewSet.
- Управление уроками (Lesson) разделено по отдельным классам Generic Views
  для гибкой настройки каждой CRUD-операции.
"""

from django.db.models import Count
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from aurora.models import Course, Lesson
from aurora.serializers import CourseSerializer, LessonSerializer
from users.permissions import IsModerPermission, IsOwnerPermission


# CRUD для Курса через ViewSet (Автоматически: Create, Retrieve, Update, Destroy, List)
class CourseViewSet(ModelViewSet):
    """
    ViewSet для управления курсами платформы Aurora.

    Оптимизирован для предотвращения проблемы N+1 запросов: количество связанных
    уроков агрегируется на уровне базы данных для всех операций вывода.
    """
    serializer_class = CourseSerializer

    def get_permissions(self):
        """Динамические права по ТЗ с учетом специфики DRF:
        - Создание (create): Администраторы и обычные пользователи (Модераторам нельзя),
        - Удаление (destroy): Только Админ или Автор объекта,
        - Редактирование и просмотр одного курса (update, retrieve): Только Модератор или Автор,
        - Просмотр списка (list): Админ, Модератор, Автор видит только свои курсы.
        """
        # Модераторам запрещено создавать курсы
        if self.action == "create":
            # Исключаем модераторов из возможности создания
            return [IsAuthenticated() & ~IsModerPermission()]

        if self.action == "destroy":
            return [IsAdminUser() | IsOwnerPermission()]

        if self.action in ["update", "partial_update", "retrieve"]:
            return [IsModerPermission() | IsOwnerPermission()]

        # Просмотр списка настаивается в get_queryset()
        return [IsAuthenticated()]

    def get_queryset(self):
        # Базовый кверисет с решенной проблемой N+1
        base_queryset = Course.objects.annotate(quantity_lessons=Count("lessons"))
        user = self.request.user

        if user.is_staff or user.is_moderator:
            return base_queryset

        # Обычные пользователи видят только свои курсы
        return base_queryset.filter(author=user)

    def perform_create(self, serializer):
        """Автоматически назначает текущего пользователя автором курса при создании."""
        serializer.save(author=self.request.user)


# CRUD для Курса через Generics
class LessonCreateAPIView(CreateAPIView):
    """Эндпоинт для создания одного урока или массового создания списка уроков."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Создать урок могут все авторизованные пользователи, но не Модератор
    permission_classes = [IsAuthenticated & ~IsModerPermission]

    def get_serializer(self, *args, **kwargs):
        """Позволяет эндпоинту принимать как один объект, так и список объектов."""
        # Если в теле запроса пришел JSON-массив (список)
        if isinstance(kwargs.get("data"), list):
            kwargs["many"] = True  # Включаем bulk-режим для ListSerializer

        return super().get_serializer(*args, **kwargs)


class LessonListAPIView(ListAPIView):
    """Эндпоинт для просмотра списка всех уроков."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Просматривать список могут ВСЕ авторизованные пользователи (включая модераторов)
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Фильтруем просмотр списка уроков по текущему пользователю."""
        user = self.request.user
        if user.is_moderator:
            return Lesson.objects.all()
        return Lesson.objects.filter(author=user)


class LessonRetrieveAPIView(RetrieveAPIView):
    """Эндпоинт для просмотра детальной информации об одном уроке."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Просматривать детали могут Авторы и Модераторы
    permission_classes = [IsAuthenticated & (IsModerPermission | IsOwnerPermission)]


class LessonUpdateAPIView(UpdateAPIView):
    """Эндпоинт для редактирования параметров урока."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Редактировать уроки могут только Авторы и Модераторы
    permission_classes = [IsAuthenticated & (IsModerPermission | IsOwnerPermission)]


class LessonDestroyAPIView(DestroyAPIView):
    """Эндпоинт для удаления урока из системы."""

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    # Удалять уроки может только Админ
    permission_classes = [IsAdminUser]
