from rest_framework import permissions


class IsModerPermission(permissions.BasePermission):
    """Кастомный класс разрешений для проверки принадлежности к группе модераторов.

    Разрешает доступ к эндпоинту только аутентифицированным пользователям,
    которые состоят в группе с именем 'moder'.
    """
    message = 'Доступ запрещен. Требуются права модератора.'

    def has_permission(self, request, view):
        """Проверяет права доступа пользователя к текущему эндпоинту.

        Args:
            request (HttpRequest): Объект текущего HTTP-запроса.
            view (APIView): Объект Django REST Framework View, к которому идет запрос.

        Returns:
            bool: True, если пользователь аутентифицирован и является модератором,
                  иначе False.
        """
        if not request.user or not request.user.is_authenticated:
            return False

        return request.user.groups.filter(name='moderators').exists()
