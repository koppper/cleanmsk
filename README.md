# README: Управление проектом в Docker

## 1. Запуск проекта с нуля
Если проект ещё не запущен или требуется пересобрать контейнеры, выполните команду:
docker-compose up --build -d


## 2. Обновление кода и перезапуск контейнеров
docker-compose restart


### 3. Бэкап базы данных
docker exec -i postgres_db2 psql -U cleanmoskow2 -d cleanmoskow2 < backups/cleanmoskow_dump.sql
