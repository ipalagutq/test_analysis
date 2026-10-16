# Docker Compose Deploy

Docker операции выполняются из `{APP_DIR}/repo`.

## Preferred Flow

```bash
docker compose build
docker compose up -d
```

Если нужна остановка перед запуском, использовать:

```bash
docker compose stop
```

Не использовать `docker compose down` по умолчанию, чтобы не удалять контейнеры/сети/тома без необходимости.

## Compose File

Если проект использует нестандартный compose файл, он должен быть явно описан в конфиге или документации проекта. Не угадывать имя файла.

## Failure Handling

Если build или up не прошли:

- не считать deploy завершённым;
- собрать последние логи, если контейнер успел стартовать;
- перейти к rollback guidance;
- не выполнять destructive cleanups без явного согласия.
