# Employee Service — документация

**Продукт:** Employee Service  
**ID:** DOC-HUB  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [Vision & Scope](./01-vision-and-scope/vision-scope.md), [backlog](./backlog.md), [Consistency Review](./consistency-review.md)

---

## Что это

Employee Service — сервис заявок сотрудников (отпуск, справки и т.п.) с согласованием руководителем: от подачи заявки до решения в одной системе.

**Проблема (кратко):** кадровые вопросы решаются устно или по почте без единой системы статусов — руководитель забывает или тянет, кадры требуют отдельное подтверждение, сотрудники лишний раз спрашивают статус.

**Стек реализации (зафиксировано):** FastAPI + PostgreSQL; лёгкий веб-клиент — статические HTML-страницы с JavaScript, которые отдаёт тот же FastAPI.

**Auth runtime:** JWT access token (`POST /auth/login`, `Authorization: Bearer`); см. [ADR-AUTH-JWT-01](./03-diagrams/architecture/adr-jwt-core-api.md). Demo-header из раннего Baseline (ADR-AUTH-DEMO-01) в runtime **не** используется.

**Экраны MVP (5):** login (JWT) / мои заявки / создание заявки / карточка заявки / очередь согласующего. Frontend — следующий этап реализации; Notifications и Admin — [backlog.md](./backlog.md).

Требования вне Baseline — [backlog.md](./backlog.md).

---

## Порядок чтения за 5 минут

1. [Vision & Scope](./01-vision-and-scope/vision-scope.md) — цели, границы, роли  
2. [Use Cases](./02-requirements/use-cases.md) — сценарии  
3. [Business Rules](./02-requirements/business-rules.md) — ключевые правила согласования  
4. [Acceptance Criteria](./02-requirements/acceptance-criteria.md) — проверяемые критерии  
5. [Архитектура](./03-diagrams/architecture/architecture-description.md) — контейнеры и границы системы  
6. [ERD](./03-diagrams/erd/erd-description.md) — модель данных  

---

## Структура `docs/`

| Папка / файл | Содержание |
| :--- | :--- |
| [01-vision-and-scope/](./01-vision-and-scope/) | Vision & Scope, глоссарий |
| [02-requirements/](./02-requirements/) | UC, FR, NFR, BR, AC, RBAC, матрица ошибок |
| [03-diagrams/bpmn/](./03-diagrams/bpmn/) | BPMN TO-BE |
| [03-diagrams/uml/](./03-diagrams/uml/) | UML: UC, state, sequence, class |
| [03-diagrams/architecture/](./03-diagrams/architecture/) | C4-подобные схемы, ADR, трассировка |
| [03-diagrams/erd/](./03-diagrams/erd/) | ERD, snapshot, data dictionary |
| [04-api/api-contract-analysis.md](./04-api/api-contract-analysis.md) | Stage 4.1 — анализ API-контракта (зафиксирован) |
| [04-api/openapi.yaml](./04-api/openapi.yaml) | OpenAPI Baseline-контракт |
| [04-api/approval-api-contract.md](./04-api/approval-api-contract.md) | Контракт Approval API (реализован) |
| [consistency-review.md](./consistency-review.md) | Реестр safe-fixes и OPEN / REQUIRES REVIEW |
| [backlog.md](./backlog.md) | Требования вне MVP Baseline |

Интерфейс описывается через экраны и сценарии в требованиях; отдельного Figma-прототипа в репозитории нет.
