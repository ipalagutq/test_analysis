# Evals — write-tests

Regression cases. Используются как gate перед патчами SKILL.md.

| ID | Описание | Шаги воспроизведения | Ожидаемый результат | Статус |
|----|----------|----------------------|---------------------|--------|
| TW-001 | Навык должен выбирать тесты по рискам реализации, а не только по типу изменённого файла | Дать spec с завершёнными этапами, diff с domain logic, API client и pipeline wiring | `write-tests` собирает target table, выбирает слои по `test-layer-selection.md`, проверяет матрицу покрытия и sufficiency gate перед commit | active |
