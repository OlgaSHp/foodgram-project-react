from django.contrib.auth.models import AbstractUser
from django.db import models

from .users_consts import (EMAIL_MAX_LEN,
                           FIRST_NAME_MAX_LEN,
                           LAST_NAME_MAX_LEN)


class User(AbstractUser):
    """Модель для представления пользователя."""
    email = models.EmailField(
        'Email',
        max_length=EMAIL_MAX_LEN,
        unique=True,)
    first_name = models.CharField(
        'Имя',
        max_length=FIRST_NAME_MAX_LEN)
    last_name = models.CharField(
        'Фамилия',
        max_length=LAST_NAME_MAX_LEN)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_users',
        blank=True,
        help_text='Группа, куда входит пользователь',
        verbose_name='группы',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_users',
        blank=True,
        help_text='Доступ для пользователя',
        verbose_name='виды доступов',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('id',)

    def __str__(self):
        return self.email
