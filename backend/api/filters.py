import django_filters as filters
from django.core.exceptions import ValidationError

from recipes.models import Ingredients, Recipes
from users.models import User


class TagsMultipleChoiceField(filters.fields.MultipleChoiceField):
    """
    Пользовательское поле выбора нескольких тегов.

    Поля:
    - self.required: Поле обязательное для заполнения.
    - self.error_messages: Словарь с сообщениями об ошибках.
    """

    def validate(self, value):
        """
        Проверяет выбранные значения на валидность.

        Параметры:
        - value: Выбранные значения.

        Исключения:
        - ValidationError: Выбранные значения невалидны.

        Возвращает:
        - None
        """
        if self.required and not value:
            raise ValidationError(self.error_messages["required"],
                                  code="required")
        for val in value:
            if val in self.choices and not self.valid_value(val):
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": val},
                )


class TagsFilter(filters.AllValuesMultipleFilter):
    """
    Фильтр для тегов.

    Поля:
    - field_class: Класс для поля выбора нескольких значений.

    Примечание:
    Данный фильтр предназначен для использования вместе с
    дополнительным полем TagsMultipleChoiceField.
    """

    field_class = TagsMultipleChoiceField


class IngredientFilter(filters.FilterSet):
    """
    Фильтр для ингредиентов.

    Поля:
    - name: Фильтр по имени ингредиента.

    Метаданные:
    - model: Ссылка на модель Ingredients.
    - fields: Поля для фильтрации.
    """

    name = filters.CharFilter(lookup_expr="istartswith")

    class Meta:
        model = Ingredients
        fields = ("name",)


class RecipeFilter(filters.FilterSet):
    """
    Фильтр для рецептов.

    Поля:
    - author: Фильтр по автору рецепта.
    - is_in_shopping_cart: Фильтр по наличию в корзине.
    - is_favorited: Фильтр по наличию в избранных.
    - tags: Фильтр по тегам.

    Метаданные:
    - model: Ссылка на модель Recipes.
    - fields: Поля для фильтрации.
    """

    author = filters.ModelChoiceFilter(queryset=User.objects.all())
    is_in_shopping_cart = filters.BooleanFilter(
        widget=filters.widgets.BooleanWidget(), label="В корзине."
    )
    is_favorited = filters.BooleanFilter(
        widget=filters.widgets.BooleanWidget(), label="В избранных."
    )
    tags = filters.AllValuesMultipleFilter(field_name="tags__slug",
                                           label="Ссылка")

    class Meta:
        model = Recipes
        fields = ["is_favorited", "is_in_shopping_cart", "author", "tags"]
