---
name: vps-setup
description: >
  Первоначальная настройка VPS для размещения проектов.
  Triggers: "настрой сервер", "vps setup", "bootstrap сервер", "подготовь VPS".
  Устанавливает Docker, Docker Compose, Git, создаёт структуру /opt/apps/,
  генерирует deploy key для GitHub, клонирует репо, запускает первый deploy.
type: analytical
---

# VPS Setup Skill

Первоначальная настройка нового VPS-сервера для размещения проектов через Docker Compose.

## Предусловия

- Файл `deploy/deploy.env` существует и заполнен (шаблон: `deploy/deploy.env.example`)
- SSH-доступ к серверу работает

## Алгоритм

### Шаг 1: Загрузка конфигурации

Прочитать `deploy/deploy.env` — получить `VPS_HOST`, `VPS_USER`, `VPS_SSH_KEY`, `VPS_APP_DIR`, `PROJECT_NAME`, `REPO_URL`.

Все SSH-команды выполнять через:
```bash
ssh -i {VPS_SSH_KEY} -o StrictHostKeyChecking=accept-new {VPS_USER}@{VPS_HOST} "команда"
```

### Шаг 2: Проверка соединения

```bash
ssh ... "uname -a && cat /etc/os-release | head -3"
```

Убедиться что это Ubuntu 22.04/24.04. Показать пользователю информацию о сервере.

### Шаг 3: Установка Docker и Git

```bash
ssh ... "apt-get update && apt-get install -y docker.io docker-compose-plugin git"
ssh ... "systemctl enable docker && systemctl start docker"
ssh ... "docker --version && docker compose version && git --version"
```

Если Docker уже установлен — пропустить. Проверить вывод версий.

### Шаг 4: Создание структуры директорий

```bash
ssh ... "mkdir -p {VPS_APP_DIR}/{PROJECT_NAME}"
```

Стандартная структура на сервере:
```
{VPS_APP_DIR}/{PROJECT_NAME}/
├── .env              (секреты, копируется через scp)
├── docker-compose.yml (из репо)
├── Dockerfile        (из репо)
└── repo/             (git clone)
```

### Шаг 5: Генерация deploy key для GitHub

```bash
ssh ... "ssh-keygen -t ed25519 -f ~/.ssh/deploy_{PROJECT_NAME} -N '' -C 'deploy-{PROJECT_NAME}'"
ssh ... "cat ~/.ssh/deploy_{PROJECT_NAME}.pub"
```

**ВАЖНО:** Показать пользователю публичный ключ и попросить добавить его в:
GitHub → репозиторий → Settings → Deploy keys → Add deploy key (Read-only).

Дождаться подтверждения от пользователя.

Настроить SSH config на сервере:
```bash
ssh ... "cat >> ~/.ssh/config << 'EOF'
Host github-{PROJECT_NAME}
    HostName github.com
    User git
    IdentityFile ~/.ssh/deploy_{PROJECT_NAME}
    IdentitiesOnly yes
EOF"
```

### Шаг 6: Клонирование репозитория

Преобразовать REPO_URL для использования с SSH-алиасом. Если `REPO_URL=git@github.com:user/repo.git`, заменить `github.com` на `github-{PROJECT_NAME}`:

```bash
ssh ... "git clone {MODIFIED_REPO_URL} {VPS_APP_DIR}/{PROJECT_NAME}/repo"
```

### Шаг 7: Копирование .env и docker файлов

```bash
scp -i {VPS_SSH_KEY} .env {VPS_USER}@{VPS_HOST}:{VPS_APP_DIR}/{PROJECT_NAME}/.env
```

Создать симлинки/копии docker файлов из репо:
```bash
ssh ... "ln -sf {VPS_APP_DIR}/{PROJECT_NAME}/repo/docker-compose.yml {VPS_APP_DIR}/{PROJECT_NAME}/docker-compose.yml"
ssh ... "ln -sf {VPS_APP_DIR}/{PROJECT_NAME}/repo/Dockerfile {VPS_APP_DIR}/{PROJECT_NAME}/Dockerfile"
```

### Шаг 8: Первый запуск

```bash
ssh ... "cd {VPS_APP_DIR}/{PROJECT_NAME} && docker compose build && docker compose up -d"
ssh ... "cd {VPS_APP_DIR}/{PROJECT_NAME} && docker compose ps && docker compose logs --tail=30"
```

### Шаг 9: Отчёт

```
✅ VPS Setup завершён

Сервер:     {VPS_USER}@{VPS_HOST}
ОС:         {os_info}
Docker:     {docker_version}
Проект:     {VPS_APP_DIR}/{PROJECT_NAME}/
Репо:       {REPO_URL}
Контейнер:  {container_status}

⚠️  Deploy key добавлен в GitHub: {да/нет}
```

## Универсальность

Этот навык работает для любого проекта с `Dockerfile` и `docker-compose.yml`. Для нового проекта достаточно:
1. Создать `deploy/deploy.env` с другим `PROJECT_NAME` и `REPO_URL`
2. Запустить навык — он создаст отдельную директорию в `/opt/apps/`
