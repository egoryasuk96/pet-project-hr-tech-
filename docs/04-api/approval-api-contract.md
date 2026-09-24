# Approval API Contract

**Продукт:** Employee Service  
**Документ:** Approval API Contract  
**ID:** DOC-API-APPROVAL  
**Версия:** 2.0  
**Статус:** **Frozen Target** — синхронизирован с runtime Contract Freeze (`openapi.yaml` v1.1.0, `app/api`, `app/schemas`, тесты)  
**Основание:** ADR-ACTION-01, ADR-LIVE-CFG-01, ADR-ERR-03, ADR-AUTH-JWT-01, ADR-ID-01; Baseline + Stage 4.1

---

## 1. Назначение и scope

Документ фиксирует **нормативный Frozen Target** контракт согласования: согласующий работает через карточку заявки и Action Engine, а не через очередь `/approval-tasks/*`.

### 1.1. Target-active (PRIMARY) — Approver flow

1. `GET /requests/{request_id}` — карточка `RequestCard` (ACL: own **или** есть своя `ApprovalTask`); иначе `404 NOT_FOUND`; роль `admin` на карточку не допускается.
2. `GET /requests/{request_id}/available-actions` — тот же ACL; ответ `{ available_actions: [{ id, code, name }] }`; **без** `effect` / `target_status`; **не** встроен в карточку.
3. `POST /requests/{request_id}/actions/{action_id}` — тело `{ comment? }`; для `reject`/`return` нужен непустой (после trim) comment → иначе `422 VALIDATION`; успех `200` = полная обновлённая **`RequestCard`** (не обёртка `ExecuteActionResult`).

UI берёт кнопки только из `available_actions`. Backend на execute повторно проверяет `ProcessTransition`, assignee, BR-15, BR-21.

### 1.2. Explicit non-goals (не Target-active в этом документе)

| Тема | Статус |
| :--- | :--- |
| `/approval-tasks`, `/approval-tasks/{id}`, `.../approve\|reject\|return` как рабочие endpoints | **Disabled stubs** → всегда `409 INVALID_STATE` (не thin aliases) |
| `POST /requests/{id}/approve\|reject\|return` | Нет таких путей |
| Mark-read уведомлений, change-password, отдельный `/users/me` (кроме Target `GET /me`) | Вне scope Approval Contract |
| Admin API, Notification API (кроме упоминания side effects) | Вне scope |
| Optimistic locking / ETag | Вне MVP |
| Embedded form schema на карточке | Нет; схема — `/request-types/{type_id}/schema` |
| `POST /requests/{id}/comments` (free comments) | Deferred stub (`409 INVALID_STATE`) — не Active |

### 1.3. Legacy submit/cancel (кратко)

`POST /requests/{request_id}/submit` и `POST /requests/{request_id}/cancel` — **deprecated thin aliases** Action Engine (коды `submit` / `cancel`). Ответ = `RequestCard`. Target-клиенты должны использовать `POST .../actions/{action_id}`. Для контекста согласования релевантны как точки входа инициатора в маршрут / выхода из `draft`/`returned`, не как decision API согласующего.

---

## 2. Источники и терминология

### 2.1. Источники истины

- Canon runtime: [`openapi.yaml`](./openapi.yaml) (Frozen Target);
- [ADR-ACTION-01](../03-diagrams/architecture/adr-configurable-actions.md);
- [ADR-ERR-03](../03-diagrams/architecture/adr-error-envelope.md);
- [ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md);
- [error-matrix.md](../02-requirements/error-matrix.md);
- UC / FR / BR / RBAC / AC в `docs/02-requirements/`;
- BPMN/UML согласования в `docs/03-diagrams/`.

### 2.2. Термины

| Термин | Значение |
| :--- | :--- |
| `RequestCard` | Полная карточка заявки (см. §5); без `available_actions`, schema, snapshot-полей |
| `available_actions` | Отдельный read: `[{ id, code, name }]` из live `ProcessTransition` |
| `ApprovalTask` | Задача согласующего: `stage_id` → live `ApprovalStage`, `assignee_user_id`, статусы `open` \| `completed` \| `cancelled` |
| sibling cancel | При first-approve / reject / return остальные `open` задачи текущего этапа → `cancelled` (BR-03) |
| decision comment | Комментарий решения (`kind=decision`), привязан к `approval_task_id` |
| Action Engine | Единый execute по `action_id` из каталога действий процесса |

**Не в Target-карточке:** `schema`, `available_actions`, `value_source`, `submit_number`, `field_value_versions`, `RouteInstance`.

---

## 3. Общие соглашения

### 3.1. Аутентификация

Все endpoints требуют JWT:

```http
Authorization: Bearer <access_token>
```

Отсутствующий / невалидный JWT → `401 UNAUTHORIZED`.  
**Demo-header не является текущим механизмом** (не Target).

### 3.2. Авторизация (approval context)

| Операция | Роли | ACL видимости / права |
| :--- | :--- | :--- |
| `GET /requests/{id}` | `employee`, `approver` | employee: своя заявка; approver: есть любая своя `ApprovalTask` (любой статус задачи). Иначе `404 NOT_FOUND`. `admin` — role gate forbid |
| `GET .../available-actions` | `employee`, `approver` | Тот же ACL, что у карточки |
| `POST .../actions/{action_id}` | `employee`, `approver`, `admin` | Transition по `role_id` + статус; для approve/reject/return дополнительно BR-15 (open assignee task на `current_stage_id`) и BR-21 |

У пользователя **одна** системная роль (`role_id`, BR-16). Роль `admin` сама по себе не даёт право согласования.

### 3.3. Формат ошибок (ADR-ERR-03)

Только nested envelope; коды **без** префикса `ERR_`:

```json
{
  "error": {
    "code": "FORBIDDEN_APPROVAL",
    "message": "Вы не можете выполнить действие по этой задаче",
    "details": {}
  }
}
```

Канонические коды: `UNAUTHORIZED`, `INVALID_CREDENTIALS`, `FORBIDDEN`, `FORBIDDEN_APPROVAL`, `NOT_FOUND`, `VALIDATION`, `INACTIVE_TYPE`, `INVALID_STATE`, `REQUEST_ACTION_NOT_ALLOWED`, `TASK_DONE`, `ROUTE_CONFIG`, `INTERNAL`.

**Удалено из Target-контракта:** `ERR_*`, flat `error_code`, утверждения «until E2 / Pre-E2 runtime».

---

## 4. Каталог endpoints (классификация)

| Method | Path | Класс | Назначение |
| :--- | :--- | :--- | :--- |
| GET | `/requests/{request_id}` | **Target active** | Карточка заявки (employee + approver ACL) |
| GET | `/requests/{request_id}/available-actions` | **Target active** | Список доступных действий |
| POST | `/requests/{request_id}/actions/{action_id}` | **Target active** | Execute (approve/reject/return/submit/cancel/…) |
| POST | `/requests/{request_id}/submit` | **Deprecated thin alias** | Alias Action Engine `submit` → `RequestCard` |
| POST | `/requests/{request_id}/cancel` | **Deprecated thin alias** | Alias Action Engine `cancel` → `RequestCard` |
| GET | `/approval-tasks` | **Disabled stub** | Всегда `409 INVALID_STATE` |
| GET | `/approval-tasks/{task_id}` | **Disabled stub** | Всегда `409 INVALID_STATE` |
| POST | `/approval-tasks/{task_id}/approve` | **Disabled stub** | Всегда `409 INVALID_STATE` |
| POST | `/approval-tasks/{task_id}/reject` | **Disabled stub** | Всегда `409 INVALID_STATE` |
| POST | `/approval-tasks/{task_id}/return` | **Disabled stub** | Всегда `409 INVALID_STATE` |

`/approval-tasks/*` — **не** thin aliases и **не** Target-active. Очередь задач в Frozen runtime не реализована; согласующий читает заявку по `GET /requests/{id}` (BR-14).

---

## 5. DTO: RequestCard, AvailableActions, Execute

### 5.1. RequestCard

Полная форма ответа `GET /requests/{id}` и успешного `POST .../actions/{action_id}` (и legacy submit/cancel).

| Поле | Тип | Notes |
| :--- | :--- | :--- |
| `id` | int64 | |
| `request_type` | `{ id, code, name }` | |
| `initiator_user_id` | uuid | |
| `initiator` | `{ id, full_name }` | |
| `status_id` | int64 | |
| `status` | `{ id, code, name }` | codes: `draft`, `in_approval`, `returned`, `approved`, `rejected`, `cancelled` |
| `current_stage_id` | int64 \| null | FK на live stage; вне активного согласования — null (или сохранённый этап после return — см. §7) |
| `current_stage` | `{ id, name, sequence_no }` \| null | |
| `created_at` | datetime | ISO-8601 |
| `updated_at` | datetime | |
| `values` | `[{ field_code, value }]` | working values; `value` nullable string |
| `approval_tasks` | `ApprovalTaskSummary[]` | см. ниже |
| `comments` | `Comment[]` | см. ниже |

**ApprovalTaskSummary:** `id`, `stage_id`, `assignee_user_id`, `status` (`open`\|`completed`\|`cancelled`), `created_at`, `completed_at?`.

**Comment:** `id`, `kind` (`free`\|`decision`), `text`, `author` `{ id, full_name }`, `approval_task_id?`, `created_at`.

**Явно отсутствует:** `schema`, `available_actions`, `value_source`, `submit_number`, `field_value_versions`.

Пример (фрагмент):

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
  "comments": []
}
```

### 5.2. AvailableActionsResponse

```json
{
  "available_actions": [
    { "id": 3, "code": "approve", "name": "Согласовать" },
    { "id": 4, "code": "return", "name": "Вернуть" },
    { "id": 5, "code": "reject", "name": "Отклонить" }
  ]
}
```

Каждый элемент — только `{ id, code, name }`. Поля `effect`, `target_status` **не** входят в runtime-контракт.

Вычисление: live `ProcessTransition` для текущего `status_id` и `role_id` пользователя.  
**Не** фильтрует по assignee / self-approval на GET (эти проверки — на execute: BR-15, BR-21).

### 5.3. ExecuteActionInput / ответ execute

**Request body** (optional):

```json
{ "comment": "Недостаточно обоснования" }
```

| Правило | Поведение |
| :--- | :--- |
| `reject` / `return` | `comment` обязателен, non-empty после trim → иначе `422 VALIDATION` (BR-25) |
| `approve` / прочие | `comment` опционален |
| Успех | `200` + полная **`RequestCard`** |
| После успеха | клиент может повторно вызвать `GET .../available-actions` |

Ответ **не** является `{ request, available_actions }` / `ExecuteActionResult`.

---

## 6. Target-active endpoints (детально)

### 6.1. GET `/requests/{request_id}`

**Summary:** Get a visible request card  
**Traceability:** UC-06, UC-07; FR-REQ-04; BR-14

**Actors:** `employee`, `approver` (не `admin` на этом endpoint).

**ACL**

- `employee` — заявка с `initiator_user_id = current_user`;
- `approver` — существует `ApprovalTask` с `assignee_user_id = current_user` (статус задачи любой: `open` / `completed` / `cancelled`);
- иначе или заявка отсутствует → **`404 NOT_FOUND`** (без утечки существования).

**Response `200`:** `RequestCard` (§5.1).  
`available_actions` **не** вложены — отдельный endpoint §6.2.  
Form schema **не** вложена.

**Errors**

| HTTP | code |
| :---: | :--- |
| 401 | `UNAUTHORIZED` |
| 403 | `FORBIDDEN` (role gate, в т.ч. admin) |
| 404 | `NOT_FOUND` |
| 500 | `INTERNAL` |

---

### 6.2. GET `/requests/{request_id}/available-actions`

**Summary:** List available actions for a request  
**ADR:** ADR-ACTION-01  
**Actors:** `employee`, `approver`

**ACL:** идентичен §6.1 → иначе `404 NOT_FOUND`.

**Response `200`:** `AvailableActionsResponse` (§5.2).

**Errors:** `401 UNAUTHORIZED`, `403 FORBIDDEN`, `404 NOT_FOUND`, `500 INTERNAL`.

---

### 6.3. POST `/requests/{request_id}/actions/{action_id}`

**Summary:** Execute a configured process action  
**ADR:** ADR-ACTION-01  
**Actors:** `employee`, `approver`, `admin` (у admin обычно нет подходящих transitions)

**Path**

| Param | Type | Meaning |
| :--- | :--- | :--- |
| `request_id` | int64 | Заявка |
| `action_id` | int64 | `available_actions[].id` (каталог Action / ProcessTransition) |

**Body:** `ExecuteActionInput` (§5.3).

**Успех `200`:** обновлённая `RequestCard`.

**Типичные decision-коды действий:** `approve`, `reject`, `return` (также `submit`, `cancel` для initiator — через тот же endpoint).

**Errors (approval-relevant)**

| HTTP | code | Когда |
| :---: | :--- | :--- |
| 401 | `UNAUTHORIZED` | Нет/битый JWT |
| 403 | `FORBIDDEN` | Role gate |
| 403 | `FORBIDDEN_APPROVAL` | Self-approval (BR-21) или нет open assignee task (BR-15) |
| 404 | `NOT_FOUND` | Заявка не видна / не существует |
| 409 | `REQUEST_ACTION_NOT_ALLOWED` | Transition не подходит статусу/роли |
| 409 | `TASK_DONE` | Задача уже `completed`/`cancelled`; конкурентный проигравший first-approve |
| 409 | `INACTIVE_TYPE` | Тип неактивен (напр. submit) |
| 409 | `ROUTE_CONFIG` | Невалидный live-маршрут (BR-18) |
| 422 | `VALIDATION` | Пустой comment на reject/return; ошибки полей submit |
| 500 | `INTERNAL` | Откат мутации |

---

## 7. Поведение execute (кратко, approval)

### 7.1. Self-approval (BR-21)

Инициатор не может выполнить approve / reject / return по своей заявке, даже если назначен assignee.  
Execute → `403 FORBIDDEN_APPROVAL`.  
GET `available_actions` **может** ещё показывать decision-коды по роли — UI обязан полагаться на результат execute; backend — источник запрета.

### 7.2. Sibling cancel / first-approve (BR-03)

При успешном decision (approve / reject / return) на этапе:

- задача actor → `completed`;
- остальные `open` задачи **того же** `stage_id` → `cancelled` (sibling cancel);
- повторный execute по `cancelled`/`completed` → `409 TASK_DONE` без side effects.

### 7.3. `current_stage_id` после reject / return / approve

| Действие | Статус заявки | `current_stage_id` |
| :--- | :--- | :--- |
| `approve`, не последний этап | остаётся `in_approval` | → следующий live stage; новые tasks |
| `approve`, последний этап | `approved` | `null` |
| `reject` | `rejected` | маршрут завершён; stage cleared / вне согласования (`null` в Target-модели вне active approval) |
| `return` | `returned` | этап возврата **сохраняется** для аудита (BR-05); open tasks этапа закрыты; повторный submit начнётся с **первого** live stage |

### 7.4. TASK_DONE

Код `409 TASK_DONE`: задача уже обработана или конкурентный проигравший при first-approve wins. Side effects не применяются повторно (NFR-REL-02).

---

## 8. Disabled stubs: `/approval-tasks/*`

Все перечисленные пути — **disabled compatibility stubs**. Поведение одинаковое:

- всегда **`409 INVALID_STATE`** (после auth/role gate);
- **не** thin aliases Action Engine;
- **не** Target-active;
- не возвращают очередь, карточку задачи и не выполняют decision.

| Path | Сообщение (смысл) |
| :--- | :--- |
| `GET /approval-tasks` | Очередь будет доступна на следующем этапе API |
| `GET /approval-tasks/{task_id}` | Stub; читать `GET /requests/{request_id}` |
| `POST .../approve\|reject\|return` | Stub; использовать `POST /requests/{id}/actions/{action_id}` |

Пример ответа:

```json
{
  "error": {
    "code": "INVALID_STATE",
    "message": "Очередь согласования будет доступна после следующего этапа API",
    "details": {}
  }
}
```

**Следствие для FR-APP-01 / FR-APP-02:** требования к очереди/карточке задачи остаются в requirements, но **runtime Frozen Target** реализует видимость через request ACL (BR-14) + available-actions + execute. Отдельный task API отключён.

---

## 9. Legacy thin aliases (initiator, кратко)

| Path | Класс | Эквивалент |
| :--- | :--- | :--- |
| `POST /requests/{id}/submit` | deprecated thin alias | Action Engine code `submit` |
| `POST /requests/{id}/cancel` | deprecated thin alias | Action Engine code `cancel` |

Ответ обоих = `RequestCard`. Target-клиенты: только `POST .../actions/{action_id}`.  
**Не путать** с `/approval-tasks/*/approve|reject|return` — те stubs, не aliases.

---

## 10. Матрица ошибок (approval-related)

| code | HTTP | Типичный контекст |
| :--- | :---: | :--- |
| `UNAUTHORIZED` | 401 | Нет JWT |
| `INVALID_CREDENTIALS` | 401 | Login (вне Approval paths, справочно) |
| `FORBIDDEN` | 403 | Неверная роль (в т.ч. admin на GET card) |
| `FORBIDDEN_APPROVAL` | 403 | BR-15 / BR-21 на execute |
| `NOT_FOUND` | 404 | Заявка не видна / отсутствует |
| `VALIDATION` | 422 | Comment reject/return; поля submit |
| `INACTIVE_TYPE` | 409 | Submit при неактивном типе |
| `INVALID_STATE` | 409 | Stubs `/approval-tasks/*`; deferred endpoints |
| `REQUEST_ACTION_NOT_ALLOWED` | 409 | Transition не для статуса/роли |
| `TASK_DONE` | 409 | Задача уже закрыта; race first-approve |
| `ROUTE_CONFIG` | 409 | Невалидный live route при создании задач |
| `INTERNAL` | 500 | Неожиданная ошибка; rollback |

Envelope всегда:

```json
{ "error": { "code": "<CODE>", "message": "...", "details": {} } }
```

---

## 11. Трассируемость UC / FR / BR

| Capability | UC | FR | BR | Target API |
| :--- | :--- | :--- | :--- | :--- |
| Просмотр карточки (initiator) | UC-06 | FR-REQ-04 | BR-01 | `GET /requests/{id}` |
| Просмотр карточки (approver) | UC-07 | FR-REQ-04, FR-APP-02* | BR-14 | `GET /requests/{id}` (не task path) |
| Список действий | UC-06…09 | ADR-ACTION-01 | BR-16 | `GET .../available-actions` |
| Approve | UC-07 | FR-APP-03, FR-APP-06/07 | BR-03, BR-17, BR-21, BR-25 | `POST .../actions/{action_id}` |
| Reject | UC-08 | FR-APP-04 | BR-04, BR-21, BR-25 | `POST .../actions/{action_id}` |
| Return | UC-09 | FR-APP-05, FR-REQ-08 | BR-05, BR-21, BR-25 | `POST .../actions/{action_id}` |
| Очередь задач | UC-07 | FR-APP-01 | BR-14 | **Stub** `GET /approval-tasks` → 409 |
| Decision по task path | UC-07…09 | FR-APP-03…05 | — | **Stub** `POST /approval-tasks/...` → 409 |
| Submit / cancel | UC-05, UC-10 | FR-REQ-03, FR-REQ-07 | BR-07, BR-19, BR-20 | Target execute; legacy thin aliases |

\* FR-APP-02 исторически описывал task card; Frozen runtime — видимость через request card (CLOSED OQ «Approver card route»).

---

## 12. Закрытые OPEN-вопросы (superseded)

| # (OpenAPI x-requires-review) | Тема | Вердикт Frozen Target |
| :--- | :--- | :--- |
| 5 | Approver card route | **CLOSED** — approver читает `GET /requests/{id}` (BR-14); `/approval-tasks/{id}` = disabled stub |
| 6 | Task visibility error | **CLOSED** — superseded: `/approval-tasks/*` всегда `409 INVALID_STATE` |
| 4 | ApprovalTask date / queue sort | **CLOSED** — очередь вне Target-active scope |
| 11 | Error envelope | **CLOSED** — nested `{ error: { code, message, details } }`, без `ERR_` |
| 1 | Authentication | **CLOSED** — JWT Bearer; demo-header не current |

Ранее в этом документе обсуждавшиеся «working Legacy decision endpoints» и встраивание `available_actions` в GET card / GET task — **отменены** Contract Freeze.

---

## 13. Связанные документы

- [`openapi.yaml`](./openapi.yaml) — machine-readable Frozen Target;
- [`api-contract-analysis.md`](./api-contract-analysis.md) — обзор Core API (сверять с Freeze; при расхождении побеждает OpenAPI + этот документ для approval);
- [ADR-ACTION-01](../03-diagrams/architecture/adr-configurable-actions.md);
- [ADR-ERR-03](../03-diagrams/architecture/adr-error-envelope.md);
- [sequence-approval.md](../03-diagrams/uml/sequence-approval.md);
- [to-be-approval-stage.md](../03-diagrams/bpmn/to-be-approval-stage.md);
- [error-matrix.md](../02-requirements/error-matrix.md).

---

## 14. История версий

| Версия | Дата | Изменение |
| :--- | :--- | :--- |
| 1.x | — | Pre-Freeze: очередь `/approval-tasks` как Target; `available_actions` на карточке; Legacy decision specs |
| **2.0** | 2026-09-24 | **Frozen Target rewrite:** Approver flow через request paths + Action Engine; `/approval-tasks/*` = disabled stubs; RequestCard без embedded actions; execute → RequestCard; nested errors без `ERR_` |
