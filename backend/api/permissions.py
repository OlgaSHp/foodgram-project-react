from rest_framework import permissions


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    """
    Правило разрешения доступа на основе авторства или статуса администратора.
    Позволяет автору изменять и удалять объект,
    администраторам - любые действия,
    другим пользователям - только безопасные (GET, HEAD, OPTIONS).
    """

    def has_object_permission(self, request, view, obj):
        """
        Проверяет, имеет ли пользователь разрешение на доступ к объекту.

        Параметры:
        - request: Объект запроса.
        - view: Объект представления.
        - obj: Объект, к которому выполняется запрос.

        Возвращает:
        - bool: True, если пользователь имеет разрешение, иначе False.
        """
        return (
            obj.author == request.user
            or request.method in permissions.SAFE_METHODS
            or request.user.is_superuser
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Правило разрешения доступа для администраторов или
    в режиме только для чтения.
    Позволяет администраторам выполнять любые действия, всем пользователям -
    только безопасные (GET, HEAD, OPTIONS).
    """

    def has_permission(self, request, view):
        """
        Проверяет, имеет ли пользователь разрешение на доступ к представлению.

        Параметры:
        - request: Объект запроса.
        - view: Объект представления.

        Возвращает:
        - bool: True, если пользователь имеет разрешение, иначе False.
        """
        return request.method in permissions.SAFE_METHODS or \
            request.user.is_staff
