# Test Patterns

Перед созданием новых тестов найти ближайший существующий паттерн и продолжить его стиль.

## Поиск паттерна

Искать в таком порядке:

1. Тесты для того же модуля или соседнего модуля.
2. Тесты того же слоя (`unit`, `api`, `integration`, `architecture`).
3. Фикстуры в `tests/conftest.py` и локальных `conftest.py`.
4. Helper factories/builders в `tests/**`.
5. Если паттерна нет — создать минимальный локальный helper в новом test-файле.

## Предпочитаемые формы

| Ситуация | Паттерн |
|---|---|
| Несколько входов одного contract | `pytest.mark.parametrize` |
| Filesystem artifact | `tmp_path`, проверка содержимого |
| Time-dependent behavior | injectable clock или monkeypatch clock provider |
| Network/API client | fake transport, mocked response object, no live request |
| Settings | локальный `Settings`/env override через fixture/monkeypatch |
| Pipeline state | explicit input state + assertion on final state/artifacts |
| Import rule | architecture test с allowlist/denylist |

## Anti-patterns

- Live API в unit/api тесте.
- Sleep вместо контролируемого clock.
- Проверка только “функция была вызвана” без результата.
- Хардкод модели, credential, абсолютного пути пользователя.
- Большая fixture, которая скрывает важные входы конкретного теста.
- Новый тестовый helper, дублирующий уже существующий factory.

## Naming

Имена должны описывать observable behavior:

- `test_returns_empty_report_for_empty_input`
- `test_maps_timeout_to_retryable_error`
- `test_pipeline_writes_stage_status_artifact`

Избегать имён про реализацию:

- `test_calls_private_helper`
- `test_internal_flag_true`
