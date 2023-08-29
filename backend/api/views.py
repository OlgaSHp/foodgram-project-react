from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Exists, OuterRef, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import (FavoriteRecipe, Ingredients, Recipes, ShoppingCart,
                            Subscriptions, Tags)
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter

from .mixins import GetObjectMixin, PermissionAndPaginationMixin
from .serializers import (CustomUserLoginSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          SubscribeSerializer, TagSerializer,
                          UserCreateSerializer, UserListSerializer,
                          UserPasswordSerializer)


class GetToken(ObtainAuthToken):
    """
    Класс для получения токена авторизации.
    Позволяет пользователям получить токен авторизации на основе
    отправленных ими учетных данных (email и пароль).
    Работает с кастомным сериализатором CustomUserLoginSerializer.
    Возвращает токен авторизации в ответе.

    HTTP методы:
        - POST: Создание токена авторизации.

    URL: /auth/token/login/
    """

    serializer_class = CustomUserLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"auth_token": token.key},
                        status=status.HTTP_201_CREATED)


class UsersViewSet(UserViewSet):
    """
    Класс представления для управления пользователями.

    Разрешено только для аутентифицированных пользователей.

    Поддерживает следующие HTTP методы:
        - GET: Получение списка пользователей (включая подписки).
        - POST: Создание нового пользователя.
        - PUT/PATCH: Обновление данных пользователя.
        - DELETE: Удаление пользователя.

    URL: /users/
    """

    serializer_class = UserListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        Получает список пользователей с информацией о подписках.

        Если пользователь аутентифицирован, возвращает список пользователей,
        а также информацию о том, на каких из них он подписан.
        Если пользователь не аутентифицирован,
        возвращает только список пользователей.

        Возвращает:
            - QuerySet: Список пользователей с информацией о подписках.

        HTTP метод: GET
        """
        return (
            User.objects.annotate(
                is_subscribed=Exists(
                    self.request.user.follower.filter(author=OuterRef("id"))
                )
            ).prefetch_related("follower", "following")
            if self.request.user.is_authenticated
            else User.objects.annotate(is_subscribed=Value(False))
        )

    def get_serializer_class(self):
        """
        Возвращает класс сериализатора в зависимости от метода запроса.

        Возвращает:
            - Класс сериализатора.

        HTTP методы: GET, POST, PUT, PATCH, DELETE
        """
        if self.request.method.lower() == "post":
            return UserCreateSerializer
        return UserListSerializer

    def perform_create(self, serializer):
        """
        Создает нового пользователя.

        Создает нового пользователя на основе данных, полученных из запроса.
        Хеширует пароль перед сохранением.

        Параметры запроса:
            - password (строка): Пароль пользователя.

        HTTP метод: POST
        """
        password = make_password(self.request.data["password"])
        serializer.save(password=password)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """
        Возвращает список подписок текущего пользователя.

        Получает список подписок для текущего аутентифицированного пользователя
        и возвращает его в ответе.

        Возвращает:
            - Response: Список подписок текущего пользователя.

        HTTP метод: GET
        """
        user = request.user
        queryset = Subscriptions.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(pages, many=True,
                                         context={"request": request})
        return self.get_paginated_response(serializer.data)


@api_view(["post"])
def set_password(request):
    """
    Изменение пароля текущего пользователя.

    Метод позволяет аутентифицированному пользователю изменить свой пароль.

    Параметры запроса:
        - new_password (строка): Новый пароль пользователя.
        - сurrent_password (строка): Старый пароль пользователя.

    Возвращает:
        - Response: Сообщение об успешном изменении пароля или ошибку
        с неверными данными.

    HTTP метод: POST
    URL: /auth/users/set_password/
    """
    serializer = UserPasswordSerializer(data=request.data,
                                        context={"request": request})
    if serializer.is_valid(raise_exception=True):
        serializer.save(user=request.user)
        return Response({"message": "Пароль изменен"},
                        status=status.HTTP_201_CREATED)


class AddDeleteSubscription(
    generics.RetrieveDestroyAPIView, generics.ListCreateAPIView
):
    """
    Подписка на авторов и отмена подписки.

    Этот класс предоставляет методы для подписки на авторов и отмены подписки.

    GET:
    Возвращает список авторов, на которых текущий пользователь подписан.

    POST:
    Создает подписку на автора. Подписка невозможна на самого себя
    и на уже подписанного автора.

    DELETE:
    Отменяет подписку на автора.

    HTTP методы: GET, POST, DELETE
    URL: /users/<int:user_id>/subscribe/
    """

    serializer_class = SubscribeSerializer

    def get_queryset(self):
        """
        Возвращает список авторов, на которых текущий пользователь подписан.
        Количество рецептов, опубликованных подписанными авторами,
        также добавляется в запрос.

        :return: QuerySet авторов с дополнительной информацией.
        """
        return (
            self.request.user.follower.select_related("following")
            .prefetch_related("following__recipe")
            .annotate(
                recipes_count=Count("following__recipe"),
                is_subscribed=Value(True),
            )
        )

    def get_object(self):
        """
        Получает объект автора по его ID.

        :return: Объект автора.
        """
        user_id = self.kwargs["user_id"]
        user = get_object_or_404(User, id=user_id)
        self.check_object_permissions(self.request, user)
        return user

    def create(self, request, *args, **kwargs):
        """
        Создает подписку на автора.

        :param request: Запрос пользователя.
        :return: Ответ с данными о созданной подписке.
        """
        instance = self.get_object()
        subscription = request.user.follower.create(author=instance)
        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """
        Отменяет подписку на автора.

        :param instance: Объект автора.
        :return: None
        """
        self.request.user.follower.filter(author=instance).delete()


class AddDeleteFavoriteRecipe(
    GetObjectMixin, generics.RetrieveDestroyAPIView, generics.ListCreateAPIView
):
    """
    Представление для добавления и удаления рецепта в/из избранных.

    Методы:
    - create: Добавляет рецепт в избранные пользователя.
    - perform_destroy: Удаляет рецепт из избранных пользователя.
    """

    def create(self, request, *args, **kwargs):
        """
        Добавляет рецепт в избранные пользователя.

        Параметры:
        - request: Объект запроса.
        Возвращает:
        - Response с сериализованными данными рецепта
        и статусом HTTP 201 Created.
        """
        instance = self.get_object()
        request.user.favorite_recipe.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """
        Удаляет рецепт из избранных пользователя.

        Параметры:
        - instance: Объект рецепта, который нужно удалить.

        Не возвращает значения.
        """
        self.request.user.favorite_recipe.recipe.remove(instance)


class AddDeleteShoppingCart(
    GetObjectMixin, generics.RetrieveDestroyAPIView, generics.ListCreateAPIView
):
    """
    Представление для добавления и удаления рецепта в корзину/из корзины.

    Методы:
    - create: Добавляет рецепт в корзину пользователя.
    - perform_destroy: Удаляет рецепт из корзины пользователя.
    """

    def create(self, request, *args, **kwargs):
        """
        Добавляет рецепт в корзину пользователя.

        Параметры:
        - request: Объект запроса.

        Возвращает:
        - Response с сериализованными данными рецепта и
        статусом HTTP 201 Created.
        """
        instance = self.get_object()
        request.user.shopping_cart.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        """
        Удаляет рецепт из корзины пользователя.

        Параметры:
        - instance: Объект рецепта, который нужно удалить из корзины.

        Не возвращает значения.
        """
        self.request.user.shopping_cart.recipe.remove(instance)


class RecipesViewSet(viewsets.ModelViewSet):
    """
    Представление для работы с рецептами.

    Методы:
    - perform_create: Создание рецепта.
    - get_serializer_class: Определение класса сериализатора в зависимости
    от метода запроса.
    - get_queryset: Получение списка рецептов с аннотациями
    информации о рецепте для аутентифицированных
                    и неаутентифицированных пользователей.
    - download_shopping_cart: Создание PDF-файла
    со списком покупок пользователя.
    """

    queryset = Recipes.objects.all()
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        """
        Получение списка рецептов с аннотациями информации о рецепте.

        Если пользователь аутентифицирован,
        то к рецептам добавляются аннотации:
        - is_favorited: флаг, указывающий,
        добавлен ли рецепт в избранное пользователем.
        - is_in_shopping_cart: флаг, указывающий,
        добавлен ли рецепт в корзину покупок пользователем.

        Если пользователь не аутентифицирован,
        аннотации is_in_shopping_cart и is_favorited будут всегда False.

        Возвращает:
        - QuerySet рецептов с аннотациями в зависимости
        от статуса аутентификации пользователя.
        """
        author_id = self.kwargs.get('author_id')
        queryset = Recipes.objects.all()

        if author_id:
            queryset = queryset.filter(author_id=author_id)
            return queryset
        return (
            Recipes.objects.annotate(
                is_favorited=Exists(
                    FavoriteRecipe.objects.filter(
                        user=self.request.user, recipe=OuterRef("id")
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user, recipe=OuterRef("id")
                    )
                ),
            )
            .select_related("author")
            .prefetch_related(
                "tags",
                "ingredients",
                "recipe",
                "shopping_cart",
                "favorite_recipe",
            )
            if self.request.user.is_authenticated
            else Recipes.objects.annotate(
                is_in_shopping_cart=Value(False),
                is_favorited=Value(False),
            )
            .select_related("author")
            .prefetch_related(
                "tags",
                "ingredients",
                "recipe",
                "shopping_cart",
                "favorite_recipe",
            )
        )

    def perform_create(self, serializer):
        """
        Создание рецепта.

        Параметры:
        - serializer: Сериализатор данных рецепта.

        Не возвращает значения.
        """
        serializer.save(author=self.request.user)

    @action(detail=False, methods=["get"],
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """
        Создание текстового файла с списком покупок пользователя.

        Параметры:
        - request: Объект запроса.

        Возвращает:
        - HttpResponse с текстовым файлом списка покупок пользователя.
        """
        shopping_cart = (
            request.user.shopping_cart.recipe.values(
                "ingredients__name", "ingredients__measurement_unit"
            )
            .annotate(amount=Sum("recipe__amount"))
            .order_by()
        )

        if shopping_cart:
            shopping_list = ["Ваш список покупок:"]
            for index, recipe in enumerate(shopping_cart, start=1):
                shopping_list.append(
                    f'{index}. {recipe["ingredients__name"]} - '
                    f'{recipe["amount"]} '
                    f'{recipe["ingredients__measurement_unit"]}.'
                )

            response = HttpResponse("\n".join(shopping_list),
                                    content_type="text/plain")
            response["Content-Disposition"] = 'attachment;'
            'filename="shopping_list.txt"'
            return response

        return HttpResponse("Список покупок пуст", content_type="text/plain")


class TagsViewSet(PermissionAndPaginationMixin, viewsets.ModelViewSet):
    """
    ViewSet для работы со списком тэгов.

    Параметры:
    - queryset: Запрос для получения списка тэгов.
    - serializer_class: Сериализатор для тэгов.

    Использует PermissionAndPaginationMixin для управления разрешениями
    и пагинацией.
    """

    queryset = Tags.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(PermissionAndPaginationMixin, viewsets.ModelViewSet):
    """
    ViewSet для работы со списком ингредиентов.

    Параметры:
    - queryset: Запрос для получения списка ингредиентов.
    - serializer_class: Сериализатор для ингредиентов.
    - filterset_class: Фильтры для ингредиентов.

    Использует PermissionAndPaginationMixin для управления разрешениями
    и пагинацией.
    """

    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
