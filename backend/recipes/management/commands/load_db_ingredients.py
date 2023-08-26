import csv

from django.core.management import BaseCommand

from recipes.models import Ingredients


class Command(BaseCommand):
    help = "Загрузка из csv файла"

    def handle(self, *args, **kwargs):
        data_path = "app/recipes/management/commands"
        with open(
            f"{data_path}/ingredients.csv", "r", encoding="utf-8"
        ) as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            ingredients_to_create = [
                Ingredients(name=row[0], measurement_unit=row[1])
                for row in reader
            ]
            Ingredients.objects.bulk_create(ingredients_to_create)
        self.stdout.write(
            self.style.SUCCESS("Загрузка ингредиентов прошла успешно")
        )
