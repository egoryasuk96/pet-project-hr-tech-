# API Contract Analysis

**Продукт:** Employee Service  
**Документ:** API Contract Analysis  
**Статус:** **Frozen Target** (синхронизирован с runtime и Contract Freeze)  
**Канон:** текущий runtime (`app/api`, `app/schemas`, `app/services`) + тесты; машинно-читаемый контракт — [`openapi.yaml`](./openapi.yaml); согласование — [`approval-api-contract.md`](./approval-api-contract.md).

---

## 1. Назначение

Документ описывает **Frozen Target** REST-контракт MVP: операции, payload, RBAC, ошибки и переходы через Action Engine. Он не заменяет OpenAPI, а фиксирует аналитическую сводку в том же состоянии, что runtime и `openapi.yaml`.

### 1.1. Принципы Target

| Принцип | Зафиксировано |
| :--- | :--- |
| Аутентификация | JWT Bearer ([ADR-AUTH-JWT-01](../03-diagrams/architecture/adr-jwt-core-api.md)): `POST /auth/login`, `GET /me` |
| Идентификаторы | `User.id` — UUID; бизнес-сущности (Request, Action, ApprovalTask, …) — integer ([ADR-ID-01](../03-diagrams/architecture/adr-id-strategy.md)); номер заявки в UI = `request.id` |
| Ошибки | Nested envelope `{ error: { code, message, details } }` ([ADR-ERR-03](../03-diagrams/architecture/adr-error-envelope.md)); коды **без** префикса `ERR_` |
| Конфиг | Live schema / route без snapshot-полей ([ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md)) |
| Lifecycle | Action Engine: `GET .../available-actions` + `POST .../actions/{action_id}` ([ADR-ACTION-01](../03-diagrams/architecture/adr-configurable-actions.md)) |
| Роль | Одна системная роль `role_id` → `roles: [employee\|approver\|admin]` (BR-16); union ролей нет |
| Карточка | `RequestCard` **без** встроенных `schema` и `available_actions` |
| Approver | Читает `GET /requests/{id}` (ACL BR-14) → available-actions → execute; **не** очередь `/approval-tasks/*` |

### 1.2. Классификация endpoints

| Класс | Смысл |
| :--- | :--- |
| **Target active** | Нормативный контракт клиента |
| **Deprecated thin alias** | Работает, делегирует в Action Engine; Target-клиент обязан использовать execute |
| **Disabled stub** | Всегда `409 INVALID_STATE`; **не** thin alias |
| **Deferred stub** | Всегда `409 INVALID_STATE`; отложено до следующего этапа API |
| **Out of Target** | Не документируется как активный Target (change-password, `/users/me`, mark-read, path-approve/reject/return) |

### 1.3. Вне scope / Out of Target-active

- Admin CRUD процессов и справочников (отдельный этап);
- `POST /auth/change-password`;
- `GET /users/me` (путь Target — **`GET /me`**);
- `PATCH /notifications/{id}` (mark-read);
- path-операции `.../approve|reject|return` на заявке или задаче как Target;
- optimistic locking;
- refresh-token.

---

## 2. Inventory endpoints

| Method | Path | Класс | Roles | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/auth/login` | Target active | public | JWT + `CurrentUser` |
| GET | `/me` | Target active | any authenticated | Текущий пользователь |
| GET | `/request-types` | Target active | employee, admin | Каталог активных типов |
| GET | `/request-types/{type_id}` | Target active | employee, admin | Описание активного типа |
| GET | `/request-types/{type_id}/schema` | Target active | employee, admin | Live-схема формы |
| POST | `/requests` | Target active | employee | Создать draft |
| GET | `/requests` | Target active | employee | Список своих заявок |
| GET | `/requests/{request_id}` | Target active | employee (own), approver (via task) | `RequestCard` |
| GET | `/requests/{request_id}/available-actions` | Target active | employee, approver | `{ available_actions: [{id,code,name}] }` |
| POST | `/requests/{request_id}/actions/{action_id}` | Target active | per ProcessTransition | Universal execute → `RequestCard` |
| GET | `/requests/{request_id}/history` | Target active | employee, approver (ACL) | `{ items: [...] }` DESC |
| GET | `/notifications` | Target active | employee, approver, admin | `{ items: [...] }` DESC |
| POST | `/requests/{request_id}/submit` | Deprecated thin alias | employee | Alias Action Engine `submit` → `RequestCard` |
| POST | `/requests/{request_id}/cancel` | Deprecated thin alias | employee | Alias Action Engine `cancel` → `RequestCard` |
| PATCH | `/requests/{request_id}` | Deferred stub | employee | Всегда `409 INVALID_STATE` |
| POST | `/requests/{request_id}/comments` | Deferred stub | employee | Всегда `409 INVALID_STATE` |
| GET | `/approval-tasks` | Disabled stub | — | Всегда `409 INVALID_STATE` |
| GET | `/approval-tasks/{task_id}` | Disabled stub | — | Всегда `409 INVALID_STATE` |
| POST | `/approval-tasks/{task_id}/approve` | Disabled stub | — | Всегда `409 INVALID_STATE` |
| POST | `/approval-tasks/{task_id}/reject` | Disabled stub | — | Всегда `409 INVALID_STATE` |
| POST | `/approval-tasks/{task_id}/return` | Disabled stub | — | Всегда `409 INVALID_STATE` |

**Не в inventory как Target-active:** `/auth/change-password`, `/users/me`, `PATCH /notifications/{id}`, `POST /requests/{id}/approve|reject|return`.

---

## 3. Auth

### 3.1. POST `/auth/login` — Target active

**Request**

```json
{ "login": "employee1", "password": "********" }
```

Security: отсутствует (public).

**Response `200`**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": {
    "id": "33333333-3333-4333-8333-333333333333",
    "login": "employee1",
    "full_name": "Иван Петров",
    "email": null,
    "position": "Specialist",
    "department": "HR",
    "roles": ["employee"]
  }
}
```

`user` — схема `CurrentUser`. Refresh-token нет.

**Errors**

| HTTP | code | Условие |
| :---: | :--- | :--- |
| 401 | `INVALID_CREDENTIALS` | Неверный login/password |
| 403 | `FORBIDDEN` | Пользователь inactive |
| 422 | `VALIDATION` | Невалидное/пустое body |
| 500 | `INTERNAL` | Непредвиденная ошибка |

Трассировка: UC-01; FR-AUTH-01.

### 3.2. GET `/me` — Target active

**Не** `/users/me`.

**Response `200`:** `CurrentUser`.

```json
{
  "id": "33333333-3333-4333-8333-333333333333",
  "login": "employee1",
  "full_name": "Иван Петров",
  "email": null,
  "position": "Specialist",
  "department": "HR",
  "roles": ["employee"]
}
```

`roles` — ровно один элемент (отражение `User.role_id`).

**Errors:** `401 UNAUTHORIZED`, `500 INTERNAL`.

Трассировка: FR-AUTH-02.

### 3.3. CurrentUser (DTO)

| Поле | Тип | Обязательно |
| :--- | :--- | :---: |
| `id` | uuid | да |
| `login` | string | да |
| `full_name` | string | да |
| `email` | string \| null | нет |
| `position` | string \| null | нет |
| `department` | string \| null | нет |
| `roles` | `[RoleCode]` length 1 | да |

`RoleCode`: `employee` \| `approver` \| `admin`.

Все защищённые endpoints: `Authorization: Bearer <access_token>`.

---

## 4. Каталог типов заявок

### 4.1. GET `/request-types` — Target active

Роли: `employee`, `admin`. Только `is_active = true`. Пустой каталог → `200` и `[]`.

**Response item (`RequestTypeSummary`):** `{ id, code, name, description? }`.

Errors: `403 FORBIDDEN`, `500 INTERNAL`.

### 4.2. GET `/request-types/{type_id}` — Target active

Отсутствующий или неактивный тип → `404 NOT_FOUND` (interim; см. OPEN §11).

### 4.3. GET `/request-types/{type_id}/schema` — Target active

Live-схема формы.

**Response**

```json
{
  "request_type_id": 1,
  "fields": [
    {
      "code": "start_date",
      "name": "Дата начала",
      "data_type": "date",
      "required": true,
      "order_no": 1,
      "dictionary_id": null
    }
  ]
}
```

`data_type`: `text` \| `date` \| `number` \| `catalog` \| `boolean`.  
Вложение dictionary items в schema **не** зафиксировано (OPEN §11).

Errors: `403 FORBIDDEN`, `404 NOT_FOUND` (нет / inactive), `500 INTERNAL`.

---

## 5. Requests lifecycle

### 5.1. RequestCard — Target shape (freeze)

Полная карточка заявки. **Нет** полей `schema`, `available_actions`, `value_source`, `submit_number`, `field_value_versions`. Схема — отдельно через schema endpoint; действия — через available-actions.

```json
{
  "id": 10245,
  "request_type": { "id": 1, "code": "annual_leave", "name": "Annual leave" },
  "initiator_user_id": "33333333-3333-4333-8333-333333333333",
  "initiator": { "id": "33333333-3333-4333-8333-333333333333", "full_name": "Иван Петров" },
  "status_id": 2,
  "status": { "id": 2, "code": "in_approval", "name": "На согласовании" },
  "current_stage_id": 10,
  "current_stage": { "id": 10, "name": "Line manager", "sequence_no": 1 },
  "created_at": "2026-09-21T09:00:00Z",
  "updated_at": "2026-09-21T09:10:00Z",
  "values": [{ "field_code": "start_date", "value": "2026-10-01" }],
  "approval_tasks": [
    {
      "id": 501,
      "stage_id": 10,
      "assignee_user_id": "77777777-7777-4777-8777-777777777777",
      "status": "open",
      "created_at": "2026-09-21T09:10:00Z",
      "completed_at": null
    }
  ],
  "comments": [
    {
      "id": 801,
      "kind": "decision",
      "text": "Недостаточно обоснования",
      "author": { "id": "...", "full_name": "..." },
      "approval_task_id": 501,
      "created_at": "2026-09-21T10:00:00Z"
    }
  ]
}
```

| Поле | Примечание |
| :--- | :--- |
| `request_type` | `{ id, code, name }` |
| `initiator_user_id` / `initiator` | UUID + `{ id, full_name }` |
| `status_id` / `status` | `{ id, code, name }` |
| `current_stage_id` / `current_stage` | nullable; при `in_approval` обычно заданы |
| `values` | working `RequestFieldValue`: `{ field_code, value }` |
| `approval_tasks` | summary: `open` \| `completed` \| `cancelled` |
| `comments` | `kind`: `free` \| `decision` |

Тот же `RequestCard` возвращают: GET card, POST execute, thin aliases submit/cancel.

### 5.2. POST `/requests` — Target active

**Request:** `{ "request_type_id": 1 }`.  
`initiator_user_id` клиент не передаёт.

**Response `201` (`CreatedRequest`):**

```json
{
  "id": 10245,
  "request_type_id": 1,
  "initiator_user_id": "33333333-3333-4333-8333-333333333333",
  "status_id": 1,
  "status": { "id": 1, "code": "draft", "name": "Черновик" },
  "current_stage_id": null,
  "created_at": "2026-09-21T09:00:00Z",
  "updated_at": "2026-09-21T09:00:00Z"
}
```

Атомарно создаётся HistoryEvent (`create` → `draft`). Snapshot RouteInstance / FieldValueVersion **не** создаются.

| HTTP | code |
| :---: | :--- |
| 404 | `NOT_FOUND` — тип не существует |
| 409 | `INACTIVE_TYPE` |
| 422 | `VALIDATION` |
| 403 | `FORBIDDEN` |
| 500 | `INTERNAL` |

### 5.3. GET `/requests` — Target active

Только заявки текущего employee (`initiator_user_id`). Сортировка `created_at` DESC.

Query: `status?` (`draft` \| `in_approval` \| `returned` \| `approved` \| `rejected` \| `cancelled`), `page?` (default 1), `page_size?` (default 20, max 100).

**Response `200`:** массив `RequestListItem` (envelope пагинации не зафиксирован — OPEN §11):

```json
[
  {
    "id": 10245,
    "request_type": { "id": 1, "code": "annual_leave", "name": "Annual leave" },
    "status": { "id": 2, "code": "in_approval", "name": "На согласовании" },
    "current_stage": { "id": 10, "name": "Line manager", "sequence_no": 1 },
    "created_at": "2026-09-21T09:00:00Z",
    "updated_at": "2026-09-21T09:10:00Z"
  }
]
```

### 5.4. GET `/requests/{request_id}` — Target active

**ACL**

- `employee` — своя заявка;
- `approver` — заявка, по которой есть **любая** собственная ApprovalTask (любой статус задачи);
- чужая / отсутствующая → `404 NOT_FOUND` (без раскрытия факта);
- `admin` на этот endpoint **не** допускается (role gate → `403 FORBIDDEN`).

**Response `200`:** `RequestCard` (см. §5.1).  
`available_actions` и form schema **не** встроены.

Трассировка: UC-06, UC-07; FR-REQ-04; BR-14.

### 5.5. GET `/requests/{request_id}/available-actions` — Target active

Read-only. Тот же ACL видимости, что у GET card.

Backend считает действия из live `ProcessTransition` по current `status_id` и user `role_id`. На этом endpoint **не** фильтруются assignee / self-approval (это на execute).

**Response `200`**

```json
{
  "available_actions": [
    { "id": 3, "code": "approve", "name": "Согласовать" },
    { "id": 4, "code": "return", "name": "Вернуть" },
    { "id": 5, "code": "reject", "name": "Отклонить" }
  ]
}
```

Каждый элемент — **только** `{ id, code, name }`. Нет `effect`, `target_status`.

UI не выбирает кнопки по жёстким `if code == "approve"`.

Roles: `employee`, `approver`.

### 5.6. POST `/requests/{request_id}/actions/{action_id}` — Target active

Единственный Target mutation для process transitions (submit / cancel / approve / reject / return и др. по каталогу Action + ProcessTransition).

**Path:** `request_id` (int), `action_id` (int) — из `available_actions[].id`.

**Body (optional)**

```json
{ "comment": "Недостаточно обоснования" }
```

`comment` обязателен (non-empty после trim) для reject/return → иначе `422 VALIDATION`. Для остальных действий optional.

**Server re-check on execute**

1. Action / transition существуют и активны;
2. process + from_status + role;
3. ownership / open assignee task / current stage / self-approval (BR-15, BR-21);
4. effect (`status_only` \| `approve_advance` на live stage и т.п.).

**Response `200`:** полный обновлённый **`RequestCard`**.  
Отдельного wrapper `ExecuteActionResult` **нет**. Клиент при необходимости перезапрашивает `GET .../available-actions`.

| HTTP | code | Условие |
| :---: | :--- | :--- |
| 403 | `FORBIDDEN` / `FORBIDDEN_APPROVAL` | Нет роли / self-approval / нет open assignee task |
| 404 | `NOT_FOUND` | Заявка не видна |
| 409 | `REQUEST_ACTION_NOT_ALLOWED` | Действие недоступно для статуса/роли |
| 409 | `TASK_DONE` | Задача уже обработана |
| 409 | `INACTIVE_TYPE` / `ROUTE_CONFIG` | Submit-сценарии |
| 422 | `VALIDATION` | Нет comment (reject/return) или ошибки полей submit |
| 500 | `INTERNAL` | Rollback мутаций |

Roles: `employee`, `approver`, `admin` (у admin обычно нет ProcessTransition).

### 5.7. POST `/requests/{request_id}/submit` — Deprecated thin alias

Делегирует в Action Engine (`submit`). Response = полный `RequestCard`.  
Target-клиент **обязан** использовать `POST .../actions/{action_id}`.

Role: `employee`. Ошибки — как у execute (submit-ветка).

### 5.8. POST `/requests/{request_id}/cancel` — Deprecated thin alias

Делегирует в Action Engine (`cancel`). Response = полный `RequestCard`.

Role: `employee`.

### 5.9. Deferred stubs (requests)

| Method | Path | Поведение |
| :--- | :--- | :--- |
| PATCH | `/requests/{request_id}` | `409 INVALID_STATE` — сохранение working values отложено |
| POST | `/requests/{request_id}/comments` | `409 INVALID_STATE` — free comment отложен |

Decision comments создаются через Action Engine (`ExecuteActionInput.comment` на reject/return), не через comments stub.

Body schemas (`UpdateValuesInput`, `CreateCommentInput`) сохранены в OpenAPI для будущего этапа, но endpoints **не** Target-active.

---

## 6. History

### 6.1. GET `/requests/{request_id}/history` — Target active

Тот же ACL видимости, что у GET card (`employee` own / `approver` via task).

**Response `200`**

```json
{
  "items": [
    {
      "id": 703,
      "action": "approve",
      "actor_id": "77777777-7777-4777-8777-777777777777",
      "from_state": "in_approval",
      "to_state": "approved",
      "comment": null,
      "at": "2026-09-21T10:00:00Z"
    },
    {
      "id": 702,
      "action": "submit",
      "actor_id": "33333333-3333-4333-8333-333333333333",
      "from_state": "draft",
      "to_state": "in_approval",
      "comment": null,
      "at": "2026-09-21T09:10:00Z"
    },
    {
      "id": 701,
      "action": "create",
      "actor_id": "33333333-3333-4333-8333-333333333333",
      "from_state": null,
      "to_state": "draft",
      "comment": null,
      "at": "2026-09-21T09:00:00Z"
    }
  ]
}
```

| Правило | Freeze |
| :--- | :--- |
| Envelope | `{ items: [...] }` |
| Сортировка | `at` **DESC** (новые сверху) |
| Actor | `actor_id` (uuid \| null) — **не** вложенный `actor` |
| Snapshot values | **нет** `field_value_versions` |
| Пагинация | не зафиксирована (OPEN §11); runtime отдаёт полный список |

History read-only. HistoryEvent не изменяется через API.

Errors: `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 NOT_FOUND`, `500 INTERNAL`.

Трассировка: UC-14; FR-AUDIT-01.

---

## 7. Notifications

### 7.1. GET `/notifications` — Target active

Только уведомления текущего пользователя (recipient = authenticated user).

**Response `200`**

```json
{
  "items": [
    {
      "id": 901,
      "request_id": 10245,
      "approval_task_id": 501,
      "event_type": "request_submitted",
      "text": "Новая заявка на согласование",
      "read": false,
      "created_at": "2026-09-21T09:10:00Z"
    }
  ]
}
```

| Правило | Freeze |
| :--- | :--- |
| Envelope | `{ items: [...] }` |
| Сортировка | `created_at` **DESC** |
| Mark-read | **не** часть Target-active (`PATCH` mark-read отсутствует) |
| Roles | `employee`, `approver`, `admin` |

`event_type` enum: `new_task` \| `status_change` \| `request_submitted` \| `request_approved` \| `request_rejected` \| `request_returned` \| `request_cancelled`.

`request_id` / `approval_task_id` — nullable.

Трассировка: UC-13; FR-NOTIF-02.

---

## 8. Disabled stubs: `/approval-tasks/*`

Все маршруты `/approval-tasks/*` — **disabled compatibility stubs**. Они **не** являются thin aliases Action Engine.

| Method | Path | Ответ |
| :--- | :--- | :--- |
| GET | `/approval-tasks` | всегда `409 INVALID_STATE` |
| GET | `/approval-tasks/{task_id}` | всегда `409 INVALID_STATE` |
| POST | `/approval-tasks/{task_id}/approve` | всегда `409 INVALID_STATE` |
| POST | `/approval-tasks/{task_id}/reject` | всегда `409 INVALID_STATE` |
| POST | `/approval-tasks/{task_id}/return` | всегда `409 INVALID_STATE` |

Пример:

```json
{
  "error": {
    "code": "INVALID_STATE",
    "message": "Очередь согласования будет доступна после следующего этапа API",
    "details": {}
  }
}
```

**Target-flow согласующего**

1. `GET /requests/{id}` (ACL BR-14 — любая своя ApprovalTask);
2. `GET /requests/{id}/available-actions`;
3. `POST /requests/{id}/actions/{action_id}`.

Очередь задач как отдельный list endpoint в Target-active **не** реализована. Детали семантики approve_advance / first-approve-wins / decision comments — в [`approval-api-contract.md`](./approval-api-contract.md) в части, согласованной с Action Engine и OpenAPI.

---

## 9. RBAC summary (runtime `role_id`)

У пользователя одна роль. Матрица ниже — поверх ownership / assignee / ProcessTransition.

| Operation | employee | approver | admin |
| :--- | :---: | :---: | :---: |
| POST `/auth/login` | public | public | public |
| GET `/me` | R | R | R |
| GET `/request-types*` | R | — | R |
| POST `/requests` | C | — | — |
| GET `/requests` | R (own) | — | — |
| GET `/requests/{id}` | R (own) | R (via any own task) | — (role gate) |
| GET `.../available-actions` | R (ACL) | R (ACL) | — |
| POST `.../actions/{action_id}` | A (transition) | A (transition) | A (обычно нет transition) |
| POST `.../submit` \| `.../cancel` | A (own, alias) | — | — |
| GET `.../history` | R (own) | R (via task) | — |
| GET `/notifications` | R (own) | R (own) | R (own) |
| PATCH values / POST comments | deferred stub | — | — |
| `/approval-tasks/*` | disabled stub | disabled stub | disabled stub |

Примечания:

1. `approver` без `employee` не получает employee permissions каталога/создания заявок.
2. Self-approval запрещён (BR-21) → `FORBIDDEN_APPROVAL` на execute.
3. Employee к чужой заявке → `404 NOT_FOUND`.
4. Admin читает каталог/схему; Admin CRUD / реестр — вне Target-active.

---

## 10. Errors (ADR-ERR-03)

### 10.1. Envelope

```json
{
  "error": {
    "code": "REQUEST_ACTION_NOT_ALLOWED",
    "message": "Действие недоступно для заявки в текущем статусе или роли",
    "details": {}
  }
}
```

Коды **без** префикса `ERR_`. Плоский `{ error_code: "ERR_…" }` — не Target.

### 10.2. Коды Target

| code | Типичный HTTP | Смысл |
| :--- | :---: | :--- |
| `UNAUTHORIZED` | 401 | Нет / невалидный JWT |
| `INVALID_CREDENTIALS` | 401 | Неверный login/password |
| `FORBIDDEN` | 403 | Роль / inactive user |
| `FORBIDDEN_APPROVAL` | 403 | Self-approval или нет open assignee task |
| `NOT_FOUND` | 404 | Объект отсутствует или невидим |
| `VALIDATION` | 422 | Body / schema / обязательный comment |
| `INACTIVE_TYPE` | 409 | Тип заявки неактивен |
| `INVALID_STATE` | 409 | Disabled/deferred stub или недопустимое состояние |
| `REQUEST_ACTION_NOT_ALLOWED` | 409 | Action Engine: transition недоступен |
| `TASK_DONE` | 409 | Задача уже completed/cancelled |
| `ROUTE_CONFIG` | 409 | Маршрут без этапов/назначений |
| `INTERNAL` | 500 | Непредвиденная ошибка; mutation rollback |

`CONFLICT_VERSION` / `DUP_ACTION` / `PASSWORD_MISMATCH` в Frozen Target-active **не** используются как primary коды текущего runtime.

---

## 11. State / transitions (Action Engine)

| From | Action code (типично) | To | Guard / effect |
| :--- | :--- | :--- | :--- |
| — | create (`POST /requests`) | `draft` | Тип активен; initiator = current user |
| `draft` / `returned` | `submit` | `in_approval` | Live validation; stage 1; ApprovalTask из live assignments |
| `draft` / `returned` | `cancel` | `cancelled` | Initiator; alias `.../cancel` |
| `in_approval` | `approve` | `in_approval` | Не последний этап; first-approve-wins; next-stage tasks |
| `in_approval` | `approve` | `approved` | Последний этап |
| `in_approval` | `reject` | `rejected` | Comment required |
| `in_approval` | `return` | `returned` | Comment required; `current_stage_id` сохранён для аудита |

Терминальные: `approved`, `rejected`, `cancelled`. Cancel из `in_approval` через ProcessTransition обычно недоступен.

**Клиентский путь**

```
available-actions → POST /requests/{id}/actions/{action_id} → RequestCard
```

Thin aliases `submit` / `cancel` дают тот же эффект и тот же `RequestCard`, но помечены deprecated.

### 11.1. Live configuration

| Данные | Поведение |
| :--- | :--- |
| Form schema | Live RequestFieldDefinition (`GET .../schema`) |
| Field values | RequestFieldValue на карточке (`values`) |
| Approval route | Live ApprovalRoute / Stage / Assignment при submit / approve_advance |
| available_actions | Отдельный GET; `{ id, code, name }` |
| History | HistoryEvent append-only |
| In-flight | Admin-правки live config **могут** затронуть in-flight ([ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md)) |

### 11.2. Запреты прямых мутаций клиентом

- Status / `current_stage_id` / `initiator_user_id` / `request_type_id` не задаются через PATCH (PATCH — deferred stub).
- ApprovalTask и HistoryEvent не создаются/меняются клиентом напрямую.
- `/approval-tasks/*` decision stubs не выполняют бизнес-эффект.

---

## 12. Traceability (сжато)

| UC / FR | Target coverage |
| :--- | :--- |
| UC-01 / FR-AUTH-01 | POST `/auth/login` |
| FR-AUTH-02 | GET `/me` |
| UC-03 / FR-CAT-01…03 | GET `/request-types*` |
| UC-04 / FR-REQ-01 | POST `/requests` |
| UC-05 / FR-REQ-03 | `actions/{id}` (submit); alias `.../submit` |
| UC-06 / FR-REQ-04…05, FR-CAB-02 | GET `/requests`, GET card |
| UC-07…09 / FR-APP-* | GET card (approver ACL) + available-actions + execute |
| UC-10 / FR-REQ-07 | execute cancel; alias `.../cancel` |
| UC-13 / FR-NOTIF-02 | GET `/notifications` |
| UC-14 / FR-AUDIT-01 | GET `.../history` |
| FR-AUDIT-02 | side effect значимых мутаций |

Admin UC-11/12/15 и mark-read FR-NOTIF-03 — вне Target-active inventory.

---

## 13. OPEN / CLOSED review items

Согласовано с `x-requires-review` в [`openapi.yaml`](./openapi.yaml).

| # | Тема | Status | Решение / остаток |
| ---: | :--- | :--- | :--- |
| 1 | Authentication | **CLOSED** | JWT; `POST /auth/login` + `GET /me` |
| 2 | Inactive type read | **OPEN** | Interim: GET detail/schema → `404 NOT_FOUND` |
| 3 | Dictionary items | **OPEN** | Embed в schema vs отдельный read endpoint не зафиксирован |
| 4 | ApprovalTask queue date | **CLOSED** | `/approval-tasks/*` disabled; queue вне Target-active |
| 5 | Approver card route | **CLOSED** | Approver читает `GET /requests/{id}` (BR-14); task card stub |
| 6 | Task visibility error | **CLOSED** | Superseded: stubs всегда `409 INVALID_STATE` |
| 7 | Cancelled card values | **OPEN** | Презентация values после cancel из `returned` отдельно не зафиксирована сверх `RequestCard.values` |
| 8 | Free comment states | **CLOSED** | `POST .../comments` — deferred stub |
| 9 | History pagination | **OPEN** | Runtime — полный `items`; нужна ли пагинация — не зафиксировано |
| 10 | List pagination envelope | **OPEN** | Есть `page` / `page_size`; envelope навигации не зафиксирован |
| 11 | Error envelope | **CLOSED** | ADR-ERR-03 nested; без `ERR_` |
| 12 | OpenAPI x-requirement | **OPEN** | Проект использует UC/FR/AC, не US-XXX |

**Истинно открытые для Target:** dictionary embed, pagination envelopes, inactive-type read code, cancelled values nuance, x-requirement convention.

---

## 14. Sibling references

| Документ | Роль |
| :--- | :--- |
| [`openapi.yaml`](./openapi.yaml) | Frozen Target OpenAPI 3.0.3 — source of truth для схем и paths |
| [`approval-api-contract.md`](./approval-api-contract.md) | Аналитика согласования / Action Engine (должна быть согласована с freeze) |
| [ADR-AUTH-JWT-01](../03-diagrams/architecture/adr-jwt-core-api.md) | JWT |
| [ADR-ACTION-01](../03-diagrams/architecture/adr-configurable-actions.md) | Configurable actions |
| [ADR-ERR-03](../03-diagrams/architecture/adr-error-envelope.md) | Error envelope |
| [ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md) | Live config |
| [ADR-ID-01](../03-diagrams/architecture/adr-id-strategy.md) | ID strategy |
| [error-matrix.md](../02-requirements/error-matrix.md) | Матрица кодов |

---

## 15. Self-check (не является текущим Target)

Следующие формулировки **не** должны читаться как актуальный Frozen Target:

- «until E2» / «Pre-E2 runtime» как описание текущего контракта;
- `/approval-tasks/*` как thin aliases;
- `available_actions` / `schema` внутри `RequestCard`;
- активный `GET /users/me` вместо `GET /me`;
- response execute как `ExecuteActionResult`;
- `field_value_versions` в history;
- primary error codes с префиксом `ERR_`;
- JWT login / notifications как «future backlog» (они Target-active);
- `POST /auth/change-password`, mark-read, path `approve|reject|return` как Target-active.
