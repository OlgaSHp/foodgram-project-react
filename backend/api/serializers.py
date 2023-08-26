import django.contrib.auth.password_validation as validators
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Ingredients, RecipeIngredient, Recipes,
                            Subscriptions, Tags)
from rest_framework import serializers
from rest_framework.serializers import (CharField, EmailField, Serializer,
                                        ValidationError)

from .api_consts import (COOKING_TIME_ERROR, ERROR_MESSAGE,
                         INGREDIENT_ADD_ERROR, INGREDIENT_AMOUNT_ERROR,
                         MAIL_PASSWORD_MISSING_MESSAGE,
                         REPEAT_INGREDIENT_ERROR, WRONG_MAIL_PASSWORD_MESSAGE)


class CustomUserLoginSerializer(Serializer):
    """
    Сериализатор для входа пользователей.

    Поля:
    - email: EmailField для электронной почты пользователя.
    - password: CharField для пароля пользователя.

    Методы:
    - validate: Проверяет корректность полей email и password.
    """

    email = EmailField()
    password = CharField()

    def validate(self, data):
        """
        Проверяет корректность полей email и password.

        Параметры:
        - data: Словарь данных, содержащий поля email и password.

        Возвращает:
        - Проверенные и обработанные данные.

        Вызывает исключение ValidationError, если поля некорректны.
        """
        request = self.context.get("request", None)

        email = data.get("email", None)
        password = data.get("password", None)
        if email is None or password is None:
            raise ValidationError(MAIL_PASSWORD_MISSING_MESSAGE)
        if not User.objects.filter(email=email).exists():
            raise ValidationError(WRONG_MAIL_PASSWORD_MESSAGE)
        username = User.objects.get(email=email).username
        user = authenticate(request=request,
                            username=username,
                            password=password)
        if not user:
            raise ValidationError(WRONG_MAIL_PASSWORD_MESSAGE)
        data["user"] = user
        return data


class GetIsSubscribedMixin:
    """
    Миксин для получения информации о подписке на пользователя.

    Методы:
    - get_is_subscribed: Возвращает информацию о подписке на пользователя.
    """

    def get_is_subscribed(self, obj):
        """
        Возвращает информацию о подписке на пользователя.

        Параметры:
        - obj: Объект пользователя, на которого проверяется подписка.

        Возвращает:
        - True, если текущий пользователь подписан на объект пользователя,
          иначе False.
        """
        user = self.context["request"].user
        return (
            user.follower.filter(author=obj).exists()
            if user.is_authenticated
            else False
        )


class UserListSerializer(GetIsSubscribedMixin, serializers.ModelSerializer):
    """
    Сериализатор списка пользователей с информацией о подписке.

    Поля:
    - is_subscribed: Поле, указывающее наличие подписки на пользователя.

    Мета-класс:
    - model: Модель User.
    - fields: Список полей, включая 'email', 'id', 'username',
              'first_name', 'last_name' и 'is_subscribed'.
    """

    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name",
                  "last_name", "is_subscribed")


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания пользователя.

    Поля:
    - id: Идентификатор пользователя.
    - email: Адрес электронной почты.
    - username: Имя пользователя (логин).
    - first_name: Имя.
    - last_name: Фамилия.
    - password: Пароль.

    Мета-класс:
    - model: Модель User.
    - fields: Список полей, включая 'id', 'email', 'username',
              'first_name', 'last_name' и 'password'.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )

    def validate_password(self, password):
        """
        Проверяет валидность пароля.

        Параметры:
        - password: Пароль для проверки.

        Возвращает:
        - Валидный пароль.
        """
        validators.validate_password(password)
        return password


class UserPasswordSerializer(serializers.Serializer):
    """
    Сериализатор изменения пароля пользователя.

    Поля:
    - new_password: Новый пароль.
    - current_password: Текущий пароль.
    """

    new_password = serializers.CharField(label="Новый пароль")
    current_password = serializers.CharField(label="Текущий пароль")

    def validate_current_password(self, current_password):
        """
        Проверяет правильность текущего пароля.

        Параметры:
        - current_password: Текущий пароль для проверки.

        Возвращает:
        - Верный текущий пароль.

        Исключения:
        - serializers.ValidationError, если текущий пароль неверен.
        """
        user = self.context["request"].user
        if not authenticate(username=user.email, password=current_password):
            raise serializers.ValidationError(ERROR_MESSAGE,
                                              code="authorization")
        return current_password

    def validate_new_password(self, new_password):
        """
        Проверяет валидность нового пароля.

        Параметры:
        - new_password: Новый пароль для проверки.

        Возвращает:
        - Валидный новый пароль.

        Исключения:
        - serializers.ValidationError, если новый пароль невалиден.
        """
        validators.validate_password(new_password)
        return new_password

    def create(self, validated_data):
        """
        Изменяет пароль пользователя.

        Параметры:
        - validated_data: Проверенные данные с новым паролем.

        Возвращает:
        - validated_data.
        """
        user = self.context["request"].user
        password = make_password(validated_data.get("new_password"))
        user.password = password
        user.save()
        return validated_data


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор тэгов.

    Поля:
    - id: Идентификатор тэга.
    - name: Название тэга.
    - color: Цвет тэга в формате HEX.
    - slug: Ссылка тэга.

    Метаданные:
    - model: Ссылка на модель Tags.
    - fields: Поля, которые будут сериализованы.
    """

    class Meta:
        model = Tags
        fields = (
            "id",
            "name",
            "color",
            "slug",
        )


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор ингредиентов.

    Метаданные:
    - model: Ссылка на модель Ingredients.
    - fields: Все поля модели.
    """

    class Meta:
        model = Ingredients
        fields = "__all__"


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для представления связи между ингредиентами и рецептами.

    Поля:
    - id: Идентификатор ингредиента.
    - name: Название ингредиента.
    - measurement_unit: Единица измерения ингредиента.

    Метаданные:
    - model: Ссылка на модель RecipeIngredient.
    - fields: Поля, которые будут сериализованы.
    """

    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeUserSerializer(GetIsSubscribedMixin, serializers.ModelSerializer):
    """
    Сериализатор пользователя с учетом подписки.

    Поля:
    - email: Адрес электронной почты пользователя.
    - id: Идентификатор пользователя.
    - username: Имя пользователя.
    - first_name: Имя пользователя.
    - last_name: Фамилия пользователя.
    - is_subscribed: Флаг подписки на пользователя.

    Метаданные:
    - model: Ссылка на модель User.
    - fields: Поля, которые будут сериализованы.
    """

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name",
                  "last_name", "is_subscribed")


class IngredientsEditSerializer(serializers.ModelSerializer):
    """
    Сериализатор ингредиентов для редактирования.

    Поля:
    - id: Идентификатор ингредиента.
    - amount: Количество ингредиента.

    Метаданные:
    - model: Ссылка на модель Ingredients.
    - fields: Поля, которые будут сериализованы.
    """

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredients
        fields = ("id", "amount")


class RecipeWriteSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления рецепта.

    Поля:
    - image: Изображение рецепта (в формате Base64).
    - tags: Список связанных тэгов.
    - ingredients: Список ингредиентов.

    Метаданные:
    - model: Ссылка на модель Recipes.
    - fields: Поля, которые будут сериализованы.
    - read_only_fields: Поля только для чтения.
    """

    image = Base64ImageField(max_length=None, use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tags.objects.all()
    )
    ingredients = IngredientsEditSerializer(many=True)

    class Meta:
        model = Recipes
        fields = "__all__"
        read_only_fields = ("author",)

    def validate(self, data):
        """
        Проверяет валидность данных перед созданием или обновлением рецепта.

        Параметры:
        - data: Словарь с данными для создания или обновления рецепта.

        Возвращает:
        - Проверенные данные, если они валидны.

        Генерирует:
        - serializers.ValidationError, если данные невалидны.
        """
        ingredients = data["ingredients"]
        ingredient_list = []
        for items in ingredients:
            ingredient = get_object_or_404(Ingredients, id=items["id"])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    REPEAT_INGREDIENT_ERROR
                )
            ingredient_list.append(ingredient)
        tags = data["tags"]
        if not tags:
            raise serializers.ValidationError("Добавьте тэг для рецепта")
        for tag_name in tags:
            if not Tags.objects.filter(name=tag_name).exists():
                raise serializers.ValidationError(
                    f"Тэга {tag_name} не существует"
                )
        return data

    def validate_cooking_time(self, cooking_time):
        """
        Проверяет корректность времени приготовления.

        Параметры:
        - cooking_time: Время приготовления рецепта.

        Возвращает:
        - cooking_time: Проверенное время приготовления.

        Вызывает исключение serializers.ValidationError,
        если время приготовления некорректное.
        """
        if int(cooking_time) < 1:
            raise serializers.ValidationError(
                COOKING_TIME_ERROR
            )
        return cooking_time

    def validate_ingredients(self, ingredients):
        """
        Проверяет корректность списка ингредиентов.

        Параметры:
        - ingredients: Список ингредиентов рецепта.

        Возвращает:
        - ingredients: Проверенный список ингредиентов.

        Вызывает исключение serializers.ValidationError,
        если ингредиенты некорректные.
        """
        if not ingredients:
            raise serializers.ValidationError(
                INGREDIENT_ADD_ERROR
            )
        for ingredient in ingredients:
            if int(ingredient.get("amount")) < 1:
                raise serializers.ValidationError(
                    INGREDIENT_AMOUNT_ERROR
                )
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        """
        Создает записи о ингредиентах для рецепта.

        Параметры:
        - ingredients: Список ингредиентов рецепта.
        - recipe: Объект рецепта.
        """
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get("id"),
                amount=ingredient.get("amount"),
            )

    def create(self, validated_data):
        """
        Создает новый рецепт.

        Параметры:
        - validated_data: Валидные данные рецепта.

        Возвращает:
        - recipe: Созданный рецепт.
        """
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        recipe = Recipes.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """
        Обновляет существующий рецепт.

        Параметры:
        - instance: Существующий рецепт для обновления.
        - validated_data: Валидные данные рецепта для обновления.

        Возвращает:
        - instance: Обновленный рецепт.
        """
        if "ingredients" in validated_data:
            ingredients = validated_data.pop("ingredients")
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if "tags" in validated_data:
            instance.tags.set(validated_data.pop("tags"))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """
        Преобразует объект рецепта в представление для сериализации.

        Параметры:
        - instance: Объект рецепта.

        Возвращает:
        - data: Представление объекта рецепта.
        """
        return RecipeReadSerializer(
            instance, context={"request": self.context.get("request")}
        ).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения рецепта.

    Поля:
    - image: Изображение рецепта (в формате Base64).
    - tags: Список связанных тэгов.
    - author: Автор рецепта.
    - ingredients: Список ингредиентов.
    - is_favorited: Флаг, показывающий, добавлен ли рецепт в избранное.
    - is_in_shopping_cart: Флаг, показывающий, добавлен ли рецепт в корзину.

    Метаданные:
    - model: Ссылка на модель Recipes.
    - fields: Поля, которые будут сериализованы.
    """
    image = serializers.ReadOnlyField(source='image.url')
    # image = serializers.SerializerMethodField(
    #     "get_image_url",
    #     read_only=True,
    # )
    tags = TagSerializer(many=True, read_only=True)
    author = RecipeUserSerializer(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        source="recipe")
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipes
        fields = "__all__"

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class SubscribeRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка рецептов, на которые подписан пользователь.

    Поля:
    - id: Идентификатор рецепта.
    - name: Название рецепта.
    - image: Изображение рецепта (в формате Base64).
    - cooking_time: Время приготовления рецепта.

    Метаданные:
    - model: Ссылка на модель Recipes.
    - fields: Поля, которые будут сериализованы.
    """

    class Meta:
        model = Recipes
        fields = ("id", "name", "image", "cooking_time")


class SubscribeSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписок пользователя.

    Поля:
    - id: Идентификатор пользователя.
    - email: Адрес электронной почты пользователя.
    - username: Имя пользователя.
    - first_name: Имя пользователя.
    - last_name: Фамилия пользователя.
    - recipes: Список рецептов пользователя.
    - is_subscribed: Флаг, показывающий, подписан ли текущий пользователь на
    другого пользователя.
    - recipes_count: Количество рецептов пользователя.

    Метаданные:
    - model: Ссылка на модель Subscriptions.
    - fields: Поля, которые будут сериализованы.
    """

    id = serializers.IntegerField(source="author.id")
    email = serializers.EmailField(source="author.email")
    username = serializers.CharField(source="author.username")
    first_name = serializers.CharField(source="author.first_name")
    last_name = serializers.CharField(source="author.last_name")
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Subscriptions
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        """
        Возвращает список рецептов, связанных с пользователем,
        на которого подписан текущий пользователь.

        Параметры:
        - obj: Объект подписки пользователя.

        Возвращает:
        - Список рецептов пользователя.
        """
        request = self.context.get("request")
        limit = request.GET.get("recipes_limit")
        recipes = (
            obj.author.recipe.all()[: int(limit)]
            if limit else obj.author.recipe.all()
        )
        return SubscribeRecipeSerializer(recipes, many=True).data
