from rest_framework import permissions


class IsModerPermission(permissions.BasePermission):
    """Кастомный класс разрешений для проверки принадлежности к группе модераторов.

    Разрешает доступ к эндпоинту только аутентифицированным пользователям,
    которые состоят в группе с именем 'moderators'.
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


class IsOwnerPermission(permissions.BasePermission):
    """Разрешает полный доступ (чтение и редактирование) автору объекта."""
    def has_permission(self, request, view):
        """Проверяет, залогинен ли пользователь."""
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """Проверяет, является ли пользователь владельцем, метод работает кроме эндпоинта list."""
        return obj.author == request.user
