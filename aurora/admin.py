"""
Настройки панели администратора приложения aurora.

Обеспечивает интерфейс модерации курсов и уроков для персонала платформы.
Включает в себя:
- Возможность инлайн-управления уроками прямо со страницы курса.
- Инструменты быстрой архивации/разархивации контента из общих списков.
- Автоматическое назначение автора для уроков, созданных через панель курса.
"""

from django.contrib import admin
from .models import Course, Lesson


class LessonInline(admin.TabularInline):
    """Позволяет управлять уроками прямо со страницы курса."""

    model = Lesson
    extra = 1
    fields = ("title", "author", "is_archived", "external_link")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Панель управления курсами с инструментами модерации."""

    list_display = ("id", "title", "author", "is_archived")
    list_display_links = ("id", "title")
    list_editable = (
        "is_archived",
    )  # ИСПРАВЛЕНО: Позволяет модератору ставить галочку прямо в списке
    list_filter = ("is_archived", "author")
    search_fields = ("title", "description")
    inlines = [LessonInline]

    def save_formset(self, request, form, formset, change):
        """Автоматическая привязка автора к урокам из инлайна."""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Lesson) and not instance.author:
                instance.author = request.user
        formset.save()


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Панель управления уроками."""

    list_display = ("id", "title", "course", "author", "is_archived")
    list_editable = ("is_archived",)  # ИСПРАВЛЕНО: Быстрая архивация уроков из списка
    list_filter = ("is_archived", "course", "author")
    search_fields = ("title", "description")
