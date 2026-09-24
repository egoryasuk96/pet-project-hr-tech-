# Employee Service

Сервис заявок сотрудников (отпуск, справки и т.п.) с согласованием руководителем: от подачи заявки до решения в одной системе.

## Проблема

Сейчас кадровые вопросы решаются устно или перепиской по почте, а единой системы, где заявка и её статус видны всем участникам, нет. Из-за этого:

1. Руководитель может забыть о вопросе или затянуть решение.
2. Кадровая служба требует от сотрудника письменного подтверждения руководителя, и сотрудник вынужден получать его отдельно.
3. Сотрудники лишний раз обращаются к руководителю, чтобы узнать статус своей заявки.

## Что делает сервис

1. Сотрудник самостоятельно подаёт заявку (отпуск, справка и т.п.) и видит её статус на каждом этапе.
2. Руководитель согласует заявку, отклоняет её или возвращает на доработку.
3. Сотрудник может доработать возвращённую заявку и отправить её повторно либо отозвать заявку.
4. Сотрудник кадровой службы видит заявку вместе с решением руководителя и без дополнительных уточнений проводит кадровое мероприятие.

## Что в репозитории

Вся аналитическая документация лежит в папке [docs](docs/README.md). Порядок чтения за 5 минут:

1. [Vision & Scope](docs/01-vision-and-scope/vision-scope.md): цели, границы, роли.
2. [Use Cases](docs/02-requirements/use-cases.md): кто и что делает в системе.
3. [Business Rules](docs/02-requirements/business-rules.md): ключевые правила согласования.
4. [Acceptance Criteria](docs/02-requirements/acceptance-criteria.md): проверяемые критерии приёмки.
5. [Архитектура](docs/03-diagrams/architecture/architecture-description.md): контейнеры и границы системы.
6. [ERD](docs/03-diagrams/erd/erd-description.md): модель данных.

Полный перечень артефактов: [docs/README.md](docs/README.md).

## Статус

| Этап | Состояние |
|------|-----------|
| Аналитическая документация | Baseline готов |
| API-контракт (OpenAPI) | Frozen Target (`docs/04-api/`) |
| Core API + Approval E2E | Готово (Stage 5.3 + Action Engine) |
| Backend polish (history / cancel / comments) | Stage 6.1 |
| Frontend (static HTML/JS) | Частично: Login, My Requests, Request Detail (available-actions / execute), Notifications. Create UI / Admin UI / Approver Queue — не реализованы |
| In-app Notifications | Target API + UI список |
| Деплой (Render + Neon) | Запланировано |

## Стек

FastAPI + PostgreSQL. Auth runtime: JWT (`POST /auth/login`, Bearer, без refresh). Лёгкий веб-клиент — static HTML/JS от того же FastAPI (реализованный срез: Login, My Requests, Request Detail, Notifications).

## Локальная БД (Stage 5.2)

Секреты и URL БД задаются переменными окружения (`DATABASE_URL`), не файлами репозитория.

Формат URL для SQLAlchemy/Alembic:

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME
```

Применить схему:

```text
alembic upgrade head
```

Повторяемый demo-seed (роли, пользователи, 2 активных типа заявок с маршрутом; без заявок и задач):

```text
python -m app.db.seed
```

Проверка процесса API (без обращения к PostgreSQL):

```text
uvicorn app.main:app --reload
```

`GET /health` возвращает `{"status":"ok"}`.

## Core API (Stage 5.3)

JWT access token, без refresh. Секреты только через переменные окружения: `DATABASE_URL`, `JWT_SECRET`, при необходимости `DEMO_PASSWORD` для demo-seed.

Запуск API (после миграций):

```text
uvicorn app.main:app --reload
```

OpenAPI / Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), схема: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json).

Миграции те же, что в Stage 5.2 (`alembic upgrade head`). Схема БД не менялась.

Login demo-пользователей (пароль не хранится в репозитории):

```text
set DEMO_PASSWORD=...
python -m app.db.seed
```

Seed идемпотентен: повторный запуск не создаёт дубликаты. Если `DEMO_PASSWORD` задан, обновляется только `password_hash` существующих demo-пользователей.

```http
POST /auth/login
{"login": "employee.demo", "password": "<DEMO_PASSWORD>"}
```

Дальше: `Authorization: Bearer <access_token>`.

Реализованные endpoint'ы (ядро):

- `POST /auth/login`
- `GET /me`
- `GET /request-types`
- `GET /request-types/{type_id}`
- `GET /request-types/{type_id}/schema`
- `POST /requests`
- `GET /requests`
- `GET /requests/{request_id}`
- `PATCH /requests/{request_id}`
- `GET /requests/{request_id}/available-actions`
- `POST /requests/{request_id}/actions/{action_id}`
- `POST /requests/{request_id}/comments`
- `GET /requests/{request_id}/history`
- Notifications API (list / mark read)

Primary mutation: Action Engine (`available-actions` + `actions/{action_id}`). Legacy aliases `POST .../submit` и `POST .../cancel` — deprecated thin wrappers. `/approval-tasks/*/approve|return|reject` — disabled stubs (не primary path).

Полный контракт: [docs/04-api/openapi.yaml](docs/04-api/openapi.yaml).

Тесты без PostgreSQL (Stage 5.2) и API-тесты:

```text
python -m pytest tests
```

API-тесты Stage 5.3 требуют **отдельную** PostgreSQL (`TEST_DATABASE_URL`), не developer-базу из `.env`. Без этой переменной они пропускаются (`skip`), Stage 5.2 тесты продолжают выполняться.

```text
set TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/employee_service_test
python -m pytest tests
```

