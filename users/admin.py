"""Настройки административной панели для управления пользователями."""

from django.contrib import admin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.translation import gettext_lazy as _

from users.forms import CustomUserChangeForm, CustomUserCreationForm
from users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
    Панель администратора для управления кастомной моделью пользователя CustomUser.

    Обеспечивает безопасное создание, редактирование и смену паролей для
    кастомных пользователей на базе AbstractBaseUser.
    """

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    ordering = ("email",)

    list_display = (
        "email",
        "phone_number",
        "city",
        "avatar",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
        "last_login",
    )

    list_filter = ("is_staff", "is_superuser", "is_active")
    readonly_fields = ("date_joined", "last_login")
    search_fields = ("email", "phone_number", "city")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Личные данные", {"fields": ("phone_number", "city", "avatar")}),
        ("Права доступа", {"fields": ("is_active", "is_staff", "is_superuser", 'groups', 'user_permissions')}),
        ("Важные даты", {"fields": ("date_joined", "last_login")}),  # Добавили сюда
    )

    # Делает выбор групп визуально удобным (две колонки со стрелочками и поиском)
    filter_horizontal = ('groups', 'user_permissions')

    def get_form(self, request, obj=None, **kwargs):
        """Динамически выбирает форму создания или редактирования."""
        if obj is None:
            kwargs["form"] = self.add_form
        form = super().get_form(request, obj, **kwargs)

        if "password" in form.base_fields and obj is not None:
            form.base_fields["password"].user = obj
        return form

    def get_fieldsets(self, request, obj=None):
        """Динамически скрывает лишние поля при создании пользователя."""
        if not obj:
            return ((None, {"fields": ("email", "password", "password2")}),)
        return super().get_fieldsets(request, obj)

    def user_change_password(self, request, id, form_url=""):
        """Кастомный обработчик страницы изменения пароля для CustomUser."""
        user = self.get_object(request, id)
        if user is None:
            raise Http404(_("User with id %s does not exist.") % id)

        if request.method == "POST":
            form = AdminPasswordChangeForm(user, request.POST)
            if form.is_valid():
                form.save()
                return self.response_post_save_change(request, user)
        else:
            form = AdminPasswordChangeForm(user)

        fieldsets = [(None, {"fields": list(form.fields.keys())})]
        adminForm = admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            "title": _("Change password: %s") % user,
            "adminForm": adminForm,
            "form": form,
            "object_id": id,
            "original": user,
            "is_popup": False,
            "media": self.media + form.media,
            "errors": admin.helpers.AdminErrorList(form, []),
            "app_label": self.opts.app_label,
            "opts": self.opts,
            "has_change_permission": self.has_change_permission(request, user),
        }

        return TemplateResponse(
            request,
            "admin/auth/user/change_password.html",
            context,
        )

    def get_urls(self):
        """Интегрирует URL смены пароля в структуру админки с высшим приоритетом."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "<id>/password/",
                self.admin_site.admin_view(self.user_change_password),
                name="auth_user_password_change",
            ),
        ]
        return custom_urls + urls
