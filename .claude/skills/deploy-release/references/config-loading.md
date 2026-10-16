# Config Loading — deploy-release

`deploy/deploy.env` задаёт, куда и как выполняется deploy. Секретные значения не выводить полностью в отчётах.

## Required Keys

| Key | Назначение |
|---|---|
| `VPS_HOST` | hostname или IP сервера |
| `VPS_USER` | SSH пользователь |
| `VPS_SSH_KEY` | локальный путь к private key |
| `VPS_APP_DIR` | базовая директория приложений на сервере |
| `PROJECT_NAME` | имя проекта внутри `VPS_APP_DIR` |
| `REPO_URL` | git remote URL проекта |

## Validation

Проверить:

- файл `deploy/deploy.env` существует;
- все required keys заполнены;
- `VPS_SSH_KEY` существует локально;
- `PROJECT_NAME` не содержит `/`, `\`, `..` или shell-метасимволы;
- `VPS_APP_DIR` абсолютный Unix path;
- `REPO_URL` выглядит как Git URL.

## Redaction

В пользовательском отчёте можно показывать:

- `VPS_USER@VPS_HOST`;
- `VPS_APP_DIR/PROJECT_NAME`;
- basename SSH key.

Не показывать содержимое `.env`, private key, токены, пароли.
