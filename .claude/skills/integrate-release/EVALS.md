# Evals — integrate-release

Regression cases. Используются как gate перед патчами SKILL.md.

| ID | Описание | Шаги воспроизведения | Ожидаемый результат | Статус |
|----|----------|----------------------|---------------------|--------|
| MH-001 | Навык должен различать spec и small-fix маршруты перед merge | Запустить integrate-release на ветке со spec, на `fix/*` без spec и на feature ветке без spec | Для spec проверяются этапы и archive, для small-fix archive пропускается, feature без spec получает STOP | active |
| MH-002 | Merge обязан синхронизировать project version artifacts | Запустить integrate-release на spec route с версией `v1.2.3` и найденными `pyproject.toml`, `VERSION` или `__version__` со старой версией | До merge все найденные version artifacts обновлены до `1.2.3`; при конфликте branch/spec/CHANGELOG или пропущенном файле навык получает STOP | active |
