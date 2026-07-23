"""Модуль кастомных форм для управления пользователями в админ-панели."""

from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.password_validation import validate_password

from users.models import CustomUser


class CustomUserCreationForm(forms.ModelForm):
    """Кастомная форма для безопасного создания нового пользователя."""

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(),
        help_text="Введите сложный пароль.",
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput(),
        help_text="Повторите введенный пароль.",
    )

    class Meta:
        model = CustomUser
        fields = ("email", "phone_number", "city", "avatar")

    def clean_password2(self):
        """Проверяет совпадение двух паролей."""
        password = self.cleaned_data.get("password")
        password2 = self.cleaned_data.get("password2")

        if password and password2 and password != password2:
            raise forms.ValidationError("Пароли не совпадают.")

        if password:
            validate_password(password)

        return password2

    def save(self, commit=True):
        """Сохраняет пользователя с правильным хэшированием пароля."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Кастомная форма для безопасного редактирования пользователя.

    Наследуется от встроенной UserChangeForm для отображения хэша пароля
    и ссылки на его изменение, но удаляет поле 'username'.
    """

    class Meta:
        model = CustomUser
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Удаляем username из полей формы, так как у нас его нет в модели
        if "username" in self.fields:
            del self.fields["username"]
