---
name: skill-creator
description: >
  Создание и валидация навыков.
  Triggers: "создай навык", "new skill", "редактируй навык", "update skill",
  "skill creator", "создание навыка".
  Генерирует SKILL.md + supporting files, валидирует по skill-quality.md,
  ведёт LEARNINGS.md/EVALS.md и правит навыки только через eval gate.
type: analytical
---

# Skill Creator

Создание и эволюция навыков, сохраняющих дух проекта: маленькая атомарная задача, богатый релевантный контекст, self-improvement через `LEARNINGS.md` и `EVALS.md`.

## Supporting Files

| Файл | Когда читать | Назначение |
|---|---|---|
| `references/generated-skill-structure.md` | Перед созданием или крупной переработкой навыка | Структура `SKILL.md`, `references/`, `scripts/`, `assets/`, `LEARNINGS.md`, `EVALS.md` |
| `references/self-improvement-gate.md` | Перед изменением существующего навыка или самого `skill-creator` | Механизм: learning → eval → patch → validation |
| `LEARNINGS.md` | В начале каждого запуска | Только релевантные уроки прошлых запусков |
| `EVALS.md` | Перед правкой `SKILL.md` | Regression cases, которые не должен сломать патч |

## Алгоритм

### 1. Определить режим

| Режим | Когда | Что делать |
|---|---|---|
| `create` | пользователь просит новый навык | Создать каталог навыка, `SKILL.md`, `LEARNINGS.md`, `EVALS.md`, при необходимости `references/`, `scripts/`, `assets/` |
| `update` | пользователь просит изменить навык | Применить self-improvement gate, не дописывать правила без eval |
| `repair` | навык ошибся или противоречит проекту | Сначала зафиксировать failure в `EVALS.md`, затем патчить минимально |
| `audit` | пользователь просит проверить навык | Проверить по quality gate, дать findings без правок, если правки не запрошены |

### 2. Собрать контекст

Всегда прочитать:
- `.ai/ARCHITECTURE.md` — текущая структура проекта
- `rules/skills.md` — анатомия навыка и конвенции
- `.claude/rules/skill-quality.md` — чеклист качества
- локальные `LEARNINGS.md` и `EVALS.md` целевого навыка, если существуют
- `references/generated-skill-structure.md` или `references/self-improvement-gate.md` по режиму

Если данных не хватает, спросить пользователя только о решениях, которые меняют назначение, trigger-фразы, границы задачи, entry/exit или next_skill.

### 3. Создать или изменить навык

Для нового навыка:
1. Создать `skills/{name}/`.
2. Создать `SKILL.md` как тонкий маршрутизатор: frontmatter, контракт, карта supporting files, алгоритм, правила, continuous improvement.
3. Создать `LEARNINGS.md` и `EVALS.md` по шаблонам из `references/generated-skill-structure.md`.
4. Создать `references/` для подробных чеклистов, runbook, rubrics, edge cases; `scripts/` для повторяемых проверок; `assets/` для шаблонов.
5. Если навык распространяется в целевые проекты, убедиться, что `init/SKILL.md` копирует supporting files вместе с `SKILL.md`.

Для существующего навыка:
1. Найти конкретную проблему: missing context, плохой trigger, неверный entry/exit, отсутствие supporting file, ошибка алгоритма.
2. Если меняется поведение `SKILL.md`, сначала добавить или обновить eval-case в `EVALS.md`.
3. Патчить минимально: заменить слабое правило, удалить устаревшее, вынести подробности в `references/`.
4. Не править `SKILL.md` только ради накопления нового наблюдения — для этого есть `LEARNINGS.md`.

### 4. Валидация

Проверить:

- [ ] Frontmatter: name, description, type заполнены
- [ ] description содержит ≥3 trigger-фразы
- [ ] Workflow Contract присутствует для workflow/internal
- [ ] `SKILL.md` решает одну атомарную задачу
- [ ] Критичное в `SKILL.md`, подробности в one-level `references/`
- [ ] Правила ≤7 и не дублируют `CLAUDE.md`
- [ ] LEARNINGS.md и EVALS.md созданы
- [ ] Для изменения поведения есть eval-case или явное обоснование, почему eval не нужен
- [ ] Supporting files названы предметно и напрямую перечислены в `SKILL.md`

Если validation fails, исправить до отчёта или явно зафиксировать blocker.

### 5. Обновление артефактов и синхронизация

| Артефакт | Когда обновлять | Что менять |
|----------|----------------|------------|
| `CLAUDE.md` | Всегда | Строка в таблице навыков |
| `.ai/ARCHITECTURE.md` | Если новый каталог | Дерево модулей |
| `rules/skills.md` | Если новый тип/паттерн | Таблица типов, шаблон контракта |
| `init/SKILL.md` | Если навык для установки | Список копируемых навыков |
| `templates/CLAUDE.md.tpl` | Если навык в шаблоне | Таблица навыков |
| `.ai/sync-manifest.json` | Если создан/удалён навык | Запись source→target для нового навыка |

После изменения product source layer (`skills/`) напомнить пользователю:
1. Добавить запись в `.ai/sync-manifest.json`, если создан новый навык
2. Синхронизировать runtime-копии: `.agents/skills/` и `.claude/skills/`
3. Запустить `python scripts/validate_source_sync.py` для проверки

| Артефакт | Когда обновлять | Что менять |
|----------|----------------|------------|
| `CLAUDE.md` | Всегда | Строка в таблице навыков |
| `.ai/ARCHITECTURE.md` | Если новый каталог | Дерево модулей |
| `rules/skills.md` | Если новый тип/паттерн | Таблица типов, шаблон контракта |
| `init/SKILL.md` | Если навык для установки | Список копируемых навыков |
| `templates/CLAUDE.md.tpl` | Если навык в шаблоне | Таблица навыков |

### 6. Отчёт и self-improvement

Вывести:
- Созданные файлы (пути)
- Результаты валидации (пройдено/не пройдено)
- Какие eval-cases защищают изменение
- Список обновлённых артефактов

После каждого запуска выполнить Improvement Triage:
1. Если задача решена без нового урока → `no_change`.
2. Если найден reusable lesson → добавить краткую запись в `LEARNINGS.md`.
3. Если инструкция навыка привела к ошибке → добавить regression case в `EVALS.md`.
4. Если ошибка повторяемая и eval-case описан → предложить или применить минимальный patch.
5. Если patch меняет поведение → проверить его по `EVALS.md` или явно указать, что eval ручной.

## Правила

1. `SKILL.md` — контракт и маршрутизатор; подробный контекст — в directly linked supporting files.
2. Новый навык без `LEARNINGS.md` и `EVALS.md` не считается завершённым.
3. Поведенческое изменение `SKILL.md` требует eval-case или явного ручного обоснования.
4. Уроки пишутся в `LEARNINGS.md`, failures — в `EVALS.md`; не превращать `SKILL.md` в журнал наблюдений.
5. Создавать в `skills/` как source of truth и сохранять Claude-ориентированную структуру для установки в `.claude/skills/`.
6. Предпочитать замену/удаление/вынесение в `references/` простому добавлению новых правил.
7. Не завершать без quality gate и краткого отчёта о том, какие файлы и почему изменены.
