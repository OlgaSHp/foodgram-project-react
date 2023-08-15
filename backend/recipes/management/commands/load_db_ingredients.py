import csv
import os

from django.core.management import BaseCommand
from recipes.models import Ingredients
data_path = os.path.dirname(os.path.abspath(__file__))



class Command(BaseCommand):
    help = 'Загрузка из csv файла'

    def handle(self, *args, **kwargs):
        data_path = '/app/recipes/management/commands'
        with open(
            f'{data_path}/ingredients.csv',
            'r',
            encoding='utf-8'
        ) as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            for row in reader:
                name, measurement_unit = row
                Ingredients.objects.create(
                    name=name,
                    measurement_unit=measurement_unit
                )
        self.stdout.write(self.style.SUCCESS('Загрузка ингредиентов прошла успешно'))
