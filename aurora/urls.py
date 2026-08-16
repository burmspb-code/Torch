"""
Конфигурация URL-маршрутов для приложения Aurora.

Данный модуль определяет эндпоинты для управления курсами и уроками (CRUD):
- Маршруты для курсов (Course) генерируются автоматически через SimpleRouter
  на базе ViewSet.
- Маршруты для уроков (Lesson) прописаны вручную с использованием Generic Views
  для разделения логики операций.
- Маршрут для включения/выключения подписки на курс.
"""

from django.urls import include
from django.urls import path
from rest_framework.routers import SimpleRouter

from aurora.apps import AuroraConfig
from aurora.views import (
    CourseViewSet,
    LessonCreateAPIView,
    LessonListAPIView,
    LessonUpdateAPIView,
    LessonDestroyAPIView,
    LessonRetrieveAPIView,
    SubscribeAPIView,
)

app_name = AuroraConfig.name

router = SimpleRouter()
router.register("courses", CourseViewSet, basename="courses")

urlpatterns = [
    # Маршруты для уроков (CRUD)
    path("lessons/", LessonListAPIView.as_view(), name="lesson_list"),
    path("lessons/create/", LessonCreateAPIView.as_view(), name="lesson_create"),
    path("lessons/<int:pk>/update/", LessonUpdateAPIView.as_view(), name="lesson_update"),
    path("lessons/<int:pk>/delete/", LessonDestroyAPIView.as_view(), name="lesson_delete"),
    path("lessons/<int:pk>/", LessonRetrieveAPIView.as_view(), name="lesson_detail"),

    # Маршрут для включения/выключения подписки
    path("courses/<int:course_id>/subscribe/", SubscribeAPIView.as_view(), name="course_subscribe"),

    # Автоматические маршруты для курсов
    path("", include(router.urls)),
]
