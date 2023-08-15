# Используем базовый образ для вашего языка программирования (например, Python, Node.js и т.д.)
FROM python:3.9

# Установите все зависимости вашего приложения
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# Копируйте исходный код приложения
COPY . .

# Запустите ваше приложение
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"] 


