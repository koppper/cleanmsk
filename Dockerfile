# Используем Python 3.8.10
FROM python:3.8.10    

# Устанавливаем рабочую директорию
WORKDIR /code

# Обновляем pip
RUN python -m pip install --upgrade pip

# Копируем файлы с зависимостями
COPY cleanmoskow/requirements.txt /code/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в рабочую директорию
COPY cleanmoskow /code/
RUN mkdir -p /app/logs

# Указываем переменную окружения для Django
ENV DJANGO_SETTINGS_MODULE=cleanmoskow.settings
ENV PYTHONPATH=/code

# Собираем статику
RUN python manage.py collectstatic --noinput

# Запускаем Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8086", "cleanmoskow.wsgi:application"]
