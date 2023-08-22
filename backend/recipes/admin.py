from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import (FavoriteRecipe, Ingredients, RecipeIngredient, Recipes,
                     RecipesTags, ShoppingCart, Subscriptions, Tags)
from .recipes_consts import EMPTY_MESSAGE, RECIPE_DISPLAY_LIMIT


class RecipeIngredientAdmin(admin.StackedInline):
    model = RecipeIngredient
    autocomplete_fields = ("ingredient",)


class RecipeTagsAdmin(admin.StackedInline):
    model = RecipesTags
    autocomplete_fields = ("tag",)


@admin.register(Recipes)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "get_author_username",
        "get_author_email",
        "name",
        "short_description",
        "cooking_time",
        "get_tags",
        "get_ingredients",
        "get_html_photo",
        "pub_date",
        "get_favorite_count",
    )
    list_display_links = (
        "get_author_email",
        "get_author_username",
        "short_description",
    )
    search_fields = (
        "name",
        "cooking_time",
        "author__email",
        "author__first_name",
        "ingredients__name",
    )
    list_filter = ("author__username", "name", "tags")
    inlines = (RecipeIngredientAdmin, RecipeTagsAdmin)
    empty_value_display = EMPTY_MESSAGE

    def get_html_photo(self, object):
        if object.image:
            return mark_safe(f"<img src='{object.image.url}' width=150")

    get_html_photo.short_description = "Фотография рецепта"

    @admin.display(description="Электронная почта автора")
    def get_author_email(self, obj):
        return obj.author.email

    @admin.display(description="Имя автора")
    def get_author_username(self, obj):
        return obj.author.username

    @admin.display(description="Тэги")
    def get_tags(self, obj):
        list_ = [_.name for _ in obj.tags.all()]
        return ", ".join(list_)

    @admin.display(description=" Ингредиенты ")
    def get_ingredients(self, obj):
        return "\n ".join(
            [
                f'{item["ingredient__name"]} - {item["amount"]}'
                f' {item["ingredient__measurement_unit"]}.'
                for item in obj.recipe.values(
                    "ingredient__name", "amount",
                    "ingredient__measurement_unit"
                )
            ]
        )

    @admin.display(description="В избранном")
    def get_favorite_count(self, obj):
        return obj.favorite_recipe.count()


@admin.register(Tags)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "color",
        "slug",
    )
    list_display_links = ("name",)
    search_fields = (
        "name",
        "slug",
    )
    inlines = (RecipeTagsAdmin,)
    empty_value_display = EMPTY_MESSAGE


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "measurement_unit",
    )
    list_display_links = ("name",)
    search_fields = (
        "name",
        "measurement_unit",
    )
    empty_value_display = EMPTY_MESSAGE


@admin.register(Subscriptions)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "author",
        "created",
    )
    search_fields = (
        "user__email",
        "author__email",
    )
    empty_value_display = EMPTY_MESSAGE


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "get_recipe", "get_count")
    empty_value_display = EMPTY_MESSAGE

    @admin.display(description="Рецепты")
    def get_recipe(self, obj):
        return [
            f'{item["name"]} '
            for item in obj.recipe.values("name")[:RECIPE_DISPLAY_LIMIT]
        ]

    @admin.display(description="В избранном")
    def get_count(self, obj):
        return obj.recipe.count()


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "get_recipe", "get_count")
    empty_value_display = EMPTY_MESSAGE

    @admin.display(description="Рецепты")
    def get_recipe(self, obj):
        return [f'{item["name"]} ' for item in obj.recipe.values("name")[:5]]

    @admin.display(description="В корзине")
    def get_count(self, obj):
        return obj.recipe.count()
