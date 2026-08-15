"""Тестирование приложения aurora."""

from django.urls import reverse
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.test import APITestCase

from aurora.models import Course, Lesson
from users.models import CustomUser


class LessonTestsCase(APITestCase):
    """Тестирование работы эндпоинтов уроков."""

    def setUp(self):

        # Создаем суперпользователя
        self.super_user = CustomUser.objects.create_superuser(email="admin")

        # Создаем обычного пользователя
        self.user = CustomUser.objects.create_user(email="test@example.com")

        # Создаем группу для модераторов
        group_moder, _ = Group.objects.get_or_create(name="moderators")

        # Создаем модератора
        self.user_moderator = CustomUser.objects.create_user(email="test_1@example.com")
        self.user_moderator.groups.add(group_moder)

        # Создаем пользователя автора урока
        self.user_owner = CustomUser.objects.create_user(email="test_2@example.com")

        # Создаем курс
        self.course = Course.objects.create(title="Питон", author=self.user_owner)

        # Создаем урок
        self.lesson = Lesson.objects.create(
            title="Циклы", course=self.course, author=self.user_owner
        )

    def test_lesson_detail(self):
        """Тестирование просмотра урока обычным пользователем, автором и модератором."""
        url = reverse("aurora:lesson_detail", args=[self.lesson.pk])

        # Проверяем, что обычный пользователь не может посмотреть чужой урок
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(
            user=None
        )  # Очистка при переходе к другому пользователю

        # Проверяем, что автор может посмотреть свой урок + валидация данных
        self.client.force_authenticate(user=self.user_owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["title"], self.lesson.title)
        self.assertEqual(response.data["course"], self.lesson.course.id)
        self.assertEqual(response.data["author"], self.user_owner.id)

        self.client.force_authenticate(
            user=None
        )  # Очистка при переходе к другому пользователю

        # Проверяем, что модератор может посмотреть урок + валидация данных
        self.client.force_authenticate(user=self.user_moderator)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["title"], self.lesson.title)
        self.assertEqual(response.data["course"], self.lesson.course.id)
        self.assertEqual(response.data["author"], self.user_owner.id)

    def test_lesson_update(self):
        """Тестирование обновления урока обычным пользователем, автором и модератором."""
        url = reverse("aurora:lesson_update", args=[self.lesson.pk])

        update_data = {"title": "Списки"}

        # Проверяем, что обычный пользователь не может редактировать чужой урок
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(url, data=update_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=None)  # Очистка

        # Проверяем, что автор может редактировать свой урок
        self.client.force_authenticate(user=self.user_owner)
        response = self.client.patch(url, data=update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Валидация ответа сервера:
        self.assertEqual(response.data["title"], update_data["title"])

        # Валидация базы данных:
        self.lesson.refresh_from_db()  # Подтягиваем изменения из БД
        self.assertEqual(self.lesson.title, "Списки")

        self.client.force_authenticate(user=None)  # Очистка

        update_data_1 = {"title": "Списки_1"}

        # Проверяем, что модератор может редактировать урок
        self.client.force_authenticate(user=self.user_moderator)
        # ИСПРАВЛЕНО: передаем именно update_data_1
        response = self.client.patch(url, data=update_data_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Валидация ответа сервера:
        self.assertEqual(response.data["title"], update_data_1["title"])

        # Валидация базы данных:
        self.lesson.refresh_from_db()  # Снова подтягиваем свежие изменения
        self.assertEqual(self.lesson.title, "Списки_1")

    def test_lesson_delete(self):
        """Тестирование удаления урока обычным пользователем, автором и модератором."""
        url = reverse("aurora:lesson_delete", args=[self.lesson.pk])

        # Проверяем, что обычный пользователь не может удалить чужой урок
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(
            user=None
        )  # Очистка при переходе к другому пользователю

        # Проверяем, что автор не может удалить свой урок
        self.client.force_authenticate(user=self.user_owner)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(
            user=None
        )  # Очистка при переходе к другому пользователю

        # Проверяем, что модератор не может удалить урок
        self.client.force_authenticate(user=self.user_moderator)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(
            user=None
        )  # Очистка при переходе к другому пользователю

        # Проверяем, что администратор может удалить урок
        self.client.force_authenticate(user=self.super_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_lesson_create(self):
        """Тестирование создания урока обычным пользователем и модератором."""
        url = reverse("aurora:lesson_create")

        new_data = {
            "title": "Новый урок",
            "course": self.course.pk,
        }

        # Проверяем, что обычный пользователь может создать урок
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data=new_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Валидация ответа сервера:
        self.assertEqual(response.data["title"], "Новый урок")
        self.assertEqual(response.data["course"], self.course.pk)

        # Валидация базы данных
        created_lesson = Lesson.objects.filter(title="Новый урок").first()
        self.assertIsNotNone(created_lesson)  # Проверяем, что такой объект существует
        self.assertEqual(
            created_lesson.course.pk, self.course.pk
        )  # Проверяем связь с курсом

        self.client.force_authenticate(
            user=None
        )  # Очистка при переходе к другому пользователю

        # Проверяем, что модератор не может создать урок
        self.client.force_authenticate(user=self.user_moderator)
        response = self.client.post(url, data=new_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lessons_list(self):
        """Тестирование просмотра списка уроков."""
        url = reverse("aurora:lesson_list")

        # Проверяем, что не авторизованный пользователь не может посмотреть список уроков
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Проверяем, что авторизованный пользователь может посмотреть список уроков
        self.client.force_authenticate(user=self.user_owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # ВАЛИДАЦИЯ ДАННЫХ ДЛЯ АВТОРА:
        self.assertIn("results", response.data)  # Проверяем наличие ключа пагинации
        self.assertEqual(response.data["count"], 1)  # В setUp создан ровно 1 урок
        # Проверяем, что в списке вернулся именно наш урок из setUp
        self.assertEqual(response.data["results"][0]["title"], self.lesson.title)

        self.client.force_authenticate(
            user=None
        )  # Очистка при переходе к другому пользователю

        # Проверяем, что модератор может посмотреть список уроков
        self.client.force_authenticate(user=self.user_moderator)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # ВАЛИДАЦИЯ ДАННЫХ ДЛЯ МОДЕРАТОРА:
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], self.lesson.title)

    def test_subscription_management(self):
        """Тестирование оформления подписки."""
        url = reverse("aurora:course_subscribe", args=[self.course.pk])

        # Проверяем, что не авторизованный пользователь не может оформитьь подписку
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Проверяем, что авторизованный пользователь может офрмить подписку
        self.client.force_authenticate(user=self.user_owner)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
