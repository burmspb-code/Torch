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

    list_display = ("id", "title", "author", "is_archived", "updated_at")
    list_display_links = ("id", "title")
    list_editable = (
        "is_archived",
    )  # Позволяет модератору ставить галочку прямо в списке
    list_filter = ("is_archived", "author", "updated_at")
    search_fields = ("title", "description")
    inlines = [LessonInline]

    readonly_fields = ("updated_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author")

    def save_formset(self, request, form, formset, change):
        """Автоматическая привязка автора к урокам из инлайна."""
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, Lesson) and not instance.author:
                instance.author = request.user
            instance.save()

        # Сохраняем связи Many-to-Many, если они появятся в инлайнах в будущем
        formset.save_m2m()


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Панель управления уроками."""

    list_display = ("id", "title", "course", "author", "is_archived", "updated_at")
    list_editable = ("is_archived",)  # Быстрая архивация уроков из списка
    list_filter = ("is_archived", "course", "author", "updated_at")
    search_fields = ("title", "description")

    readonly_fields = ("updated_at",)

    def get_queryset(self, request):
        """Оптимизация запросов: жадная загрузка курса и автора."""
        return super().get_queryset(request).select_related("course", "author")

    def save_model(self, request, obj, form, change):
        """Автоматическая привязка текущего пользователя в качестве автора урока."""
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)
