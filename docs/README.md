# Employee Service — документация

**Продукт:** Employee Service  
**ID:** DOC-HUB  
**Версия:** 1.0  
**Статус:** Baseline v1.0 (структура каталога)  
**Связанные документы:** [Vision & Scope](./01-vision-and-scope/vision-scope.md), [backlog](./backlog.md) (появится на следующем этапе)

---

## Что это

Employee Service — сервис заявок сотрудников (отпуск, справки и т.п.) с последовательным workflow согласования. Проект для портфолио системного аналитика: главный результат — аналитическая документация; код MVP вторичен.

**Стек реализации (зафиксировано):** FastAPI + PostgreSQL; лёгкий веб-клиент — статические HTML-страницы с JavaScript, которые отдаёт тот же FastAPI. Без настоящей авторизации: роль передаётся в заголовке.

**Экраны MVP (5):** выбор роли, мои заявки, создание заявки, карточка заявки, очередь согласующего.

---

## Порядок чтения за 5 минут

1. [Vision & Scope](./01-vision-and-scope/vision-scope.md) — цели, границы, роли  
2. [Use Cases](./02-requirements/use-cases.md) — сценарии  
3. [Business Rules](./02-requirements/business-rules.md) — ключевые правила (+ [Snapshot Model](./03-diagrams/erd/snapshot-model.md))  
4. [Acceptance Criteria](./02-requirements/acceptance-criteria.md) — проверяемые критерии  
5. [Архитектура](./03-diagrams/architecture/architecture-description.md) — контейнеры и границы системы  
6. [ERD](./03-diagrams/erd/README.md) — модель данных  

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
| [04-api/openapi.yaml](./04-api/openapi.yaml) | Заготовка OpenAPI (контракт — отдельная задача) |

Интерфейс описывается через экраны и сценарии в требованиях; отдельного Figma-прототипа в репозитории нет.
