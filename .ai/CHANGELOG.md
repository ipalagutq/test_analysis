# CHANGELOG

## [0.2.1] — 2026-10-16

### Fixed — Workflow validator on main before deploy

`scripts/validate_workflow_state.py --step deploy-release` на `main` без spec теперь печатает `allowed=YES` и `next` на чистом дереве и даёт FAIL с `DIRTY_TREE` при незакоммиченных изменениях — вывод совпадает с exit code.

**Tests:** 215 passed

## [0.2.0] — 2026-10-16

### Added — Lab Scan MVP

Первый рабочий релиз: полный демо-сценарий «скан → vision-LLM → строгий JSON → нормализация по справочнику → проверка человеком → карта пациента → таймлайн и тренды». Запись в карту только после подтверждения; режим `EXTRACTOR=fake` проходит сценарий без ключа API.

**Компоненты:**
- [config.py](../src/test_analysis/config.py), [main.py](../src/test_analysis/main.py): настройки из env/`.env` с отказом старта при `EXTRACTOR=openrouter` без ключа или модели, FastAPI-приложение, единый формат ошибок
- [extraction/](../src/test_analysis/extraction/): предобработка файла (magic bytes, лимиты, растеризация PDF), JSON-схема ответа, `OpenRouterExtractor` (json_schema strict, один повтор) и детерминированный `FakeExtractor`, нормализация в строки черновика
- [lab_catalog/](../src/test_analysis/lab_catalog/): справочник ~40 показателей ОАК и биохимии — синонимы, конверсия единиц, флаг нормы по справочнику
- [patient_card/](../src/test_analysis/patient_card/): SQLite-хранилище пациентов, черновиков, визитов и результатов; идемпотентный seed демо-пациентов
- [api/](../src/test_analysis/api/): health, catalog, patients (timeline/trends), uploads, drafts (confirm/discard), samples
- [frontend/](../frontend/): Next.js — загрузка, экран проверки «скан / таблица», карта пациента с таймлайном и графиком тренда
- `scripts/generate_demo_scans.py`, `Dockerfile`, `docker-compose.yml`: демо-сканы с фикстурами, сборка и запуск одним сервисом

**Tests:** 215 passed

## [0.1.0] — 2026-10-16

### Added — Initial Setup

Начальная настройка проекта Lab Scan Reader.

**Компоненты:**
- Начальная структура проекта
- Workflow: 11 навыков, 2 агента, 5 path-gated rules
- `.ai/ARCHITECTURE.md`, `.ai/DECISIONS.md` — целевая архитектура и границы прототипа
