# Архитектура Lab Scan Reader

## Назначение

Прототип: ИИ читает сканы лабораторных анализов и раскладывает показатели в карту пациента. Скан → vision-LLM (через OpenRouter) → строгий JSON → нормализация по справочнику → проверка человеком → запись в карту → таймлайн и тренды.

## Точка входа

`src/test_analysis/main.py` — FastAPI `app` (`create_app()`), все HTTP-роуты под `/api` (`src/test_analysis/api/`). Конфигурация — `src/test_analysis/config.py` (`Settings` на `pydantic-settings`, чтение из env/`.env`, падение при старте на невалидной комбинации). Ошибки API в формате `{"error": code, "detail": str}`. Фронт — `frontend/` (Next.js, статический export, раздаётся тем же процессом).

Запуск: `uv run uvicorn test_analysis.main:app`.

## Структура модулей

```
src/test_analysis/
├── main.py              ← create_app(): роутеры /api, обработчики ошибок, lifespan (create_all + seed), статика frontend/out
├── config.py            ← Settings (pydantic-settings), проверка EXTRACTOR=openrouter
├── seed.py              ← идемпотентный seed демо-пациентов из data/seed/patients.json
├── extraction/
│   ├── preprocess.py    ← magic bytes, лимиты, растеризация PDF (pypdfium2), уменьшение до 2000 px
│   ├── schema.py        ← ExtractionResult / ExtractedItem — JSON-схема ответа LLM
│   ├── prompt.py        ← системный промпт
│   ├── base.py          ← протокол Extractor, ExtractionFailed / ExtractionInvalidResponse
│   ├── openrouter.py    ← OpenRouterExtractor (openai SDK + httpx, json_schema strict, 1 повтор)
│   ├── fake.py          ← FakeExtractor: data/fixtures/extraction/{sha256}.json | default.json
│   ├── factory.py       ← выбор реализации по EXTRACTOR
│   └── normalize.py     ← ExtractedItem → DraftRow (код, конверсия, флаг, needs_review)
├── lab_catalog/
│   ├── models.py        ← LabTest, референсные интервалы
│   └── catalog.py       ← match / convert / compute_flag по data/lab_catalog.json
├── patient_card/
│   ├── db.py            ← engine, sessions, create_schema
│   ├── models.py        ← patients, drafts, visits, results
│   └── repository.py    ← жизненный цикл черновика, confirm, timeline, trend
└── api/                 ← под /api: health, catalog, patients (+timeline/trends), uploads, drafts, samples; errors.py — маппинг ошибок
frontend/src/
├── lib/api.ts           ← единственный типизированный клиент /api
├── app/layout.tsx       ← демо-баннер на всех страницах
├── app/page.tsx         ← / — выбор пациента, загрузка, демо-сканы
├── app/review/page.tsx  ← /review?id= — ScanViewer + ReviewTable, confirm / discard
├── app/patient/page.tsx ← /patient?id= — шапка, TrendChart (Recharts, ReferenceArea нормы), Timeline
└── components/          ← ScanViewer, ReviewTable, Timeline, TrendChart
data/                    ← lab_catalog.json, seed/, samples/, fixtures/ (в git); patient_card.db, uploads/ (runtime)
scripts/generate_demo_scans.py ← детерминированные демо-сканы и фикстуры Fake
```

Все runtime-пути (`data/…`, `frontend/out`) относительны рабочего каталога: процесс запускается из корня репозитория (в контейнере — `WORKDIR /app`).

## Деплой

`Dockerfile` собирается в два этапа: `node:20` выполняет `npm ci && npm run build` → `frontend/out`, затем `python:3.12-slim` + uv ставит зависимости из `uv.lock` (`--no-dev`) и копирует `src`, статические данные и `frontend/out`. `docker-compose.yml` описывает один сервис `app` на порту 8000 с volume `./data:/app/data`, healthcheck `/api/health` и опциональным `.env` (без него работает режим `fake`).

## Ключевые паттерны

- **Один сервис, синхронный пайплайн** — без очередей и микросервисов.
- **Schema-first экстракция** — ответ LLM: массив `{test_name_raw, value, unit, ref_range, flag, confidence, needs_review}`, валидируется Pydantic; невалидный ответ не идёт дальше.
- **Канонизация через справочник** — `"Hb"/"Гемоглобин"/"HGB"` → один код; конверсия единиц; флаг выше/ниже нормы считается по справочнику, а не берётся на веру у LLM.
- **Human-in-the-loop** — черновик результата живёт отдельно от карты; запись только после подтверждения.

## Потоки данных

```
upload(scan, patient_id)
  → extraction: vision-LLM via OpenRouter (EXTRACTOR=openrouter|fake) → raw JSON → schema validation
  → lab_catalog: map name → code, convert unit, compute flag
  → review draft (UI: edit / confirm)
  → patient_card: persist confirmed results to visit
  → timeline / trend по коду показателя между визитами
```
