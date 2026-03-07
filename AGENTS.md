# AGENTS.md - Инструкции для AI Assistant

## Запуск проекта на Windows

Проект использует bash-скрипты и GNU-утилиты. Для Windows используйте **Docker**:

### Docker (рекомендуется)

1. Убедитесь, что Docker Desktop запущен

2. Соберите и запустите:
```powershell
docker build -t grapheneos-website .
docker run -d -p 8080:80 --name grapheneos grapheneos-website
```

Сайт будет доступен на http://localhost:8080

### WSL2 (альтернатива)

```bash
wsl --install
# В WSL Ubuntu:
sudo apt update && sudo apt install -y python3-venv python3-pip nodejs npm openjdk-17-jre parallel moreutils rsync brotli zopfli libxml2-utils gixy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm ci
./process-static
```

## Структура проекта

```
grapheneos.org/
├── openspec/           # OpenSpec планирование
│   ├── changes/       # Изменения
│   └── specs/         # Спецификации
├── templates/         # Jinja2 шаблоны
├── static/            # Исходные статические файлы
├── i18n/              # Переводы (после реализации i18n)
│   ├── en/messages.json
│   ├── de/messages.json
│   ├── fr/messages.json
│   ├── es/messages.json
│   └── ru/messages.json
├── process-templates  # Обработка Jinja2 шаблонов
├── process-static     # Полный пайплайн сборки
├── generate-sitemap   # Генерация sitemap.xml
├── generate-feed      # Генерация Atom feed
├── nginx/             # Конфигурация nginx
│   └── nginx-dev.conf # Конфиг для локальной разработки
└── static-tmp/        # Собранные файлы (создаётся автоматически)
```

## OpenSpec Workflow

Создано для управления спецификациями и изменениями проекта.

### Структура

```
openspec/
├── specs/       # Спецификации (SPEC.md - шаблон)
└── changes/    # Изменения (CHANGE.md - шаблон)
```

### Команды

```bash
# Создать новую спецификацию
cp openspec/specs/SPEC.md openspec/specs/<feature-name>.md

# Создать изменение
cp openspec/changes/CHANGE.md openspec/changes/<feature-name>.md
```

### Статусы

- **SPEC:** Draft → Review → Accepted → Implemented
- **CHANGE:** Draft → Review → Accepted → Merged

## Сборка (в Docker/WSL)

```bash
# Полная сборка со всеми проверками
./process-static

# Отдельные шаги:
python process-templates static        # Только шаблоны
./generate-sitemap                    # Sitemap
./generate-feed                       # Feed
```

## Проверка качества

Скрипт `process-static` автоматически запускает:
- `eslint` для JavaScript
- `stylelint` для CSS
- `vnu-jar` для валидации HTML/XML/SVG
- `html-minifier-terser` для minification
- `gixy` для проверки nginx конфига

## Локальный веб-сервер

Один контейнер — сборка и nginx сразу:

```powershell
# Собрать и запустить
docker build -t grapheneos-website .
docker run -d -p 8080:80 --name grapheneos grapheneos-website
```

После изменений — пересобрать:
```powershell
docker build -t grapheneos-website . && docker rm -f grapheneos && docker run -d -p 8080:80 --name grapheneos grapheneos-website
```

Откройте http://localhost:8080

## Развёртывание

```bash
./deploy-static  # Требует доступ к серверам GrapheneOS
```

## Примечания

- Все bash-скрипты используют `#!/bin/bash` (требуется bash, не sh)
- Для Windows без WSL/Docker требуется портировать скрипты на Python
- Проект использует GNU parallel, sponge (moreutils), brotli, zopfli
