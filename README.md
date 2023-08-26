# Проект Продуктовый помощник Foodgram

## Информация о проекте

Сайт, на котором пользователи могут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также доступен сервис «Список покупок». Он позволяет создавать и скачивать список продуктов, которые нужно купить для приготовления выбранных блюд.

** Основные возможности: **

* Создание аккаунтов
* Публикация рецептов с фотографиями
* Подписка на авторов рецептов
* Добавление рецепта в избранное и список покупок
* Фильтрация рецептов по тэгам

## Технологии 

* Python
* Django
* Django Rest Framework 
* PostgreSQL
* JavaScript 
* React
* Ubuntu
* Gunicorn
* Nginx
* Docker
* Dockerhub

## Запуск проекта локально

### Клонируйте репозиторий

```bash
git@github.com:OlgaSHp/foodgram-project-react.git
```

###  Создайте файл .env с тестовыми переменными

```bash
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DB_HOST=
DB_PORT=5432
DJANGO_SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=
```


## Подготовка backend:

```bash
cd backend
python3 -m venv venv
```

# Linux/macOS:

```bash
  source env/bin/activate
```
# Windows:

```bash
  source env/Scripts/activate
```


## Установите зависимости, примените миграции, создайте суперюзера

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
python manage.py createsuperuser
```
При успешном старте backend приложение ответит по адресу 127.0.0.1:8000

## При желании дообавьте тестовые данные

```bash
python manage.py load_db_ingredients.py
python manage.py load_tags.py
```

## Запуск проекта на сервере

Подключитесь к серверу
```bash
ssh user_name@server_ip
```

Установите докер
```bash
sudo apt update
sudo apt upgrade
sudo apt install docker.io
```

Скопируйте 2 файла в домашний каталог
```bash
nginx.conf из папки gateway
docker-compose.production.yml
```

Выполните команды
```bash
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_db_ingredients.py
sudo docker compose -f docker-compose.production.yml exec backend python manage.py load_tags.py
```

Проект доступен по адресу:
```bash
foodgramplatform.ddns.net
логин администратора - root
пароль администратора - admin123
```