"""
Модели управления пользователями (users).

Содержит кастомную модель пользователя CustomUser, расширяющую стандартный
функционал Django возможностью хранения номеров телефонов и аватаров.
Использует внешнюю библиотеку django-phonenumber-field для валидации номеров.

Применяется в качестве глобальной модели аутентификации проекта
через настройку AUTH_USER_MODEL в settings.py.
"""

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField
from django.db import models


class CustomUserManager(BaseUserManager):
    """Менеджер для управления пользователями, где email является логином."""

    def create_user(self, email, password=None, **extra_fields):
        """Создает, хэширует пароль и сохраняет обычного пользователя в базе данных."""
        if not email:
            raise ValueError("Поле Email обязательно для заполнения")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Принудительно устанавливает права суперпользователя и создает его."""
        # Жестко перезаписываем или создаем ключи в словаре extra_fields
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True

        # Теперь проверки не нужны, так как передать False "снаружи" уже невозможно
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Класс создания кастомной модели пользователя."""

    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        verbose_name="Email",
        help_text="Введите адрес электронной почты",
    )
    phone_number = PhoneNumberField(
        blank=True,
        null=True,
        unique=True,
        verbose_name="Номер телефона",
        help_text="Введите номер телефона",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Город",
        help_text="Введите город",
    )
    avatar = models.ImageField(
        blank=True,
        null=True,
        upload_to="users/avatars/",
        verbose_name="Аватар",
        help_text="Загрузите аватар",
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    is_staff = models.BooleanField(default=False, verbose_name="Статус персонала")
    data_joined = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата регистрации"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()  # Связываем модель с кастомным менеджером

    class Meta:
        """Класс метаданных."""

        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email
