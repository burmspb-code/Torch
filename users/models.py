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

from aurora.models import Course, Lesson


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
    date_joined = models.DateTimeField(
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


class Payments(models.Model):
    """Модель платежей."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.PROTECT,
        null=False,
        blank=False,
        related_name="payments",
        verbose_name="Пользователь",
    )
    payment_date = models.DateField(
        auto_now_add=True,  # Автоматически ставит текущую дату при создании
        verbose_name="Дата платежа"
    )
    paid_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        blank=True, # Может быть пустым, если оплачен отдельный урок
        null=True, # Обязательно True, так как on_delete=SET_NULL
        related_name="payments",
        verbose_name="Оплаченный курс",
        help_text="Выберите курс для оплаты",
    )
    paid_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        blank=True, # Может быть пустым, если оплачен отдельный урок
        null=True, # Обязательно True, так как on_delete=SET_NULL
        related_name="payments",
        verbose_name="Оплаченный урок",
        help_text="Выберите урок для оплаты",
    )
    payment_amount = models.DecimalField(
        decimal_places=2,
        default=0,
        max_digits=10,
        null=False,
        blank=False,
        verbose_name="Сумма оплаты",
        help_text="Укажите сумму платежа"
    )
    PAYMENT_METHODS: list[tuple[str, str]] = [
        ("cash", "Наличные"),
        ("transfer_to_account", "Перевод на счет"),
    ]
    payment_method = models.CharField(
        max_length=50,
        choices=PAYMENT_METHODS,
        verbose_name="Способ оплаты",
        help_text="Выберите способ оплаты",
    )

    class Meta:
        """Класс метаданных."""
        verbose_name="Платеж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        return f"Платеж {self.id} от {self.user} на сумму {self.payment_amount}"
