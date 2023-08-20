from django.contrib import admin
from django.contrib.auth import get_user_model

from .users_consts import EMPTY_MESSAGE

User = get_user_model()

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'username', 'email',
        'first_name', 'last_name')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('email', 'username')
    list_display_links = ('username',)
    empty_value_display = EMPTY_MESSAGE
