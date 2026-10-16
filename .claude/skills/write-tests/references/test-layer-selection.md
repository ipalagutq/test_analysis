# Test Layer Selection

Выбирать самый низкий слой, который доказывает поведение без хрупкости. Более высокий слой нужен только когда lower-level тест не видит важный контракт.

## Матрица

| Изменение | Основной слой | Что доказывать | Когда добавить выше |
|---|---|---|---|
| Pure/domain logic, value objects, validators | `tests/unit/` | input/output, invariants, edge cases | Когда доменный объект подключён к pipeline и есть риск неверной сборки |
| Parsing, formatting, serialization | `tests/unit/` | accepted formats, invalid input, stable output | Когда формат является внешним API или файловым артефактом |
| Settings/config/defaults | `tests/unit/` | default, override, invalid config | Когда config влияет на end-to-end route |
| HTTP/API client | `tests/api/` | request shape, response mapping, error mapping, retry/backoff if present | Когда несколько clients участвуют в одном workflow |
| CLI command / service entrypoint | `tests/integration/` | wiring, exit/status, generated artifacts | Когда есть чистая функция — покрыть её unit-тестом отдельно |
| Agent/pipeline flow | `tests/integration/` | step order, state transition, artifacts, rollback/error path | Когда отдельные transforms сложны — добавить unit |
| Import boundary / forbidden dependency | `tests/architecture/` | запрет зависимости между слоями | Когда изменение создаёт новый архитектурный слой |
| Regression for previous bug | Самый низкий воспроизводящий слой | точный сценарий падения | Когда баг проявлялся только через integration path |

## Правила выбора

1. Один риск закрывается одним наиболее точным тестом; не дублировать один assertion на трёх слоях.
2. Mock boundary ставить на внешнем I/O: network, filesystem outside tmp, clock, random, credentials, LLM/API.
3. Integration-тест должен проверять связку, а не подробности чистой функции.
4. Architecture-тест добавлять только для устойчивого правила зависимости, а не для разового импорта.
5. Если существующий тестовый слой уже покрывает contract, расширить его вместо создания нового файла.
