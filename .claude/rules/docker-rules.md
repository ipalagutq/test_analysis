---
paths:
  - "Dockerfile"
  - "docker-compose*.yml"
  - ".dockerignore"
---

# Docker конвенции

## Правила

1. **Базовый образ**: официальные с pin-версией (`python:3.12-slim`, не `python:latest`)
2. **Layers**: минимизировать количество, grouping по частоте изменений
3. **.dockerignore**: всегда включать `.git`, `__pycache__`, `.env`, `.venv`
4. **Compose**: `depends_on` с `condition: service_healthy`
5. **Переменные**: через `.env` файл или `environment:`, не хардкодить
6. **Healthcheck**: обязательный для сервисов, `interval: 30s`
7. **Не использовать**: `latest` теги, `ADD` (использовать `COPY`), привилегированный режим
