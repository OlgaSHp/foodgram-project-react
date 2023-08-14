from django.urls import include, path
from rest_framework.routers import DefaultRouter
from djoser.views import TokenDestroyView, UserViewSet

from api.views import (AddAndDeleteSubscribe, AddDeleteFavoriteRecipe,
                       AddDeleteShoppingCart, GetToken, IngredientsViewSet,
                       RecipesViewSet, TagsViewSet, UsersViewSet)

app_name = 'api'

router = DefaultRouter()
router.register('users', UsersViewSet)
router.register('tags', TagsViewSet)
router.register('ingredients', IngredientsViewSet)
router.register('recipes', RecipesViewSet)


urlpatterns = [
     path(
          'auth/token/login/',
          GetToken.as_view(),
          name='login'),
     path(
         'logout/',
         TokenDestroyView.as_view(),
         name='token_destroy'),
     path(
         'users/set_password/',
         UserViewSet.as_view({'post': 'set_password'}),
         name='set_password'),
     path(
          'users/<int:user_id>/subscribe/',
          AddAndDeleteSubscribe.as_view(),
          name='subscribe'),
     path(
          'recipes/<int:recipe_id>/favorite/',
          AddDeleteFavoriteRecipe.as_view(),
          name='favorite_recipe'),
     path(
          'recipes/<int:recipe_id>/shopping_cart/',
          AddDeleteShoppingCart.as_view(),
          name='shopping_cart'),
     path('', include(router.urls)),
     path('auth/', include('djoser.urls')),
     path('auth/', include('djoser.urls.authtoken')),
]
