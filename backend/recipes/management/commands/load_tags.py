from django.core.management import BaseCommand
from recipes.models import Tags


class Command(BaseCommand):
    """Загрузка тэгов"""

    def handle(self, *args, **kwargs):
        data = [
            {"name": "Завтрак", "color": "#E26C2D", "slug": "breakfast"},
            {"name": "Обед", "color": "#49B64E", "slug": "dinner"},
            {"name": "Ужин", "color": "#8775D2", "slug": "supper"},
        ]
        Tags.objects.bulk_create(Tags(**tag) for tag in data)
        self.stdout.write(self.style.SUCCESS("Загрузка тэгов прошла успешно"))
