# Evals — deploy-release

Regression cases. Используются как gate перед патчами SKILL.md.

| ID | Описание | Шаги воспроизведения | Ожидаемый результат | Статус |
|----|----------|----------------------|---------------------|--------|
| DP-001 | Навык должен валидировать конфиг и health перед успешным deploy-отчётом | Запустить deploy-release с отсутствующим ключом config, затем с compose output содержащим Traceback/exited | Deploy останавливается на config/health gate, не сообщает успех и предлагает vps-setup или rollback/server-check | active |
