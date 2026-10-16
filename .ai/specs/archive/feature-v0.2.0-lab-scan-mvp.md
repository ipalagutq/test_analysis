# Lab Scan MVP — Specification (v0.2.0)

> **Дата создания:** 2026-10-16
> **Ветка:** `feature/v0.2.0-lab-scan-mvp`
> **Статус:** Завершено
> **Standard:** IEEE 29148:2018 (`validate-requirements-ieee29148`) | Score: 94/100

---

## Workflow выполнения

| Шаг | Действие | Навык | Статус |
| --- | --------- | ----- | ------ |
| а | Создание ТЗ + Ветка | — | ✅ |
| б | Реализация | `implement-spec-stage` | ✅ |
| в | Написание тестов | `write-tests` | ✅ |
| г | Мерж | `integrate-release` | ✅ |
| д | Деплой | `deploy-release` | ⬜ |

## Видение

Первый рабочий релиз Lab Scan Reader, который проходит весь сценарий из `.ai/ARCHITECTURE.md`:

```
upload(scan, patient_id) → extraction (vision-LLM через OpenRouter, JSON-схема)
  → lab_catalog (код, единицы, флаг) → review draft (правка человеком)
  → confirm → patient_card (визит + результаты) → timeline / trends
```

**Пользователь:** демонстратор прототипа (врач, продакт или инвестор на демо). Он выбирает демо-пациента, загружает скан анализа (PDF/JPG/PNG), видит скан рядом с редактируемой таблицей показателей, исправляет сомнительные строки, подтверждает и сразу видит новый визит в карте пациента и на графике тренда.

**Ценность:** убедительно показать, что LLM читает бланк целиком и раскладывает показатели в сопоставимую структуру: канонические коды, единицы, пересчитанный по справочнику флаг. При этом в карту ничего не попадает без подтверждения человеком.

**Результат релиза:** один Docker-контейнер (FastAPI + статический Next.js), который поднимается `docker compose up` и работает в двух режимах экстракции: `openrouter` (реальная модель, выбираемая в env) и `fake` (детерминированные фикстуры, без ключа).

## Архитектурные решения

| # | Вопрос | Решение |
|---|--------|---------|
| Q1 | Один релиз или серия | Один spec v0.2.0, все фичи из ARCHITECTURE.md разбиты на 11 этапов в порядке зависимостей. Каждый этап реализуется отдельной сессией `implement-spec-stage`. |
| Q2 | LLM-провайдер | **OpenRouter** (OpenAI-совместимый API `https://openrouter.ai/api/v1`), клиент — Python-пакет `openai` с `base_url`. Ключ: `OPENROUTER_API_KEY`. Прямой Anthropic SDK не используется; `ANTHROPIC_API_KEY` удаляется из конфигурации (CLAUDE.md, `.env.example`). Решение пользователя: модель должна выбираться самостоятельно. |
| Q3 | Выбор модели | Только через env `OPENROUTER_MODEL` (обязателен при `EXTRACTOR=openrouter`, без значения по умолчанию в коде; пример в `.env.example`). Смена модели требует рестарта. Выбора в UI нет. Идентификатор модели сохраняется в черновике и визите. |
| Q4 | Работа без ключа | Интерфейс `Extractor` с двумя реализациями: `OpenRouterExtractor` и `FakeExtractor`. Выбор через env `EXTRACTOR=openrouter\|fake` (по умолчанию `fake`). Тесты всегда используют `fake`. При `EXTRACTOR=openrouter` без `OPENROUTER_API_KEY` или `OPENROUTER_MODEL` приложение падает при старте с понятной ошибкой конфигурации. |
| Q5 | Передача PDF | Backend растеризует страницы PDF в PNG (`pypdfium2`, 200 dpi, не более `MAX_PDF_PAGES=5` страниц) и отправляет изображения. Это не OCR: модель видит скан целиком, граница IS NOT «нет OCR-движка» соблюдена. Одинаково работает с любой vision-моделью. |
| Q6 | Структурированный ответ | Запрос с `response_format={"type":"json_schema", strict: true}`, схема генерируется из Pydantic-модели `ExtractionResult`. Ответ всегда валидируется Pydantic на сервере. При невалидном JSON — один повтор, затем ошибка `502 extraction_invalid_response`. Флаг нормы от LLM сохраняется как `llm_flag`, итоговый `flag` считается по справочнику. |
| Q7 | Frontend | Next.js + TypeScript, `output: 'export'`. Статику раздаёт FastAPI из того же процесса (`/` → `frontend/out`), API под `/api`. CORS не нужен. Графики — Recharts. Маршруты без динамических сегментов: `/`, `/review?id=`, `/patient?id=`. |
| Q8 | Хранилище | SQLite через SQLAlchemy 2.x, `DATABASE_URL=sqlite:///data/patient_card.db`. Схема создаётся `create_all` при старте, без Alembic (демо). Загруженные файлы и отрендеренные страницы хранятся в `data/uploads/{draft_id}/`. |
| Q9 | Черновик и карта | Черновик (`drafts`) — отдельная таблица со статусом `draft → confirmed \| discarded` и строками в JSON. Таблицы `visits` и `results` пишутся только в транзакции `confirm`. Повторный confirm/discard → `409`. |
| Q10 | Демо-данные | (Вопрос не получил явного ответа, взят рекомендуемый default.) 3 вымышленных пациента, у каждого 2–3 подтверждённых визита в seed. 3 синтетических скана: PDF (ОАК), JPG (биохимия), PNG (смешанный), генерируются скриптом и коммитятся. Плюс фикстуры ответов для `FakeExtractor`. Эндпоинта создания пациентов нет. |
| Q11 | Сопоставление названий | Нормализация строки (lowercase, `ё→е`, удаление пробелов, точек, скобок и дефисов) + точное совпадение со списком синонимов справочника. Fuzzy-matching не делаем. Не распознанная строка остаётся в черновике с `code=null` и `needs_review=true`. |
| Q12 | Нормы | Справочник хранит референсный интервал взрослого в канонической единице: общий `ref` и опциональные `ref_male` / `ref_female`. Флаг: `low` если `value < low`, `high` если `value > high`, иначе `normal`. Если интервала нет — `unknown`. Интервал с бланка (`ref_range`) показывается, но в расчёте не участвует. |
| Q13 | Деплой | Multi-stage `Dockerfile` (node build → python runtime) и `docker-compose.yml` входят в этот релиз. Сам выкат делает шаг ⑤ `deploy-release`. |
| Q14 | Product boundaries | Проверено по `.ai/DECISIONS.md`. Конфликтов с IS NOT нет: нет OCR (Q5), только демо-пациенты (Q10), нет МИС/HL7, нет auth/очередей. OpenRouter покрывается IS «мультимодальная LLM с vision». Новых границ нет. |

## Расширение решений проекта

> Заполняется, если ТЗ расширяет product boundaries (`.ai/DECISIONS.md`).

Расширений нет: границы продукта не меняются. Меняется только технологическая строка в `CLAUDE.md` («Claude (vision)» → «vision-LLM через OpenRouter») — это технологическое решение, а не product boundary.

## Требования

Приоритет по MoSCoW: **M** — Must, **S** — Should.

| ID | Пр. | Требование | Обоснование | Проверка |
|---|---|---|---|---|
| R1 | M | `GET /api/health` возвращает `200 {"status":"ok","version":"0.2.0","extractor":"fake\|openrouter"}`. | Проверка деплоя и режима. | API-тест, `curl` после `docker compose up`. |
| R2 | M | Конфигурация читается из env через `pydantic-settings`: `EXTRACTOR`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `DATABASE_URL`, `UPLOAD_DIR` (default `data/uploads`), `MAX_UPLOAD_MB` (default 10), `MAX_PDF_PAGES` (default 5), `LLM_TIMEOUT_S` (default 120). | Q2–Q4. | Unit-тест Settings: невалидная комбинация вызывает ошибку старта. |
| R3 | M | Справочник `data/lab_catalog.json` содержит от 30 до 50 показателей ОАК и биохимии. У каждого: `code`, `name_ru`, `group` (`cbc`\|`biochem`), `synonyms[]` (≥2, рус + лат/аббревиатура), `unit` (каноническая), `unit_aliases{unit: factor}`, `ref` и/или `ref_male`/`ref_female`. Справочник валидируется Pydantic при загрузке, дубликаты синонимов между кодами — ошибка. | IS DECISIONS, принцип 2. | Unit-тест загрузки, тест на отсутствие дублей. |
| R4 | M | `lab_catalog.match(name_raw) -> code \| None` по правилу Q11. `"Hb"`, `"HGB"`, `"Гемоглобин"` дают `HGB`. | Канонизация. | Unit-тесты по синонимам. |
| R5 | M | `lab_catalog.convert(code, value, unit) -> (value, canonical_unit) \| None` по множителю из `unit_aliases`. Сравнение единиц нечувствительно к регистру и пробелам, `мкмоль/л == µmol/L`. Неизвестная единица — `None`. Минимально: глюкоза (ммоль/л ↔ мг/дл), креатинин (мкмоль/л ↔ мг/дл), гемоглобин (г/л ↔ г/дл), холестерин (ммоль/л ↔ мг/дл). | Сопоставимость визитов. | Unit-тесты с эталонными значениями (погрешность ≤0.01). |
| R6 | M | `lab_catalog.compute_flag(code, value, sex) -> low\|normal\|high\|unknown` по правилу Q12. | Принцип 3. | Unit-тесты на границы интервала. |
| R7 | M | Загрузка принимает только PDF/JPEG/PNG (тип проверяется по magic bytes, а не по расширению), размер ≤ `MAX_UPLOAD_MB`. Иначе `415 unsupported_media_type` / `413 file_too_large`. PDF с числом страниц > `MAX_PDF_PAGES` → `422 too_many_pages`. Изображения уменьшаются до 2000 px по длинной стороне перед отправкой в LLM. | Защита пайплайна и стоимости. | API-тесты на каждый код ошибки. |
| R8 | M | Ответ LLM соответствует `ExtractionResult{items: [ExtractedItem]}`, где `ExtractedItem = {test_name_raw: str, value: float\|null, value_raw: str, unit: str\|null, ref_range: str\|null, flag: "low"\|"normal"\|"high"\|null, confidence: float 0..1, needs_review: bool}`. | ARCHITECTURE: schema-first. | Unit-тест схемы и невалидных payload. |
| R9 | M | `OpenRouterExtractor` отправляет системный промпт + все страницы как `image_url` (data URL base64) в одном запросе, `temperature=0`, таймаут `LLM_TIMEOUT_S`. Ошибки: сеть/таймаут/HTTP ≥400 → `502 extraction_failed`; невалидный JSON после 1 повтора → `502 extraction_invalid_response`. Ключ API не попадает в логи и ответы. | Q2, Q6. | Unit-тест с замоканным HTTP-транспортом (без реальной сети). |
| R10 | M | `FakeExtractor` возвращает фикстуру `data/fixtures/extraction/{sha256(file)}.json`, если она есть, иначе `default.json`. Работает без сети и без ключа. | Q4. | Unit-тест: демо-скан даёт ожидаемые строки. |
| R11 | M | Нормализация превращает каждый `ExtractedItem` в строку черновика `{row_id, test_name_raw, value_raw, value, unit_raw, code, canonical_value, canonical_unit, flag, llm_flag, ref_range_raw, confidence, needs_review, include: true}`. `needs_review=true`, если выполнено хотя бы одно: LLM вернула `needs_review`; `confidence < 0.8`; `code is None`; `value is None`; единица не конвертируется; `llm_flag` не совпадает с `flag` (при `flag != unknown`). | Human-in-the-loop, принцип 3. | Unit-тесты на каждое условие. |
| R12 | M | `POST /api/uploads` (multipart: `file`, `patient_id`) синхронно выполняет растеризацию, экстракцию и нормализацию и создаёт черновик. Ответ `201 {draft_id}`. Неизвестный пациент → `404`. Результаты в `results` при этом не пишутся. | Поток данных. | API-тест: после upload таблица `results` не изменилась. |
| R13 | M | `GET /api/drafts/{id}` → `{id, patient_id, status, model, extractor, page_count, rows[], created_at}`. `GET /api/drafts/{id}/pages/{n}` → PNG страницы `n` (0-based). Для JPG/PNG — одна страница. | Экран review. | API-тесты. |
| R14 | M | `POST /api/drafts/{id}/confirm` с телом `{collected_at: date, rows: [{row_id, code, canonical_value, include}]}` в одной транзакции создаёт `visit` и `results` только для строк с `include=true`. Флаг пересчитывается сервером. Строка с `include=true` без `code` из справочника или без числового значения → `422` с перечнем `row_id`, и ничего не пишется. Статус черновика становится `confirmed`. | Принцип 1. | API-тесты: успех, 422 без частичной записи, повторный confirm → 409. |
| R15 | M | `POST /api/drafts/{id}/discard` переводит черновик в `discarded`. Для не-`draft` → `409`. | Явный отказ. | API-тест. |
| R16 | M | `GET /api/patients` → список демо-пациентов `{id, display_name, sex, birth_year}`. `GET /api/catalog` → `{code, name_ru, unit, group}[]`. | UI-выбор. | API-тесты. |
| R17 | M | `GET /api/patients/{id}/timeline` → визиты по убыванию `collected_at`, каждый с результатами `{code, name_ru, value, unit, flag}`. `GET /api/patients/{id}/trends?code=X` → `{code, unit, ref_low, ref_high, points:[{collected_at, value, flag}]}` по возрастанию даты. Неизвестный код → `404`. | Таймлайн и тренды. | API-тесты на seed-данных. |
| R18 | M | Seed `python -m test_analysis.seed` идемпотентно создаёт 3 вымышленных пациентов (`is_demo=true`) и 2–3 визита у каждого с ≥8 показателями. Повторный запуск не дублирует данные. При старте с пустой БД seed выполняется автоматически. | Тренды на демо (Q10). | Integration-тест: двойной seed даёт те же количества. |
| R19 | M | Скрипт `scripts/generate_demo_scans.py` (Pillow) генерирует `data/samples/cbc_ivanova.pdf`, `data/samples/biochem_petrov.jpg`, `data/samples/mixed_sidorova.png` — бланки-таблицы с вымышленными данными и пометкой «ДЕМО». Для каждого создаётся фикстура `data/fixtures/extraction/{sha256}.json`. Хотя бы в одной фикстуре есть строка с `confidence<0.8` и строка с нераспознаваемым названием. | Демо без ключа, показ review. | Скрипт отрабатывает; `FakeExtractor` находит фикстуры по хэшу. |
| R20 | M | UI `/`: выбор пациента, drag&drop или выбор файла (PDF/JPG/PNG), кнопки «скачать пример» для 3 демо-сканов, индикатор загрузки, показ ошибки API. После успеха — переход на `/review?id={draft_id}`. | IS DECISIONS. | Manual-сценарий + `npm run build`. |
| R21 | M | UI `/review`: слева страницы скана (листание), справа таблица строк. Редактируются `code` (select из каталога), `canonical_value`, `include`. Строки с `needs_review` подсвечены. Флаг показывается после пересчёта на сервере. Поле «дата забора» (default — сегодня). Кнопки «Подтвердить» и «Отклонить». После подтверждения — переход на `/patient?id=`. | Human-in-the-loop. | Manual-сценарий. |
| R22 | M | UI `/patient`: шапка пациента, таймлайн визитов с результатами и цветными флагами, график тренда (Recharts LineChart) с выбором показателя и полосой референсного интервала. | Карта пациента. | Manual-сценарий. |
| R23 | M | На каждой странице UI виден баннер «Демо-прототип. Не медицинское изделие, не для диагностики. Только вымышленные данные.» | IS NOT DECISIONS. | Manual-проверка. |
| R24 | S | Все не-LLM эндпоинты отвечают за ≤500 мс на seed-данных локально. Экстракция в режиме `fake` занимает ≤3 с для 5-страничного PDF. | Скорость демо. | Замер в integration-тесте (`time.perf_counter`). |
| R25 | M | `docker compose up --build` поднимает один сервис `app` на порту 8000 с volume `./data:/app/data`, healthcheck на `/api/health`, env из `.env`. Без `.env` стартует в режиме `fake`. | Деплой (IS DECISIONS). | Manual: `docker compose up`, `curl :8000/api/health`. |

## Этапы реализации

### ✅ Этап 1: Каркас backend и конфигурация

**Файлы:**
- `pyproject.toml` (uv, Python 3.12, `version = "0.1.0"` — до мержа, версию поднимет `integrate-release`; зависимости: fastapi, uvicorn[standard], pydantic>=2, pydantic-settings, sqlalchemy>=2, openai, pypdfium2, pillow, python-multipart; dev: pytest, httpx, ruff)
- `src/test_analysis/__init__.py` (`__version__`)
- `src/test_analysis/config.py`
- `src/test_analysis/main.py`
- `src/test_analysis/api/__init__.py`, `src/test_analysis/api/health.py`
- `.env.example`, `.gitignore` (`.env`, `data/*.db`, `data/uploads/`, `frontend/out`, `frontend/node_modules`)
- `CLAUDE.md` (секции «Технологии», «Конфигурация»: OpenRouter вместо Anthropic), `.ai/ARCHITECTURE.md` (точка входа, LLM через OpenRouter)

**Что делаем:** создаём FastAPI-приложение `app` с роутером `/api` и `Settings` по R2 (валидация комбинации `EXTRACTOR=openrouter` + ключ + модель). Добавляем `GET /api/health` по R1. Общий формат ошибок API: `{"error": code, "detail": str}`.

**Зависимости:** нет.

**Определение готовности:** `uv sync` проходит; `uv run uvicorn test_analysis.main:app` стартует; `curl /api/health` возвращает R1; `uv run ruff check . && uv run ruff format --check .` чисто; при `EXTRACTOR=openrouter` без ключа процесс завершается с сообщением о недостающей переменной.

**Проверка:** smoke-запуск + ruff.

### ✅ Этап 2: Справочник показателей (lab_catalog)

**Файлы:**
- `data/lab_catalog.json`
- `src/test_analysis/lab_catalog/__init__.py`, `models.py`, `catalog.py`
- `src/test_analysis/api/catalog.py` (`GET /api/catalog`)

**Что делаем:** справочник на 30–50 показателей (ОАК: HGB, RBC, WBC, PLT, HCT, MCV, MCH, MCHC, RDW, ESR, NEUT, LYMPH, MONO, EOS, BASO; биохимия: GLU, CREA, UREA, ALT, AST, TBIL, DBIL, CHOL, HDL, LDL, TG, TP, ALB, CRP, ALP, GGT, K, NA, FE, FERR, TSH, HBA1C, URIC, CA, MG) по R3. Функции `match`, `convert`, `compute_flag` по R4–R6. Справочник загружается один раз (lru_cache).

**Зависимости:** Этап 1.

**Определение готовности:** справочник проходит валидацию (30 ≤ N ≤ 50, без дублей синонимов). Примеры из R4/R5 дают ожидаемый результат в REPL. `GET /api/catalog` отдаёт N записей.

**Проверка:** ручной вызов функций + `curl /api/catalog`.

### ✅ Этап 3: Предобработка файла скана

**Файлы:**
- `src/test_analysis/extraction/__init__.py`, `preprocess.py`

**Что делаем:** `preprocess(data: bytes) -> ScanPages{mime, pages: list[bytes PNG]}`. Определение типа по magic bytes, лимиты из R7 (исключения `UnsupportedMediaType`, `FileTooLarge`, `TooManyPages`), растеризация PDF через `pypdfium2` (200 dpi), ресайз до 2000 px, нормализация EXIF-поворота для JPEG.

**Зависимости:** Этап 1.

**Определение готовности:** PDF на 2 страницы → 2 PNG; JPG → 1 PNG ≤2000 px; `.txt`, переименованный в `.pdf`, → `UnsupportedMediaType`.

**Проверка:** ручной прогон на синтетических файлах.

### ✅ Этап 4: Экстракция — схема, OpenRouter и Fake

**Файлы:**
- `src/test_analysis/extraction/schema.py` (`ExtractedItem`, `ExtractionResult`)
- `src/test_analysis/extraction/prompt.py`
- `src/test_analysis/extraction/base.py` (`Extractor` Protocol: `extract(pages) -> ExtractionResult`, свойство `model_id`)
- `src/test_analysis/extraction/openrouter.py`, `fake.py`, `factory.py` (`get_extractor(settings)`)

**Что делаем:** схема по R8. `OpenRouterExtractor` по R9 и Q6: клиент `openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=...)`, `chat.completions.create`, `response_format` json_schema из `ExtractionResult.model_json_schema()`, один повтор при ошибке валидации. Промпт: извлечь все показатели как есть, не переводить единицы, не выдумывать значения, `confidence` — уверенность чтения, `needs_review` — при плохой читаемости. `FakeExtractor` по R10 (принимает исходные байты для хэша, `model_id="fake"`). Исключения `ExtractionFailed`, `ExtractionInvalidResponse`.

**Зависимости:** Этап 3.

**Определение готовности:** `FakeExtractor` возвращает валидный `ExtractionResult` для `default.json`. `OpenRouterExtractor` с подставленным `httpx.MockTransport` корректно разбирает валидный ответ и бросает `ExtractionInvalidResponse` на двух невалидных подряд. В логах нет значения ключа.

**Проверка:** ручной прогон с mock-транспортом. Опционально — реальный вызов при наличии ключа.

### ✅ Этап 5: Нормализация в строки черновика

**Файлы:**
- `src/test_analysis/extraction/normalize.py` (`normalize(result, sex) -> list[DraftRow]`)

**Что делаем:** связываем экстракцию со справочником по R11: `match` → `convert` → `compute_flag`, вычисление `needs_review` по всем шести условиям, `row_id` — порядковый индекс.

**Зависимости:** Этапы 2, 4.

**Определение готовности:** для фикстуры с нераспознанной строкой, строкой с `confidence=0.5`, строкой в мг/дл и строкой с расхождением флага каждая получает ожидаемые `code`, `canonical_value`, `flag`, `needs_review`.

**Проверка:** ручной прогон на фикстуре.

### ✅ Этап 6: Хранилище карты пациента и seed

**Файлы:**
- `src/test_analysis/patient_card/__init__.py`, `db.py` (engine, session, `create_all`), `models.py`, `repository.py`
- `src/test_analysis/seed.py`
- `data/seed/patients.json`

**Что делаем:** модели SQLAlchemy:
- `Patient(id, display_name, sex: M|F, birth_year, is_demo=True)`;
- `Draft(id uuid, patient_id, status, extractor, model, mime, page_count, rows JSON, created_at, decided_at)`;
- `Visit(id, patient_id, collected_at date, draft_id nullable, model, created_at)`;
- `Result(id, visit_id, code, value, unit, flag, test_name_raw)`.

Репозиторий: `create_draft`, `get_draft`, `confirm_draft` (одна транзакция, R14), `discard_draft`, `list_patients`, `timeline`, `trend`. Seed по R18 (вымышленные ФИО с пометкой «(демо)», значения с динамикой, чтобы тренды были видны). Автоматический seed при старте на пустой БД.

**Зависимости:** Этап 2 (коды и флаги в seed считаются через справочник).

**Определение готовности:** после старта с пустой БД — 3 пациента и 7±1 визитов; повторный seed не меняет счётчики; `confirm_draft` с ошибочной строкой не оставляет записей в `visits`/`results`.

**Проверка:** ручной прогон seed + запросы к SQLite.

### ✅ Этап 7: HTTP API пайплайна, ревью и карты

**Файлы:**
- `src/test_analysis/api/uploads.py`, `drafts.py`, `patients.py`, `errors.py`
- `src/test_analysis/main.py` (подключение роутеров, зависимостей, обработчиков ошибок)

**Что делаем:** эндпоинты R12–R17 с маппингом исключений: `UnsupportedMediaType→415`, `FileTooLarge→413`, `TooManyPages→422`, `ExtractionFailed/InvalidResponse→502`, недопустимый статус → `409`, не найдено → `404`. Файл и PNG-страницы сохраняются в `UPLOAD_DIR/{draft_id}/`. В ответе confirm возвращается `{visit_id}`.

**Зависимости:** Этапы 3–6.

**Определение готовности:** в режиме `fake` сценарий через `curl` проходит целиком: `GET /api/patients` → `POST /api/uploads` → `GET /api/drafts/{id}` → `GET .../pages/0` → `POST .../confirm` → `GET /api/patients/{id}/timeline` показывает новый визит → `GET .../trends?code=HGB` содержит новую точку. Каждый код ошибки из R7/R14/R15 воспроизводится.

**Проверка:** ручной curl-сценарий (позже переходит в integration-тест на шаге ③).

### ✅ Этап 8: Демо-сканы и фикстуры Fake-экстрактора

**Файлы:**
- `scripts/generate_demo_scans.py`
- `data/samples/cbc_ivanova.pdf`, `data/samples/biochem_petrov.jpg`, `data/samples/mixed_sidorova.png`
- `data/fixtures/extraction/{sha256}.json` (×3), `data/fixtures/extraction/default.json`
- `src/test_analysis/api/samples.py` (`GET /api/samples`, `GET /api/samples/{name}`)

**Что делаем:** по R19 рисуем бланки (шапка «ДЕМО-ЛАБОРАТОРИЯ», ФИО демо-пациента, таблица «Показатель / Результат / Ед. / Норма») с вариативностью названий (`Hb`, `Гемоглобин`, `ГЛЮ`) и единиц (мг/дл в одном бланке). Фикстуры соответствуют тому, что нарисовано. Скрипт детерминирован (фиксированный шрифт из Pillow, без случайности), чтобы хэши были стабильны. API отдаёт список и файлы примеров для кнопок «скачать пример».

**Зависимости:** Этапы 4, 7.

**Определение готовности:** повторный запуск скрипта даёт побайтно идентичные файлы. Загрузка каждого сэмпла в режиме `fake` возвращает строки из его фикстуры, а не `default.json`.

**Проверка:** `sha256sum` до/после повторной генерации + upload через curl.

### ✅ Этап 9: Frontend — каркас, раздача и экран загрузки

**Файлы:**
- `frontend/package.json`, `next.config.mjs` (`output: 'export'`, `images.unoptimized`), `tsconfig.json`
- `frontend/src/app/layout.tsx` (баннер R23), `frontend/src/app/page.tsx` (загрузка)
- `frontend/src/lib/api.ts` (типизированный клиент `/api`)
- `src/test_analysis/main.py` (монтирование `frontend/out` как StaticFiles с `html=True` после роутов `/api`, если каталог существует)

**Что делаем:** UI `/` по R20. В dev Next проксирует `/api` на `localhost:8000` через `rewrites` (только в dev-режиме, для export не используется).

**Зависимости:** Этапы 7, 8.

**Определение готовности:** `npm run build` создаёт `frontend/out`. При запущенном backend `http://localhost:8000/` показывает экран загрузки. Загрузка сэмпла ведёт на `/review?id=...`. `npm run lint` чисто.

**Проверка:** manual-сценарий в браузере.

### ✅ Этап 10: Frontend — экран проверки (review)

**Файлы:**
- `frontend/src/app/review/page.tsx`
- `frontend/src/components/ScanViewer.tsx`, `ReviewTable.tsx`

**Что делаем:** UI по R21. Таблица хранит правки локально и отправляет в `confirm` только `row_id/code/canonical_value/include`. `422` подсвечивает перечисленные строки. Черновик со статусом не `draft` открывается только для чтения с пометкой статуса.

**Зависимости:** Этап 9.

**Определение готовности:** сценарий «загрузить mixed-сэмпл → исправить код нераспознанной строки → снять include у одной строки → подтвердить» создаёт визит, в котором ровно отмеченные строки. Попытка подтвердить строку без кода показывает ошибку и ничего не пишет.

**Проверка:** manual-сценарий + проверка `timeline` через API.

### ✅ Этап 11: Frontend — карта пациента, Docker и документация

**Файлы:**
- `frontend/src/app/patient/page.tsx`, `frontend/src/components/Timeline.tsx`, `TrendChart.tsx`
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- `README.md` (запуск локально и в Docker, режимы экстракции, выбор модели через `OPENROUTER_MODEL`)
- `.ai/ARCHITECTURE.md` (фактическая структура модулей)

**Что делаем:** UI по R22 (выбор показателя из тех, что есть у пациента; `ReferenceArea` для нормы). Dockerfile: stage `node:20` → `npm ci && npm run build`; stage `python:3.12-slim` + uv → копия `src`, `data/lab_catalog.json`, `data/seed`, `data/samples`, `data/fixtures`, `frontend/out`; `CMD uvicorn test_analysis.main:app --host 0.0.0.0 --port 8000`. Compose по R25.

**Зависимости:** Этапы 9, 10.

**Определение готовности:** `docker compose up --build` на чистом клоне без `.env` поднимает сервис. `curl :8000/api/health` → `extractor: fake`. Полный демо-сценарий (загрузка → ревью → карта → тренд с новой точкой) проходит в браузере на `:8000`.

**Проверка:** manual end-to-end в контейнере.

## Нефункциональные требования и ограничения

- **Безопасность и приватность:** только демо-пациенты, эндпоинта создания пациентов нет. `OPENROUTER_API_KEY` не логируется и не возвращается. `.env` в `.gitignore`. Загруженные файлы хранятся только локально в volume `data/`. Сканы уходят третьей стороне (OpenRouter и провайдер модели) только в режиме `openrouter` — это отмечено в README.
- **Производительность:** R24. Время реальной экстракции зависит от модели и не нормируется. Таймаут `LLM_TIMEOUT_S`.
- **Совместимость:** Python 3.12, Node 20 LTS, современные Chrome/Firefox/Safari (desktop). Мобильная вёрстка не требуется.
- **Качество кода:** `ruff check` и `ruff format` без ошибок, правила `.claude/rules/python-style.md`, `frontend-react.md`, `docker-rules.md`.
- **Тесты:** пишутся на шаге ③ `write-tests` (unit для lab_catalog/extraction/normalize, API и integration для пайплайна в режиме `fake`). Реальная сеть в тестах запрещена.

## Риски и ограничения

| Риск/ограничение | Влияние | Митигация |
|---|---|---|
| Выбранная в OpenRouter модель не поддерживает vision или `json_schema` | Экстракция падает с 502 | Ошибка с понятным `detail`. README перечисляет требования к модели (vision + structured outputs). Серверная Pydantic-валидация не зависит от модели. |
| LLM галлюцинирует значения | Ошибочные данные в карте | Обязательный review, пересчёт флага по справочнику, `needs_review` по 6 условиям (R11). |
| Синхронный upload держит запрос до `LLM_TIMEOUT_S` | Долгое ожидание в UI | Индикатор загрузки, таймаут. Очереди вне скоупа (IS NOT). |
| Точное сопоставление синонимов пропускает редкие написания | Больше ручной работы на review | Строка остаётся с `code=null` и выбирается из select. Синонимы расширяются в справочнике. |
| Нормы взрослого не учитывают возраст и лабораторию | Флаг может отличаться от бланка | Расхождение подсвечивается (`needs_review`), баннер «не для диагностики». |
| SQLite + `create_all` без миграций | Изменение схемы ломает существующую БД | Демо: допустимо пересоздать `data/patient_card.db`. Описано в README. |
| Большой объём релиза (11 этапов) | Долгий цикл до деплоя | Этапы независимо проверяемы и реализуются по одному за сессию. |

## Validation

- **Structural validation:** pass (`validate_spec_structure.py`)
- **Standard validation:** 94/100 (IEEE 29148:2018): S1 38/40 (Singular 3), S2 18/20 (No Duplication 3), S3 20/20, S4 18/20 (No Assumptions 3 — Q10 default)
- **Open questions:** none. Q10 (демо-данные) принят по рекомендуемому default, потому что явного ответа не было; его можно пересмотреть до начала Этапа 6.
