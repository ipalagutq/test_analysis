# Архитектура Lab Scan Reader

## Назначение

Прототип: ИИ читает сканы лабораторных анализов и раскладывает показатели в карту пациента. Скан → vision-LLM → строгий JSON → нормализация по справочнику → проверка человеком → запись в карту → таймлайн и тренды.

## Точка входа

Планируется: `src/test_analysis/main.py` (FastAPI `app`), фронт — `frontend/` (Next.js). Код появится в первом ТЗ.

## Структура модулей

```
src/test_analysis/
├── extraction/     ← скан целиком в vision-LLM, ответ по жёсткой JSON-схеме
├── lab_catalog/    ← 30–50 показателей ОАК/биохимии: коды, синонимы, единицы, нормы
├── patient_card/   ← пациенты, визиты, подтверждённые результаты (SQLite/Postgres)
└── api/            ← upload, review, confirm, patient timeline/trends
frontend/
├── upload          ← drag&drop PDF/JPG/PNG + выбор демо-пациента
├── review          ← скан слева / редактируемая таблица справа
└── patient         ← карта пациента, таймлайн, графики трендов
```

## Ключевые паттерны

- **Один сервис, синхронный пайплайн** — без очередей и микросервисов.
- **Schema-first экстракция** — ответ LLM: массив `{test_name_raw, value, unit, ref_range, flag, confidence, needs_review}`, валидируется Pydantic; невалидный ответ не идёт дальше.
- **Канонизация через справочник** — `"Hb"/"Гемоглобин"/"HGB"` → один код; конверсия единиц; флаг выше/ниже нормы считается по справочнику, а не берётся на веру у LLM.
- **Human-in-the-loop** — черновик результата живёт отдельно от карты; запись только после подтверждения.

## Потоки данных

```
upload(scan, patient_id)
  → extraction: LLM vision → raw JSON → schema validation
  → lab_catalog: map name → code, convert unit, compute flag
  → review draft (UI: edit / confirm)
  → patient_card: persist confirmed results to visit
  → timeline / trend по коду показателя между визитами
```
