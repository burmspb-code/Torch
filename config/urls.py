"""
Конфигурация корневых URL-маршрутов всего проекта.

Этот модуль перенаправляет запросы к соответствующим URL-конфигурациям приложений:
- Панель администратора Django доступна по адресу /admin/
- Эндпоинты курсов и уроков подключены через приложение aurora (/aurora/)
- Эндпоинты профилей пользователей подключены через приложение users (/users/)
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("aurora/", include("aurora.urls", namespace="aurora")),
    path("users/", include("users.urls", namespace="users")),
]
