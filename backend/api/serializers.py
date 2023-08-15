import django.contrib.auth.password_validation as validators
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from rest_framework.serializers import (
    Serializer, CharField, EmailField,
    ValidationError)

from .consts import ERROR_MESSAGE

from recipes.models import Ingredients, Recipes, RecipeIngredient, Subscriptions, Tags

User = get_user_model()


class CustomUserLoginSerializer(Serializer):
    """Создает сериализатор для валидации аунтификационных данных на
    URL ".../auth/token/login/"."""

    email = EmailField()
    password = CharField()

    def validate(self, data):
        """Проверяет корректность указанных полей:
            - email;
            - password.
        Возвращает объект пользователя в случае успешной аутентификации."""
        request = self.context.get('request', None)
        
        email: str = data.get('email', None)
        password: str = data.get('password', None)
        if email is None or password is None:
            raise ValidationError('Не указана электронная почта или пароль!')
        if not User.objects.filter(email=email).exists():
            raise ValidationError(
                'Указана неверная электронная почта или пароль!')
        username: str = User.objects.get(email=email).username
        user = authenticate(
            request=request,
            username=username,
            password=password)
        if not user:
            raise ValidationError(
                'Указана неверная электронная почта или пароль!')
        data['user'] = user
        return data


class GetIsSubscribedMixin:

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        return (
            user.follower.filter(author=obj).exists()
            if user.is_authenticated
            else False
        )


class UserListSerializer(
        GetIsSubscribedMixin,
        serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed')


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username',
            'first_name', 'last_name', 'password',)

    def validate_password(self, password):
        validators.validate_password(password)
        return password


class UserPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        label='Новый пароль')
    current_password = serializers.CharField(
        label='Текущий пароль')

    def validate_current_password(self, current_password):
        user = self.context['request'].user
        if not authenticate(
                username=user.email,
                password=current_password):
            raise serializers.ValidationError(
                ERROR_MESSAGE, code='authorization')
        return current_password

    def validate_new_password(self, new_password):
        validators.validate_password(new_password)
        return new_password

    def create(self, validated_data):
        user = self.context['request'].user
        password = make_password(
            validated_data.get('new_password'))
        user.password = password
        user.save()
        return validated_data


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tags
        fields = (
            'id', 'name', 'color', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredients
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id')
    name = serializers.ReadOnlyField(
        source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = (
            'id', 'name', 'measurement_unit', 'amount')


class RecipeUserSerializer(
        GetIsSubscribedMixin,
        serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField(
        read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed')


class IngredientsEditSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredients
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    image = Base64ImageField(
        max_length=None,
        use_url=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tags.objects.all())
    ingredients = IngredientsEditSerializer(
        many=True)

    class Meta:
        model = Recipes
        fields = '__all__'
        read_only_fields = ('author',)

    def validate(self, data):
        ingredients = data['ingredients']
        ingredient_list = []
        for items in ingredients:
            ingredient = get_object_or_404(
                Ingredients, id=items['id'])
            if ingredient in ingredient_list:
                raise serializers.ValidationError(
                    'Ингредиент должен быть уникальным')
            ingredient_list.append(ingredient)
        tags = data['tags']
        if not tags:
            raise serializers.ValidationError(
                'Добавьте тэг для рецепта')
        for tag_name in tags:
            if not Tags.objects.filter(name=tag_name).exists():
                raise serializers.ValidationError(
                    f'Тэга {tag_name} не существует')
        return data

    def validate_cooking_time(self, cooking_time):
        if int(cooking_time) < 1:
            raise serializers.ValidationError(
                'Время приготовления >= 1')
        return cooking_time

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Добавьте Минимум 1 ингредиент в рецепт')
        for ingredient in ingredients:
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(
                    'Количество ингредиентов >= 1!')
        return ingredients

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient.get('id'),
                amount=ingredient.get('amount'), )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipes.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            instance.ingredients.clear()
            self.create_ingredients(ingredients, instance)
        if 'tags' in validated_data:
            instance.tags.set(
                validated_data.pop('tags'))
        return super().update(
            instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context={
                'request': self.context.get('request')
            }).data


class RecipeReadSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    tags = TagSerializer(
        many=True,
        read_only=True)
    author = RecipeUserSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault())
    ingredients = RecipeIngredientSerializer(
        many=True,
        required=True,
        source='recipe')
    is_favorited = serializers.BooleanField(
        read_only=True)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True)

    class Meta:
        model = Recipes
        fields = '__all__'


class SubscribeRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='author.id')
    email = serializers.EmailField(
        source='author.email')
    username = serializers.CharField(
        source='author.username')
    first_name = serializers.CharField(
        source='author.first_name')
    last_name = serializers.CharField(
        source='author.last_name')
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(
        read_only=True)
    recipes_count = serializers.IntegerField(
        read_only=True)

    class Meta:
        model = Subscriptions
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = (
            obj.author.recipe.all()[:int(limit)] if limit
            else obj.author.recipe.all())
        return SubscribeRecipeSerializer(
            recipes,
            many=True).data