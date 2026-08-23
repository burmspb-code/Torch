"""
Модели приложения LMS-системы aurora.

Содержит основные бизнес-сущности образовательной платформы:
- Course: Модель учебного курса, публикуемого независимыми авторами.
- Lesson: Модель отдельного урока, жестко связанного со своим курсом.

Обеспечивает гибкое управление жизненным циклом контента благодаря
механизмам безопасного удаления авторов (SET_NULL), каскадного удаления
уроков (CASCADE), ручной модерации через поле архивации (is_archived),
а также встроенной бэкенд-валидации обязательности автора при создании.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from decimal import Decimal

from config import settings


class Course(models.Model):
    """
    Модель для хранения информации об учебных курсах.

    Связи:
        lessons (Lesson): Обратная связь для получения всех уроков курса.

    Логика валидации:
        При создании нового курса поле 'author' является обязательным.
    """

    title = models.CharField(
        max_length=100,
        unique=True,
        blank=False,
        null=False,
        verbose_name="Курс",
        help_text="Введите название курса",
    )
    preview = models.ImageField(
        upload_to="aurora/images/course/",
        blank=True,
        null=True,
        verbose_name="Превью",
        help_text="Загрузите превью",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
        help_text="Введите описание",
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name="Архивный",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Автор",
        help_text="Укажите автора курса",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Время последнего обновления"
    )

    class Meta:
        """Настройки отображения модели в административной панели."""

        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["-id"]

    def __str__(self):
        return self.title

    def clean(self):
        """Проверка обязательности автора при создании нового курса."""
        super().clean()
        if not self.pk and not self.author:
            raise ValidationError(
                {
                    "author": "При создании нового курса необходимо обязательно указать автора."
                }
            )

    @property
    def price(self):
        """Динамический расчет цены в зависимости от уроков."""
        amount = self.lessons.filter(is_archived=False).aggregate(total=Sum("price"))
        return amount.get("total") or 0.00


class Lesson(models.Model):
    """
    Модель отдельного урока в рамках курса платформы Aurora.

    Связи:
        course (Course): Прямая связь с курсом (related_name='lessons').
        author (User): Прямая связь с автором (related_name='lessons').
    """

    title = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        verbose_name="Урок",
        help_text="Введите название урока",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
        help_text="Введите описание урока",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        verbose_name="Курс",
        related_name="lessons",
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name="Архивный",
    )
    preview = models.ImageField(
        upload_to="aurora/images/lesson/",
        blank=True,
        null=True,
        verbose_name="Превью",
        help_text="Загрузите превью",
    )
    external_link = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Ссылка",
        help_text="Укажите ссылку на материалы видео",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Автор",
        help_text="Укажите автора урока",
        related_name="lessons",
    )
    price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        default=0,
        validators=[MinValueValidator(Decimal(0.00))],  # Цена не может быть меньше 0.00
        verbose_name="Стоимость урока",
        help_text="Введите стоимость урока",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Время последнего обновления"
    )

    class Meta:
        """Настройки отображения модели в административной панели."""

        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def clean(self):
        """Проверка обязательности автора при создании нового урока."""
        super().clean()
        if not self.pk and not self.author:
            raise ValidationError(
                {
                    "author": "При создании нового урока необходимо обязательно указать автора."
                }
            )


class Subscribe(models.Model):
    """Модель подписки пользователя на курс."""

    is_archived = models.BooleanField(
        default=False,
        verbose_name="Архивная",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="subscribes",
        verbose_name="Пользователь",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="subscribes",
        verbose_name="Курс",
    )

    class Meta:
        """Настройка параметров модели."""

        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["-id"]
        # Гарантируем, что связь между юзером и курсом существует в единственном экземпляре
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="unique_user_course_subscribe",
            )
        ]

    def __str__(self):
        return f"{self.user.email} подписан на курс {self.course.title}"
