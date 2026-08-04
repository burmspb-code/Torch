from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Создание кастомной команды моздания группы модераторов."""
    help = 'Создает группу модераторов (moder) с базовыми правами доступа'

    def handle(self, *args, **options):
        # Создаем группу
        group, created = Group.objects.get_or_create(name='moderators')

        if created:
            self.stdout.write(self.style.SUCCESS('Группа "moderators" успешно создана.'))
        else:
            self.stdout.write(self.style.WARNING('Группа "moderators" уже существует.'))

        # Ищем системные права, которые Django создал для моделей приложения aurora.
        permissions = Permission.objects.filter(
            codename__in=[
                'view_course',  # Просмотр курсов
                'change_course',  # Редактирование курсов
                'view_lesson',  # Просмотр уроков
                'change_lesson',  # Редактирование уроков
            ],
            content_type__app_label='aurora'
        )

        # Привязываем права к группе
        group.permissions.set(permissions)

        self.stdout.write(
            self.style.SUCCESS(f'Для группы успешно настроено {permissions.count()} прав.')
        )
