from django.contrib import admin

from .models import (FavoriteRecipe, Ingredients, Recipes, RecipeIngredient,
                     ShoppingCart, Subscriptions, Tags, RecipesTags)

EMPTY_MSG = '-пусто-'


class RecipeIngredientAdmin(admin.StackedInline):
    model =  RecipeIngredient
    autocomplete_fields = ('ingredient',)


class RecipeTagsAdmin(admin.StackedInline):
    model = RecipesTags
    autocomplete_fields = ('tag',)


@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'cooking_time', 'author')
    list_filter = ('name', 'author', 'tags')
    readonly_fields = ('get_favorites_count',)

    def get_favorites_count(self, obj):
        """Возвращает количество пользователей, которые в настоящий момент
        имеют рецепт в избранном."""
        return FavoriteRecipe.objects.filter(recipe=obj).count()

    """Меняет отображение поля в админ-зоне."""
    get_favorites_count.short_description = 'Добавлено в избранное раз'


@admin.register(Tags)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'color', 'slug',)
    search_fields = ('name', 'slug',)
    inlines = (RecipeTagsAdmin,)
    empty_value_display = EMPTY_MSG


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'measurement_unit',)
    search_fields = (
        'name', 'measurement_unit',)
    list_filter = ('name',)


@admin.register(Subscriptions)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'author', 'created',)
    search_fields = (
        'user__email', 'author__email',)
    empty_value_display = EMPTY_MSG


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'get_recipe', 'get_count')
    empty_value_display = EMPTY_MSG

    @admin.display(
        description='Рецепты')
    def get_recipe(self, obj):
        return [
            f'{item["name"]} ' for item in obj.recipe.values('name')[:5]]

    @admin.display(
        description='В избранных')
    def get_count(self, obj):
        return obj.recipe.count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'get_recipe', 'get_count')
    empty_value_display = EMPTY_MSG

    @admin.display(description='Рецепты')
    def get_recipe(self, obj):
        return [
            f'{item["name"]} ' for item in obj.recipe.values('name')[:5]]

    @admin.display(description='В избранных')
    def get_count(self, obj):
        return obj.recipe.count()
