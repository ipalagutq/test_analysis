# Lab Scan Reader

Прототип: ИИ читает сканы лабораторных анализов (PDF/JPG/PNG) и раскладывает показатели в карту пациента — структурированно, с нормализацией и обязательной проверкой человеком.

---

## Workflow

**За сессию — один шаг.** Перед началом определить текущий шаг.
Основной маршрут использует ТЗ. Параллельный маршрут `small-fix` предназначен только для небольших фиксов без ТЗ и требует постановку задачи в Plan mode.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  plan-release   │────►│implement-spec-stage│────►│ write-tests │────┐
│  ① ТЗ + Ветка   │     │ ② Реализация      │     │ ③ Тесты    │    │
└─────────────────┘     └──────────────────┘     └─────────────┘    │
                                                                     ▼
┌─────────────────┐                                            ┌──────────────────┐     ┌────────────────┐
│  apply-small-fix│───────────────────────────────────────────►│ integrate-release │────►│ deploy-release │
│ F① Plan + Fix   │                                            │  ④ Мерж           │     │ ⑤              │
└─────────────────┘                                            └──────────────────┘     └────────────────┘
```

### Новая фича / крупный багфикс

| Шаг | Навык | ENTRY | EXIT |
| --- | --- | --- | --- |
| ① | plan-release | branch: `main` | `.ai/specs/{type}-v{version}-{slug}.md` создан, ветка `{type}/v{version}-{slug}` |
| ② | implement-spec-stage | spec + ⬜ этапы | все этапы ✅ |
| ③ | write-tests | все ✅ | тесты GREEN |
| ④ | integrate-release | GREEN | branch: `main`, spec в `archive/`, version artifacts синхронизированы |
| ⑤ | deploy-release | `main` + merge | контейнер up |

### Небольшой фикс

| Шаг | Навык | ENTRY | EXIT |
| --- | --- | --- | --- |
| F① | apply-small-fix | Plan mode, branch: `main`, локальный фикс без ТЗ | `fix/{slug}` + commit + проверка |
| ④ | integrate-release | `fix/*`, нет spec, нет uncommitted changes | branch: `main`, CHANGELOG обновлён |
| ⑤ | deploy-release | `main` | контейнер up |

### Правила переходов

1. **Нельзя пропускать шаги внутри выбранного маршрута** — каждый навык проверяет ENTRY
2. **Один шаг за сессию** — после завершения `/clear`
3. **Явный next_skill** — навык указывает следующий шаг
4. **`apply-small-fix` только через Plan mode** — постановка небольшого фикса обязательна в Plan mode
5. **Если навык ошибся** — зафиксировать, исправить, спросить
6. **Каждое ТЗ = новый релиз** — `plan-release` выбирает будущую SemVer-версию `MAJOR.MINOR.PATCH` и использует её в заголовке ТЗ, spec-файле и ветке: `{type}-v{version}-{slug}.md` и `{type}/v{version}-{slug}`
7. **Версия синхронизируется на merge** — `integrate-release` обновляет `.ai/CHANGELOG.md` и все найденные version artifacts проекта (`pyproject.toml`, `package.json`, `VERSION`, `__version__` и аналоги) до версии релиза

### Workflow State Validation

`scripts/validate_workflow_state.py --step {skill}` — ENTRY-проверка declared workflow state. Проверяет маршрут, spec, статусы этапов и version consistency. Не заменяет фактические проверки навыков.

---

## Решения проекта

Все проектные решения и границы — в `.ai/DECISIONS.md`.

---

## Структура

Код ещё не создан — каркас появится в первом ТЗ. Целевая раскладка:

```
test_analysis/
├── CLAUDE.md                ← этот файл
├── pyproject.toml           ← backend (uv), версия релиза
├── src/test_analysis/       ← FastAPI-сервис
│   ├── extraction/          ← вызов vision-LLM + JSON-схема ответа
│   ├── lab_catalog/         ← справочник показателей, синонимы, единицы, нормы
│   ├── patient_card/        ← хранилище: пациенты, визиты, результаты
│   └── api/                 ← HTTP-роуты: загрузка, ревью, карта, тренды
├── tests/                   ← pytest: unit/ + integration/
├── frontend/                ← React/Next.js: загрузка, ревью, карта пациента
├── data/                    ← демо-пациенты, справочник, примеры сканов
├── deploy/                  ← deploy.env.example для VPS
├── scripts/                 ← валидаторы workflow и agent output
├── schemas/agent-output/    ← JSON-схемы выходов субагентов
└── .ai/                     ← ARCHITECTURE, DECISIONS, CHANGELOG, specs/
```

## Технологии

| Технология | Версия | Назначение |
|---|---|---|
| Python | 3.12 | Backend |
| uv | latest | Пакетный менеджер backend |
| FastAPI | — | HTTP-сервис: загрузка → LLM → валидация → нормализация → запись |
| Pydantic | 2.x | JSON-схема ответа LLM и валидация |
| vision-LLM через OpenRouter (`openai` SDK) | — | Чтение скана целиком, без отдельного OCR; модель задаётся `OPENROUTER_MODEL` |
| SQLite / Postgres | — | Карта пациента (SQLite для демо) |
| React / Next.js | — | Веб-UI (npm) |
| pytest, ruff | — | Тесты, форматирование и линтинг |
| Docker Compose | — | Деплой на VPS |

## Конфигурация

`.env` файл (не коммитится):

```env
EXTRACTOR=fake                # fake | openrouter
OPENROUTER_API_KEY=           # обязателен при EXTRACTOR=openrouter
OPENROUTER_MODEL=             # обязателен при EXTRACTOR=openrouter (vision + structured outputs)
DATABASE_URL=sqlite:///data/patient_card.db
UPLOAD_DIR=data/uploads
MAX_UPLOAD_MB=10
MAX_PDF_PAGES=5
LLM_TIMEOUT_S=120
```

Полный пример — `.env.example`. При `EXTRACTOR=openrouter` без ключа или модели сервис не стартует.

---

## Навыки

| Навык | Шаг | Описание |
| --- | --- | --- |
| plan-release | ① | ТЗ по IEEE 29148 с версией релиза + ветка + коммит |
| apply-small-fix | F① | Небольшой фикс без ТЗ, только после постановки в Plan mode |
| implement-spec-stage | ② | Реализация этапов ТЗ |
| write-tests | ③ | Написание тестов |
| integrate-release | ④ | CHANGELOG + синхронизация версии + архив spec + merge |
| deploy-release | ⑤ | Деплой на VPS |
| commit-helper | — | Conventional commits |
| skill-creator | — | Руководство по созданию навыков |
| validate-requirements-ieee29148 | standard | IEEE 29148 валидация ТЗ |
| server-check | — | SSH-диагностика VPS |
| vps-setup | — | Первоначальная настройка VPS |

## Path-gated правила

`.claude/rules/` — инструкции загружаются автоматически при совпадении `paths:` с текущим файлом: python-style, pre-commit, testing-rules, docker-rules, frontend-react.

## Документация

| Документ | Путь | Описание |
| --- | --- | --- |
| Решения | `.ai/DECISIONS.md` | Product boundaries |
| Архитектура | `.ai/ARCHITECTURE.md` | Структура и потоки данных |
| ТЗ | `.ai/specs/` | Технические задания |
| CHANGELOG | `.ai/CHANGELOG.md` | История изменений |

---

> **Один шаг за сессию. После — `/clear`. Каждый навык указывает `next_skill`.**
>
> **Ничего не пишется в карту пациента без подтверждения человеком. Только демо-данные — никаких реальных ПДн.**
