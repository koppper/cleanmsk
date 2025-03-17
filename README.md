# README: Управление проектом в Docker

Этот файл содержит инструкции по сборке, обновлению кода и выполнению миграций в контейнерах Docker.

## 1. Запуск проекта с нуля

Если проект ещё не запущен или требуется пересобрать контейнеры, выполните команду:

docker-compose up --build -d

### Описание команды:
- `up` – запустить контейнеры.
- `--build` – пересобрать контейнеры перед запуском.
- `-d` – запустить в фоновом режиме (detached mode).

## 2. Обновление кода и перезапуск контейнеров

После внесения изменений в код можно перезапустить контейнеры без пересборки:

docker-compose restart


### Описание команды:
- restart – перезапускает контейнеры без пересборки образов.

Если изменения касаются зависимостей (например, requirements.txt), необходимо пересобрать контейнеры:

docker-compose up --build -d


## 3. Просмотр запущенных контейнеров

Чтобы проверить статус запущенных контейнеров:

docker ps

## 4. Управление миграциями в Django (внутри Docker)

### 4.1. Создание миграций

docker-compose exec django_app python manage.py makemigrations


### 4.2. Применение миграций

docker-compose exec django_app python manage.py migrate


### 4.3. Создание суперпользователя

docker-compose exec django_app python manage.py createsuperuser


## 5. Управление базой данных

### 5.1. Открытие консоли PostgreSQL

docker-compose exec postgres_db psql -U postgres


### 5.2. Бэкап базы данных

docker exec -t postgres_db pg_dump -U postgres -F c -f /backup/db_backup.dump


### 5.3. Восстановление базы данных

docker exec -t postgres_db pg_restore -U postgres -d database_name /backup/db_backup.dump


## 6. Остановка контейнеров

docker-compose down


## 7. Очистка контейнеров и образов

Если нужно очистить все контейнеры, сети и тома:

docker-compose down -v


Удаление всех неиспользуемых образов Docker:

docker system prune -a
