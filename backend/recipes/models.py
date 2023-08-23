from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
from django.db.models import (CASCADE, SET_NULL, CharField, DateTimeField,
                              ForeignKey, ImageField, ManyToManyField, Model,
                              OneToOneField, PositiveSmallIntegerField,
                              SlugField, TextField, UniqueConstraint)
from django.db.models.signals import post_save
from django.dispatch import receiver

from .recipes_consts import (HEX_COLOR_VALIDATOR, MAX_LENGTH_COLOR_TAGS,
                             MAX_LENGTH_MEASUREMENT, MAX_LENGTH_NAME_ING,
                             MAX_LENGTH_NAME_RECIPES, MAX_LENGTH_NAME_TAGS,
                             MAX_LENGTH_SLUG_TAGS, TEXT_PREVIEW_LENGTH)


class Ingredients(Model):
    """Модель для представления ингредиентов."""
    name = CharField(
        'Название ингредиента',
        max_length=MAX_LENGTH_NAME_ING)
    measurement_unit = CharField(
        'Единица измерения ингредиента',
        max_length=MAX_LENGTH_MEASUREMENT)

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Tags(Model):
    """Модель для представления тэгов."""
    name = CharField(
        'Название',
        max_length=MAX_LENGTH_NAME_TAGS,
        unique=True)
    color = CharField(
        'Цвет',
        max_length=MAX_LENGTH_COLOR_TAGS,
        validators=[RegexValidator(
            regex=HEX_COLOR_VALIDATOR,
            message='Введите корректный цвет в формате HEX')],
        unique=True)
    slug = SlugField(
        'Ссылка',
        max_length=MAX_LENGTH_SLUG_TAGS,
        unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
        ordering = ['-id']

    def __str__(self):
        return self.name


class Recipes(Model):
    """Модель для представления рецептов."""
    author = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='recipe',
        verbose_name='Автор')
    name = CharField(
        'Название рецепта',
        max_length=MAX_LENGTH_NAME_RECIPES)
    image = ImageField(
        'Фотография рецепта',
        upload_to='recipe/',
        blank=True,
        null=True)
    text = TextField(
        'Описание рецепта')
    ingredients = ManyToManyField(
        Ingredients,
        through='RecipeIngredient')
    tags = ManyToManyField(
        Tags,
        verbose_name='Тэги',
        through='RecipesTags',
        related_name='recipes')
    cooking_time = PositiveSmallIntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[MinValueValidator(
            1, message='Мин. время приготовления 1 минута'), ])
    pub_date = DateTimeField(
        'Дата публикации',
        auto_now_add=True)

    def short_description(self):
        return self.text[:TEXT_PREVIEW_LENGTH]

    short_description.short_description = 'Описание рецепта'

    def __str__(self):
        return f'{self.author.email}, {self.name}'

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', )


class FavoriteRecipe(Model):
    """Модель для представления избранных рецептов."""
    user = OneToOneField(
        User,
        on_delete=CASCADE,
        null=True,
        related_name='favorite_recipe',
        verbose_name='Пользователь')
    recipe = ManyToManyField(
        Recipes,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт')

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self):
        list_ = [item['name'] for item in self.recipe.values('name')]
        return f'Пользователь {self.user} добавил {list_} в избранные.'

    @receiver(post_save, sender=User)
    def create_favorite_recipe(
            sender, instance, created, **kwargs):
        if created:
            return FavoriteRecipe.objects.create(user=instance)


class RecipeIngredient(Model):
    """Модель для представления связи между ингредиентами и рецептами."""
    recipe = ForeignKey(
        Recipes,
        on_delete=CASCADE,
        related_name='recipe')
    ingredient = ForeignKey(
        Ingredients,
        on_delete=CASCADE,
        related_name='ingredient')
    amount = PositiveSmallIntegerField(
        default=1,
        validators=(
            MinValueValidator(
                1, message='Мин. количество ингридиентов 1'),),
        verbose_name='Количество',)

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        ordering = ['-id']
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique ingredient')]

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class RecipesTags(Model):
    """Модель для представления связи между рецептом и тегом."""
    recipe = ForeignKey(
        Recipes,
        null=True,
        on_delete=CASCADE,
        related_name='recipe_tag',
        verbose_name='Рецепт')
    tag = ForeignKey(
        Tags,
        null=True,
        on_delete=SET_NULL,
        related_name='tag_recipe',
        verbose_name='Тэг')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=('recipe', 'tag'),
                name='recipe_tag')]
        ordering = ('recipe', 'tag')

    def __str__(self):
        return f'{self.recipe.name} - {self.tag.name}'

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Subscriptions(Model):
    """Модель для представления подписок пользователей на авторов."""
    user = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='follower',
        verbose_name='Подписчик')
    author = ForeignKey(
        User,
        on_delete=CASCADE,
        related_name='following',
        verbose_name='Автор')
    created = DateTimeField(
        'Дата подписки',
        auto_now_add=True)

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-id']
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription')]

    def __str__(self):
        return f'Пользователь {self.user} подписан на автора {self.author}'


class ShoppingCart(Model):
    """Модель для представления корзины покупок."""
    user = OneToOneField(
        User,
        on_delete=CASCADE,
        related_name='shopping_cart',
        null=True,
        verbose_name='Пользователь')
    recipe = ManyToManyField(
        Recipes,
        related_name='shopping_cart',
        verbose_name='Покупка')

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'
        ordering = ['-id']

    def __str__(self):
        list_ = [item['name'] for item in self.recipe.values('name')]
        return f'Пользователь {self.user} добавил {list_} в покупки.'

    @receiver(post_save, sender=User)
    def create_shopping_cart(
            sender, instance, created, **kwargs):
        if created:
            return ShoppingCart.objects.create(user=instance)
