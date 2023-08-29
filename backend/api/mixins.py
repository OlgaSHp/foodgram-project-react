from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny

from recipes.models import Recipes
from .permissions import IsAdminOrReadOnly
from .serializers import SubscribeRecipeSerializer


class GetObjectMixin:
    """
    Миксин для получения объекта рецепта.

    Поля:
    - serializer_class: Класс сериализатора для объекта.
    - permission_classes: Классы разрешений для доступа к объекту.
    """

    serializer_class = SubscribeRecipeSerializer
    permission_classes = (AllowAny,)

    def get_object(self):
        """
        Получает объект рецепта по его идентификатору.

        Возвращает:
        - Объект рецепта.
        """
        recipe_id = self.kwargs["recipe_id"]
        recipe = get_object_or_404(Recipes, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe


class PermissionAndPaginationMixin:
    """
    Миксин для установки разрешений и типа пагинации.

    Поля:
    - permission_classes: Классы разрешений для доступа к списку объектов.
    - pagination_class: Класс пагинации для списка объектов.

    Примечание:
    Данный миксин предназначен для использования в viewsets и
    предоставляет возможность
    определения разрешений и пагинации для списка объектов.
    """

    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None
