"""Тестирование приложения aurora."""

from django.urls import reverse
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APITestCase

from aurora.models import Course, Lesson
from users.models import CustomUser


class LessonTestsCase(APITestCase):

    def setUp(self):

        # Создаем суперпользователя
        self.super_user = CustomUser.objects.create_superuser(email="admin")

        # Создаем обычного пользователя
        self.user = CustomUser.objects.create_user(email='test@example.com')

        # Создаем группу для модераторов
        group_moder, _ = Group.objects.get_or_create(name='moderators')

        # Создаем модератора
        self.user_moderator = CustomUser.objects.create_user(email='test_1@example.com')
        self.user_moderator.groups.add(group_moder)

        # Создаем пользователя автора урока
        self.user_owner = CustomUser.objects.create_user(email='test_2@example.com')

        # Создаем курс
        self.course = Course.objects.create(title='Питон', author=self.user_owner)

        # Создаем урок
        self.lesson = Lesson.objects.create(title='Циклы', course=self.course, author=self.user_owner)

    def test_lesson_detail(self):
        """Тестирование просмотра урока обычным пользователем, автором и модератором."""
        url = reverse("aurora:lesson_detail", args=[self.lesson.pk])

        # Проверяем, что обычный пользователь не может посмотреть чужой урок
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что автор может посмотреть свой урок
        self.client.force_authenticate(user=self.user_owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что модератор может посмотреть урок
        self.client.force_authenticate(user=self.user_moderator)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_lesson_update(self):
        """Тестирование обновления урока обычным пользователем, автором и модератором."""
        url = reverse("aurora:lesson_update", args=[self.lesson.pk])

        update_data = {
            "title":"Списки"
        }

        # Проверяем, что обычный пользователь не может редактировать чужой урок
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(url, data=update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что автор может редактировать свой урок
        self.client.force_authenticate(user=self.user_owner)
        response = self.client.patch(url, data=update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что модератор может редактировать урок
        self.client.force_authenticate(user=self.user_moderator)
        response = self.client.patch(url, data=update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_lesson_delete(self):
        """Тестирование удаления урока обычным пользователем, автором и модератором."""
        url = reverse("aurora:lesson_delete", args=[self.lesson.pk])

        # Проверяем, что обычный пользователь не может удалить чужой урок
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что автор не может удалить свой урок
        self.client.force_authenticate(user=self.user_owner)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что модератор не может удалить урок
        self.client.force_authenticate(user=self.user_moderator)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Проверяем, что администратор может удалить урок
        self.client.force_authenticate(user=self.super_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
