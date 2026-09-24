# Матрица прав доступа (RBAC)

**Продукт:** Employee Service  
**Документ:** RBAC Matrix  
**ID:** DOC-RBAC  
**Версия:** 1.0  
**Статус:** Baseline v1.0

**Обозначения:**  
`C` — create · `R` — read · `U` — update · `D` — delete · `A` — action · `—` — нет доступа

Права определяются **единственной** ролью пользователя (`role_id`, BR-16 / [ADR-ORG-01](../03-diagrams/architecture/adr-org-model.md)). Union нескольких ролей в Target **не** используется.

Ядро: роли `employee` / `approver` / `admin`. Admin CRUD и смена роли пользователя — в scope целевой модели (реализация — после E1).

**Legacy:** multi-role + union permissions — Previous model.

---

## 1. Матрица функций (ядро Baseline)

| Function | employee | approver | admin (см. backlog) |
| :--- | :---: | :---: | :---: |
| Просмотр каталога активных типов | R | — | R (удобство проверки; создание заявок — нет) |
| Просмотр схемы формы типа | R | — | R |
| Создание заявки (draft) | C | — | — |
| Редактирование своей заявки (`draft` / `returned`) | U | — | — |
| Submit / повторный submit своей заявки | A | — | — |
| Отмена своей заявки (`draft` / `returned`) | A | — | — |
| Просмотр своих заявок (список/карточка) | R | — | — |
| Свободный комментарий к своей заявке (в т.ч. `in_approval`) | C / R | — | — |
| Очередь своих задач согласования | — | R | — |
| Просмотр заявки по своей задаче (полная карточка) | — | R | — |
| Approve / Reject / Return по своей задаче | — | A | — |
| Комментарий при решении по задаче | — | C | — |
| История своей заявки | R | — | — |
| История заявки по своей задаче | — | R | — |
| Выполнение approve/reject/return без задачи | — | — | — |

Примечания к ячейкам:
- Учётка с ролью `approver` не создаёт заявки (нужна роль `employee` на отдельной учётке).
- Для reject/return комментарий обязателен (BR-25); для approve — нет.
- Инициатор может оставлять свободные комментарии в `in_approval` (BR-28).
- Admin может менять `role_id` пользователя; роль влияет на доступные ProcessTransition.
- Право decision по задаче = роль, допускающая transition, **и** assignee open task (BR-15).
- Login JWT — [ADR-AUTH-JWT-01](../03-diagrams/architecture/adr-jwt-core-api.md).

---

## 2. Ограничения доступа (Baseline)

### ACL-01 — Чужие заявки сотрудника
`employee` не может читать/изменять/отменять заявку другого инициатора (BR-01).  
Ожидаемый результат: **HTTP 404** + `ERR_NOT_FOUND` (NFR-SEC-05).

### ACL-02 — Чужие задачи согласующего
`approver` не может approve/reject/return по задаче, где он не assignee (BR-15). → **403** / `ERR_FORBIDDEN_APPROVAL`.

### ACL-03 — Самосогласование
Инициатор не выполняет решения по своей заявке (BR-21). → **403** / `ERR_FORBIDDEN_APPROVAL`.

### ACL-04 / ACL-09 — не определены в Baseline
`ACL-04` и `ACL-09` упоминаются в backlog (AC-ACC-04) и Future-диаграммах admin. В Baseline rbac-matrix **не определены**; семантика — [consistency-review.md](../consistency-review.md) RR-ACL-01.

### ACL-05 — Неактивный тип
Создание заявки по неактивному типу запрещено (BR-10). → `ERR_INACTIVE_TYPE`.

### ACL-06 — Недопустимый статус для действия
Submit/cancel/edit/approve и т.д. вне допустимых статусов → `ERR_INVALID_STATE`.

### ACL-07 — Завершённая / cancelled задача
Повторное действие по завершённой или `cancelled` задаче запрещено (NFR-REL-02, BR-03). → `ERR_TASK_DONE` / `ERR_DUP_ACTION`.

### ACL-08 — Одна роль на пользователя
Пользователь имеет ровно одну роль (`role_id`, BR-16). Admin может изменить роль. Выбор «активной роли» не требуется.  
Auth: JWT ([ADR-AUTH-JWT-01](../03-diagrams/architecture/adr-jwt-core-api.md)).

**Legacy:** multi-role union — Previous model.

---

## 3. Backlog (admin / auth UI)

Отложенные функции и ACL admin/login — см. [backlog.md](../backlog.md).

---

## 4. Связь с ролями Vision

| Роль Vision | Код | Матрица |
| :--- | :--- | :--- |
| Сотрудник | `employee` | колонка employee |
| Согласующий | `approver` | колонка approver |
| Администратор | `admin` | backlog (колонка admin) |

Отдельные колонки «Руководитель» / «HR» **не вводятся** (соответствует Vision).

---

## 5. Open Questions / TBD

**Обязательных открытых вопросов RBAC для Baseline нет.**

---

## 6. Трассировка (Baseline)

| Ограничение | BR | FR | AC |
| :--- | :--- | :--- | :--- |
| ACL-01 | BR-01 | FR-REQ-04 | AC-ACC-01 |
| ACL-02 | BR-15 | FR-APP-03–05 | AC-ACC-02 |
| ACL-03 | BR-21 | FR-APP-03–05 | AC-ACC-03 |
| ACL-05 | BR-10 | FR-REQ-01 | AC-CAT-01 |
| ACL-04, ACL-09 | — | — | backlog AC-ACC-04; не определены в Baseline ([consistency-review.md](../consistency-review.md) RR-ACL-01) |
| ACL-08 | BR-16 | см. [backlog.md](../backlog.md) | см. [backlog.md](../backlog.md) |
| Полная карточка approver | BR-14 | FR-APP-02 | AC-ACC-06 |

Отложенные ACL admin — см. [backlog.md](../backlog.md).
