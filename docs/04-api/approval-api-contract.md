# Approval API Contract

**Продукт:** Employee Service  
**Документ:** Approval API Contract  
**Версия:** 1.2
**Статус:** Implemented
**Основание:** Baseline v1.0 требований, Stage 4.1 API Contract Analysis, Stage 5.3 Core API

---

## 1. Назначение и scope

Документ фиксирует контракт Approval API: очередь задач согласующего, полную карточку заявки, approve, return и reject. Endpoints реализованы в backend; бизнес-модель Baseline не расширялась.

В документе:

- детальное описание приведено на русском языке;
- `path`, operation name, Swagger `summary` и `description` приведены на английском;
- используется task-centric ресурс `ApprovalTask`, поскольку решение принимается по назначенной задаче, а не напрямую по заявке (BR-15);
- используется JWT Bearer, уже реализованный в Stage 5.3;
- новые статусы, роли, business rules и `error_code` не вводятся.

### 1.1. В scope

- `GET /approval-tasks` — очередь открытых задач текущего согласующего;
- `GET /approval-tasks/{task_id}` — задача и полная карточка заявки;
- `POST /approval-tasks/{task_id}/approve`;
- `POST /approval-tasks/{task_id}/return`;
- `POST /approval-tasks/{task_id}/reject`;
- decision comments в составе approve/reject/return;
- связь с free comments инициатора;
- RBAC, state transitions, snapshot, first-approve-wins и ошибки.

### 1.2. Вне scope

- изменение ERD;
- Admin API;
- Notification API (таблица может существовать; поведение и endpoints — backlog);
- изменение RouteInstance или прошлых FieldValueVersion через API;
- отдельный CRUD для ApprovalTask или Comment;
- optimistic locking и `ERR_CONFLICT_VERSION`.

BR-29 и связанные in-app notifications остаются backlog. Если notifications будут включены в scope будущей реализации, они должны фиксироваться в одной транзакции с бизнес-событием по BR-29. В текущем Baseline решение, задачи, состояние заявки и HistoryEvent изменяются атомарно по NFR-REL-01.

---

## 2. Источники и терминология

### 2.1. Изученные источники

- `docs/02-requirements/use-cases.md`;
- `docs/02-requirements/functional-requirements.md`;
- `docs/02-requirements/business-rules.md`;
- `docs/02-requirements/rbac-matrix.md`;
- `docs/02-requirements/error-matrix.md`;
- `docs/02-requirements/acceptance-criteria.md`;
- `docs/02-requirements/non-functional-requirements.md`;
- `docs/03-diagrams/bpmn/to-be-request-lifecycle.md`;
- `docs/03-diagrams/bpmn/to-be-approval-stage.md`;
- `docs/03-diagrams/uml/state-request.md`;
- `docs/03-diagrams/uml/sequence-submit.md`;
- `docs/03-diagrams/uml/sequence-approval.md`;
- `docs/03-diagrams/architecture/`;
- `docs/03-diagrams/erd/`;
- `docs/04-api/api-contract-analysis.md`;
- `docs/04-api/openapi.yaml`;
- `docs/consistency-review.md`;
- текущие routes, DTO, domain models, services, error handlers и тесты в `app/` и `tests/`.

### 2.2. Термины

| Термин | Значение |
| :--- | :--- |
| `ApprovalTask` | Задача конкретного согласующего на конкретном этапе и для конкретной FieldValueVersion |
| `RouteInstance` | Неизменяемый экземпляр маршрута заявки, созданный при первом successful submit |
| working values | Изменяемые значения заявки в `draft` и `returned` |
| `FieldValueVersion` | Append-only версия схемы и значений, созданная при successful submit |
| submitted version | Представление FieldValueVersion в API |
| `submit_number` | Порядковый номер successful submit: 1, 2, ... |
| `current_stage` | Текущий этап согласования; после return хранит этап возврата для аудита |
| decision comment | Комментарий согласующего, привязанный к ApprovalTask |
| free comment | Свободный комментарий инициатора к своей заявке |

---

## 3. Общие соглашения API

### 3.1. Аутентификация

Все Approval endpoints требуют JWT access token:

```http
Authorization: Bearer <access_token>
```

Отсутствующий, истёкший или невалидный JWT возвращает `401 ERR_UNAUTHORIZED`. Demo-header не используется, поскольку ADR-AUTH-JWT-01 принят для текущего Core API.

### 3.2. Авторизация

Ролевые права проверяются на backend отдельно для чтения и для decision:

**GET `/approval-tasks/{task_id}`**

1. пользователь имеет роль `approver`;
2. задача существует и назначена текущему пользователю;
3. assignee может читать свою задачу независимо от её статуса: `open`, `completed` или `cancelled` (BR-14).

**POST decision endpoints (`approve`, `return`, `reject`)**

1. пользователь имеет роль `approver`;
2. задача существует и назначена текущему пользователю;
3. задача имеет статус `open`;
4. заявка имеет статус `in_approval`;
5. этап задачи является текущим этапом заявки;
6. инициатор заявки не является текущим согласующим (BR-21).

Права пользователя с несколькими ролями объединяются по BR-16. Роль `admin` сама по себе не даёт право согласования. Пользователь `admin + approver` может действовать только как assignee своей open-задачи и только если он не является инициатором.

Assignee определяется не Approval API: при создании задач система разрешает explicit assignments из RouteInstance (`user` и/или `role`) в конкретных активных пользователей. Auto-routing по оргструктуре не используется (BR-12).

### 3.3. Формат ошибок

Используется фактический формат текущего Core API:

```json
{
  "error_code": "ERR_INVALID_STATE",
  "message": "Действие недоступно для текущего статуса",
  "details": {}
}
```

Новые `error_code` не вводятся. `ERR_CONFLICT` в Error Matrix отсутствует. HTTP `409 Conflict` используется вместе с существующими `ERR_INVALID_STATE` или `ERR_TASK_DONE`. `ERR_DUP_ACTION` в текущем Approval API не используется.

### 3.4. Общие DTO

```json
{
  "current_stage": {
    "number": 1,
    "name": "Line manager"
  }
}
```

```json
{
  "request_type": {
    "id": "11111111-1111-4111-8111-111111111111",
    "name": "Annual leave"
  }
}
```

```json
{
  "user": {
    "id": "33333333-3333-4333-8333-333333333333",
    "full_name": "Иван Петров"
  }
}
```

### 3.5. Terminal status ApprovalTask

Для approve, return и reject применяется единая семантика:

- actor task, по которой assignee принял решение, получает статус `completed`;
- sibling tasks текущего этапа, остававшиеся `open`, получают статус `cancelled`.

`completed` означает, что task завершена собственным решением assignee. `cancelled` означает, что task прекращена без собственного решения вследствие другого решения или завершения этапа.

---

## 4. Сводка Approval endpoints

| Method | Path | Operation name | Actor | Назначение |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/approval-tasks` | `list_approval_tasks` | `approver` | Получить свои открытые задачи |
| GET | `/approval-tasks/{task_id}` | `get_approval_task` | `approver` (assignee) | Получить задачу и полную карточку заявки |
| POST | `/approval-tasks/{task_id}/approve` | `approve_task` | `approver` (assignee) | Согласовать текущий этап |
| POST | `/approval-tasks/{task_id}/return` | `return_task` | `approver` (assignee) | Вернуть заявку на доработку |
| POST | `/approval-tasks/{task_id}/reject` | `reject_task` | `approver` (assignee) | Отклонить заявку |

Отдельный Approval endpoint для комментариев не требуется: decision comment является частью решения. Free comment инициатора относится к `POST /requests/{request_id}/comments`, рассмотренному в §10.

---

## 5. Endpoint contracts

### 5.1. GET `/approval-tasks`

**Operation name:** `list_approval_tasks`

**Swagger summary**

```text
List approval tasks
```

**Swagger description**

```text
UC-07 / FR-APP-01 / BR-14.
Returns open approval tasks assigned to the current approver.
Empty queue is 200 and [].
```

**Actor / role:** `approver`.

**Parameters**

| Parameter | In | Type | Required | Default | Constraints |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `page` | query | integer | no | `1` | `>= 1` |
| `page_size` | query | integer | no | `20` | `1..100` |

Фильтр применяется неявно:

```text
assignee_id = current_user.id
AND status = open
```

Закрытые, отменённые и чужие задачи в очередь не включаются. Сортировка фиксирована:

```text
created_at ASC, id ASC
```

**Request body:** отсутствует.

**Response — `200 OK`**

```json
[
  {
    "id": "66666666-6666-4666-8666-666666666666",
    "request_id": "22222222-2222-4222-8222-222222222222",
    "request_type": {
      "id": "11111111-1111-4111-8111-111111111111",
      "name": "Annual leave"
    },
    "stage": {
      "number": 1,
      "name": "Line manager"
    },
    "status": "open",
    "created_at": "2026-09-21T09:10:00Z"
  }
]
```

`created_at` — неизменяемая дата создания ApprovalTask (`timestamptz`, `NOT NULL`), устанавливаемая при создании задачи. Поле используется в ответе и как первый ключ сортировки. Пустая очередь возвращается как `200` и `[]`.

Ответ — массив элементов без pagination envelope. Поле `total` не возвращается. Для навигации используются существующие query-параметры `page` и `page_size`.

**HTTP statuses и ошибки**

| HTTP | Error code | Условие |
| :---: | :--- | :--- |
| 200 | — | Список получен, включая пустой |
| 401 | `ERR_UNAUTHORIZED` | JWT отсутствует или невалиден |
| 403 | `ERR_FORBIDDEN` | Нет роли `approver` |
| 422 | `ERR_VALIDATION` | Некорректные `page` / `page_size` |
| 500 | `ERR_INTERNAL` | Непредвиденная ошибка |

**Traceability:** UC-07; FR-APP-01; BR-14; BR-16; AC-APP-03.

---

### 5.2. GET `/approval-tasks/{task_id}`

**Operation name:** `get_approval_task`

**Swagger summary**

```text
Get an approval task and request card
```

**Swagger description**

```text
UC-07 / FR-APP-02 / BR-14.
Returns an assigned task in any status and the full snapshot-based request card.
Available actions are returned only for an actionable open task.
```

**Actor / role:** `approver`, только assignee задачи.

**Parameters**

| Parameter | In | Type | Required | Constraints |
| :--- | :--- | :--- | :---: | :--- |
| `task_id` | path | UUID | yes | Идентификатор ApprovalTask |

**Request body:** отсутствует.

**Response — `200 OK`**

```json
{
  "task": {
    "id": "66666666-6666-4666-8666-666666666666",
    "request_id": "22222222-2222-4222-8222-222222222222",
    "stage_number": 1,
    "assignee_id": "77777777-7777-4777-8777-777777777777",
    "status": "open",
    "decision": null,
    "value_version_id": "88888888-8888-4888-8888-888888888888",
    "decided_at": null
  },
  "request": {
    "id": "22222222-2222-4222-8222-222222222222",
    "request_type": {
      "id": "11111111-1111-4111-8111-111111111111",
      "name": "Annual leave"
    },
    "initiator": {
      "id": "33333333-3333-4333-8333-333333333333",
      "full_name": "Иван Петров"
    },
    "status": "in_approval",
    "current_stage": {
      "number": 1,
      "name": "Line manager"
    },
    "created_at": "2026-09-21T09:00:00Z",
    "updated_at": "2026-09-21T09:10:00Z",
    "schema": {
      "request_type_id": "11111111-1111-4111-8111-111111111111",
      "fields": []
    },
    "values": [],
    "value_source": "submitted_version",
    "submit_number": 1,
    "comments": []
  },
  "available_actions": [
    "approve",
    "return",
    "reject"
  ]
}
```

**Правила ответа**

- assignee может читать свою задачу со статусом `open`, `completed` или `cancelled` (BR-14);
- карточка содержит все поля заявки, статус, этап и комментарии;
- `schema` и `values` берутся из FieldValueVersion, указанной в `task.value_version_id`;
- `value_source` всегда равен `submitted_version`;
- `submit_number` соответствует выбранной FieldValueVersion;
- для `completed`/`cancelled` задачи `available_actions = []`;
- для `open` задачи actions `approve`, `return`, `reject` возвращаются только если заявка находится в `in_approval`, этап задачи является текущим и выполняется BR-21;
- если initiator является assignee этой open-задачи, `available_actions = []`;
- независимо от `available_actions`, каждый decision endpoint повторно проверяет BR-21 на backend и при self-approval возвращает `403 ERR_FORBIDDEN_APPROVAL`;
- история заявки не включена в зафиксированный payload до решения Open Question OQ-08.

**HTTP statuses и ошибки**

| HTTP | Error code | Условие |
| :---: | :--- | :--- |
| 200 | — | Своя задача и карточка получены |
| 401 | `ERR_UNAUTHORIZED` | JWT отсутствует или невалиден |
| 403 | `ERR_FORBIDDEN` | Нет роли `approver` |
| 403 | `ERR_FORBIDDEN_APPROVAL` | Задача отсутствует или не назначена текущему пользователю |
| 422 | `ERR_VALIDATION` | `task_id` не является UUID |
| 500 | `ERR_INTERNAL` | Непредвиденная ошибка |

Для отсутствующей и чужой task используется одинаковый ответ `403 ERR_FORBIDDEN_APPROVAL` с message `Нет полномочий на заявку`. API не раскрывает, существует ли task, к которой у пользователя нет полномочий.

**Traceability:** UC-07; FR-APP-02; FR-REQ-04; FR-REQ-05; BR-14; BR-15; BR-26; AC-ACC-06.

---

### 5.3. POST `/approval-tasks/{task_id}/approve`

**Operation name:** `approve_task`

**Swagger summary**

```text
Approve request
```

**Swagger description**

```text
UC-07 / FR-APP-03 / BR-03 / BR-21.
Approves the request at the current approval stage.
Only the assigned approver can approve; self-approval is forbidden.
```

**Actor / role:** `approver`, только assignee своей open-задачи.

**Parameters**

| Parameter | In | Type | Required |
| :--- | :--- | :--- | :---: |
| `task_id` | path | UUID | yes |

**Request body**

```json
{
  "comment": "Approved."
}
```

JSON object обязателен по существующему Stage 4.1 OpenAPI; поле `comment` необязательно, поэтому минимальный body — `{}`.

| Field | Type | Required | Rule |
| :--- | :--- | :---: | :--- |
| `comment` | string | no | Непустой после trim текст сохраняется как decision comment |

Поле `comment` для approve необязательно:

- поле отсутствует → approve без Comment;
- `comment = ""` → approve без Comment;
- `comment = "   "` → approve без Comment;
- непустой после trim текст → создаётся decision comment с нормализованным текстом;
- пустой Comment не создаётся.

**Response — `200 OK`**

```json
{
  "task": {
    "id": "66666666-6666-4666-8666-666666666666",
    "status": "completed",
    "decision": "approve",
    "value_version_id": "88888888-8888-4888-8888-888888888888"
  },
  "request": {
    "id": "22222222-2222-4222-8222-222222222222",
    "status": "in_approval",
    "current_stage": {
      "number": 2,
      "name": "HR"
    }
  }
}
```

Для последнего этапа:

```json
{
  "task": {
    "id": "66666666-6666-4666-8666-666666666666",
    "status": "completed",
    "decision": "approve",
    "value_version_id": "88888888-8888-4888-8888-888888888888"
  },
  "request": {
    "id": "22222222-2222-4222-8222-222222222222",
    "status": "approved",
    "current_stage": {
      "number": 2,
      "name": "HR"
    }
  }
}
```

**Предусловия и side effects**

1. Задача назначена текущему пользователю и имеет статус `open`.
2. Заявка имеет статус `in_approval`.
3. Этап задачи совпадает с `request.current_stage_number`.
4. `request.initiator_id != current_user.id` — обязательная backend-проверка BR-21.
5. Решение привязывается к `task.value_version_id`.
6. Задача победителя становится `completed`, `decision = approve`.
7. Остальные open-задачи текущего этапа становятся `cancelled` (BR-03).
8. Если есть следующий этап RouteInstance, заявка остаётся `in_approval`, меняется `current_stage`, создаются задачи следующего этапа.
9. Если этап последний, заявка становится `approved` (BR-17).
10. Решение, decision comment, задачи, заявка и HistoryEvent фиксируются одной транзакцией.

**HTTP statuses и ошибки**

| HTTP | Error code | Условие |
| :---: | :--- | :--- |
| 200 | — | Approve применён |
| 401 | `ERR_UNAUTHORIZED` | JWT отсутствует или невалиден |
| 403 | `ERR_FORBIDDEN` | Нет роли `approver` |
| 403 | `ERR_FORBIDDEN_APPROVAL` | Task отсутствует, пользователь не assignee или является инициатором |
| 409 | `ERR_TASK_DONE` | Задача уже `completed`/`cancelled` |
| 409 | `ERR_TASK_DONE` | Конкурентный проигравший запрос; side effects не выполняются |
| 409 | `ERR_INVALID_STATE` | Заявка или этап не допускает approve |
| 422 | `ERR_VALIDATION` | Некорректный UUID/body |
| 500 | `ERR_INTERNAL` | Ошибка с rollback транзакции |

**Traceability:** UC-07; FR-APP-03; FR-APP-06; FR-APP-07; FR-AUDIT-02; BR-02; BR-03; BR-14; BR-15; BR-17; BR-21; BR-25; BR-26; AC-APP-04; AC-APP-05; AC-APP-05b; AC-APP-09.

---

### 5.4. POST `/approval-tasks/{task_id}/return`

**Operation name:** `return_task`

**Swagger summary**

```text
Return request for revision
```

**Swagger description**

```text
UC-09 / FR-APP-05 / BR-05 / BR-21 / BR-25.
Returns the request to the initiator for revision.
Only the assigned approver can return; a non-empty comment is required.
```

**Actor / role:** `approver`, только assignee своей open-задачи.

**Parameters**

| Parameter | In | Type | Required |
| :--- | :--- | :--- | :---: |
| `task_id` | path | UUID | yes |

**Request body**

```json
{
  "comment": "Please correct the dates."
}
```

| Field | Type | Required | Rule |
| :--- | :--- | :---: | :--- |
| `comment` | string | yes | После trim должен быть непустым |

**Response — `200 OK`**

```json
{
  "task": {
    "id": "66666666-6666-4666-8666-666666666666",
    "status": "completed",
    "decision": "return",
    "value_version_id": "88888888-8888-4888-8888-888888888888"
  },
  "request": {
    "id": "22222222-2222-4222-8222-222222222222",
    "status": "returned",
    "current_stage": {
      "number": 2,
      "name": "HR"
    }
  }
}
```

Actor task получает статус `completed`. Все sibling open tasks текущего этапа получают статус `cancelled`.

**Предусловия и side effects**

1. Задача назначена текущему пользователю и имеет статус `open`.
2. Заявка находится в `in_approval`.
3. Этап задачи совпадает с `request.current_stage_number`.
4. Self-approval запрещён по BR-21.
5. Создаётся decision comment, привязанный к задаче.
6. Заявка переходит в `returned`.
7. Номер этапа возврата сохраняется в `current_stage` для аудита.
8. Actor task становится `completed`; sibling open tasks текущего этапа становятся `cancelled`.
9. RouteInstance и существующие FieldValueVersion не изменяются.
10. Решение, comment, задачи, заявка и HistoryEvent фиксируются одной транзакцией.
11. После return согласующий сохраняет read-доступ через свою закрытую задачу (BR-14), но больше не имеет доступных decision actions.

**HTTP statuses и ошибки**

| HTTP | Error code | Условие |
| :---: | :--- | :--- |
| 200 | — | Return применён |
| 401 | `ERR_UNAUTHORIZED` | JWT отсутствует или невалиден |
| 403 | `ERR_FORBIDDEN` | Нет роли `approver` |
| 403 | `ERR_FORBIDDEN_APPROVAL` | Task отсутствует, пользователь не assignee или является инициатором |
| 409 | `ERR_TASK_DONE` | Задача уже имеет статус `completed`/`cancelled` |
| 409 | `ERR_TASK_DONE` | Конкурентный проигравший запрос; side effects не выполняются |
| 409 | `ERR_INVALID_STATE` | Заявка или этап не допускает return |
| 422 | `ERR_VALIDATION` | Comment отсутствует/пуст после trim либо body невалиден |
| 500 | `ERR_INTERNAL` | Ошибка с rollback транзакции |

**Traceability:** UC-09; FR-APP-05; FR-REQ-08; FR-REQ-09; FR-AUDIT-02; BR-05; BR-06; BR-15; BR-21; BR-25; BR-26; AC-APP-07; AC-APP-07b.

---

### 5.5. POST `/approval-tasks/{task_id}/reject`

**Operation name:** `reject_task`

**Swagger summary**

```text
Reject request
```

**Swagger description**

```text
UC-08 / FR-APP-04 / BR-04 / BR-21 / BR-25.
Rejects the request and completes its approval route.
Only the assigned approver can reject; a non-empty comment is required.
```

**Actor / role:** `approver`, только assignee своей open-задачи.

**Parameters**

| Parameter | In | Type | Required |
| :--- | :--- | :--- | :---: |
| `task_id` | path | UUID | yes |

**Request body**

```json
{
  "comment": "Required information is missing."
}
```

| Field | Type | Required | Rule |
| :--- | :--- | :---: | :--- |
| `comment` | string | yes | После trim должен быть непустым |

**Response — `200 OK`**

```json
{
  "task": {
    "id": "66666666-6666-4666-8666-666666666666",
    "status": "completed",
    "decision": "reject",
    "value_version_id": "88888888-8888-4888-8888-888888888888"
  },
  "request": {
    "id": "22222222-2222-4222-8222-222222222222",
    "status": "rejected",
    "current_stage": {
      "number": 2,
      "name": "HR"
    }
  }
}
```

Actor task получает статус `completed`. Все sibling open tasks текущего этапа получают статус `cancelled`.

**Предусловия и side effects**

1. Задача назначена текущему пользователю и имеет статус `open`.
2. Заявка находится в `in_approval`.
3. Этап задачи совпадает с `request.current_stage_number`.
4. Self-approval запрещён по BR-21.
5. Создаётся обязательный decision comment.
6. Заявка переходит в терминальный статус `rejected`.
7. Actor task становится `completed`; sibling open tasks текущего этапа становятся `cancelled`; задачи следующих этапов не создаются.
8. Решение привязывается к текущей FieldValueVersion.
9. Решение, comment, задачи, заявка и HistoryEvent фиксируются одной транзакцией.

**HTTP statuses и ошибки**

| HTTP | Error code | Условие |
| :---: | :--- | :--- |
| 200 | — | Reject применён |
| 401 | `ERR_UNAUTHORIZED` | JWT отсутствует или невалиден |
| 403 | `ERR_FORBIDDEN` | Нет роли `approver` |
| 403 | `ERR_FORBIDDEN_APPROVAL` | Task отсутствует, пользователь не assignee или является инициатором |
| 409 | `ERR_TASK_DONE` | Задача уже имеет статус `completed`/`cancelled` |
| 409 | `ERR_TASK_DONE` | Конкурентный проигравший запрос; side effects не выполняются |
| 409 | `ERR_INVALID_STATE` | Заявка или этап не допускает reject |
| 422 | `ERR_VALIDATION` | Comment отсутствует/пуст после trim либо body невалиден |
| 500 | `ERR_INTERNAL` | Ошибка с rollback транзакции |

**Traceability:** UC-08; FR-APP-04; FR-AUDIT-02; BR-04; BR-15; BR-21; BR-25; BR-26; AC-APP-06; AC-APP-06b.

---

## 6. RBAC

Матрица показывает права отдельной роли. При нескольких ролях права объединяются по BR-16, но ownership, assignee и BR-21 продолжают применяться.

| Действие | employee | approver | admin |
| :--- | :---: | :---: | :---: |
| Просмотр своей заявки | Да, только own | Нет по этой роли | Нет |
| Редактирование `draft` / `returned` | Да, только own | Нет | Нет |
| Submit своей заявки | Да, только own | Нет | Нет |
| Просмотр очереди согласования | Нет | Да, только own open tasks | Нет |
| Просмотр заявки на согласовании | Нет | Да, только via own task, включая completed/cancelled | Нет |
| Approve | Нет | Да, только own open task | Нет |
| Return | Нет | Да, только own open task | Нет |
| Reject | Нет | Да, только own open task | Нет |
| Добавление комментария | Free comment к own request | Decision comment в составе решения | Нет |

### 6.1. BR-21 — запрет самосогласования

Обязательное условие decision endpoints:

```text
request.initiator_id != current_user.id
```

Условие проверяется на backend непосредственно перед мутацией. Скрытие кнопки клиентом не является проверкой доступа. Нарушение возвращает:

```text
403 ERR_FORBIDDEN_APPROVAL
```

Правило действует даже если инициатор назначен assignee лично или через роль и даже если у пользователя одновременно есть роли `employee`, `approver` и/или `admin`.

---

## 7. State transitions

### 7.1. Матрица переходов

| From | To | Actor | Action | Endpoint | Preconditions | Возможные ошибки | Текущая реализация |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `draft` | `in_approval` | employee/initiator | submit | `POST /requests/{request_id}/submit` | Own request; valid live schema; active type; valid route | `ERR_NOT_FOUND`, `ERR_INVALID_STATE`, `ERR_INACTIVE_TYPE`, `ERR_ROUTE_CONFIG`, `ERR_VALIDATION` | Реализовано |
| `returned` | `in_approval` | employee/initiator | resubmit | `POST /requests/{request_id}/submit` | Own request; valid working values; тот же RouteInstance; новая FieldValueVersion | те же, что submit | Реализовано |
| `in_approval` | `in_approval` | approver/assignee | approve непоследнего этапа | `POST /approval-tasks/{task_id}/approve` | Own open task; current stage; not initiator | `ERR_FORBIDDEN_APPROVAL`, `ERR_TASK_DONE`, `ERR_INVALID_STATE` | Отсутствует |
| `in_approval` | `approved` | approver/assignee | approve последнего этапа | `POST /approval-tasks/{task_id}/approve` | Те же + последний этап RouteInstance | те же | Отсутствует |
| `in_approval` | `returned` | approver/assignee | return | `POST /approval-tasks/{task_id}/return` | Own open task; not initiator; non-empty comment | те же + `ERR_VALIDATION` | Отсутствует |
| `in_approval` | `rejected` | approver/assignee | reject | `POST /approval-tasks/{task_id}/reject` | Own open task; not initiator; non-empty comment | те же + `ERR_VALIDATION` | Отсутствует |

### 7.2. Дополнительные правила переходов

- Approve непоследнего этапа не меняет `status`: заявка остаётся `in_approval`, меняется только `current_stage`.
- `approved` и `rejected` — терминальные статусы.
- После return этап возврата сохраняется для аудита.
- Resubmit после return всегда начинается с первого этапа существующего RouteInstance.
- Переходы и связанные изменения ApprovalTask/HistoryEvent атомарны по NFR-REL-01.
- Переход в `cancelled` существует в требованиях для `draft`/`returned`, но не является частью Approval API и в текущем backend ещё не реализован.

---

## 8. Snapshot, working values и `submit_number`

### 8.1. Правило чтения

Approval API не читает working values для принятия решения. Согласующий видит:

```text
value_source = submitted_version
```

`schema` и `values` берутся из FieldValueVersion, связанной с ApprovalTask через `value_version_id`. Decision также сохраняется с этой версией. Изменение live-схемы, working values или live-маршрута не должно менять уже созданную задачу и отображаемую ей submitted version.

### 8.2. Сценарий submit #1 → return → submit #2

| Шаг | Request status | Working values | FieldValueVersion | `submit_number` | Что видит approver |
| :--- | :--- | :--- | :--- | :---: | :--- |
| Первый successful submit | `in_approval` | Сохраняются отдельно | Создаётся version #1 | 1 | Schema/values version #1 |
| Return | `returned` | Доступны для редактирования | Version #1 неизменна | 1 | Прошлая задача остаётся связана с #1 |
| Редактирование | `returned` | Меняются по live-схеме | Новая версия ещё не создаётся | 1 | Согласование не выполняется |
| Второй successful submit | `in_approval` | Копируются в новую версию | Создаётся version #2 | 2 | Новые задачи показывают version #2 |

При submit #2:

- RouteInstance остаётся тем же;
- `current_stage` устанавливается на первый этап;
- создаются новые задачи первого этапа;
- каждая новая задача ссылается на FieldValueVersion #2;
- решения по #1 не переносятся на #2;
- FieldValueVersion #1 и связанные решения остаются append-only и доступны через историю;
- следующий `submit_number` вычисляется как номер очередного successful submit.

Failed submit не создаёт FieldValueVersion и не увеличивает `submit_number`.

---

## 9. First-approve-wins и конкурентный approve

### 9.1. Контракт результата

Для двух assignee одного этапа:

```text
Approver A ──┐
             ├── approve ──→ один approval stage
Approver B ──┘
```

- ровно один запрос успешно завершает этап и получает `200 OK`;
- задача победителя становится `completed` с `decision = approve`;
- остальные open-задачи этапа становятся `cancelled`;
- создаётся не более одного набора задач следующего этапа;
- либо выполняется ровно один переход заявки в `approved`;
- второй конкурентный запрос не выполняет никаких side effects и получает `409 ERR_TASK_DONE`;
- `ERR_DUP_ACTION` в текущем Approval API не используется.

### 9.2. Persistence-level condition

Реализация должна обеспечить единственного победителя условием на persistence level:

```text
task.id = task_id
AND task.assignee_id = current_user.id
AND task.status = open
AND request.status = in_approval
AND task.stage_number = request.current_stage_number
```

Условный переход `open → completed` должен затронуть ровно одну строку победителя. Это может быть обеспечено блокировкой строк в транзакции, условным atomic update или эквивалентной сериализацией. Проверки только в памяти приложения недостаточно.

В той же транзакции выполняются:

1. completion задачи победителя;
2. cancellation sibling open tasks;
3. создание задач следующего этапа или финальный статус `approved`;
4. optional decision comment;
5. HistoryEvent;
6. notification, только если она позже войдёт в scope BR-29.

Если условный переход не затронул строку, повторная мутация запрещена; запрос получает `409 ERR_TASK_DONE` без side effects.

---

## 10. Comments

### 10.1. Виды комментариев

| Kind | Кто добавляет | Когда | Обязательность | API |
| :--- | :--- | :--- | :--- | :--- |
| `decision` | approver/assignee | В составе approve | Необязателен | `POST .../approve` |
| `decision` | approver/assignee | В составе return | Обязателен | `POST .../return` |
| `decision` | approver/assignee | В составе reject | Обязателен | `POST .../reject` |
| `free` | employee/initiator | К своей заявке; явно разрешён `in_approval` | Непустой text | `POST /requests/{request_id}/comments` |

Decision comment нельзя создавать отдельным endpoint'ом: он должен быть атомарно связан с решением. Отдельный `GET /comments` также не требуется: комментарии возвращаются в `comments[]` полной карточки.

### 10.2. DTO комментария

```json
{
  "id": "99999999-9999-4999-8999-999999999999",
  "kind": "decision",
  "text": "Please correct the dates.",
  "author": {
    "id": "77777777-7777-4777-8777-777777777777",
    "full_name": "Анна Соколова"
  },
  "approval_task_id": "66666666-6666-4666-8666-666666666666",
  "created_at": "2026-09-21T09:20:00Z"
}
```

| Field | Type | Required | Meaning |
| :--- | :--- | :---: | :--- |
| `id` | UUID | yes | Идентификатор Comment |
| `kind` | `free` / `decision` | yes | Вид комментария |
| `text` | string | yes | Непустой текст сохранённого комментария |
| `author` | UserRef | yes | `id`, `full_name` автора |
| `approval_task_id` | UUID / null | yes | Task для decision; `null` для free |
| `created_at` | datetime | yes | Время создания |

Порядок `comments[]` не зафиксирован требованиями и остаётся OQ-07. До решения клиент не должен полагаться на неявный порядок.

### 10.3. Связанный free-comment endpoint

Free comments нужны по BR-28, но endpoint относится к Request API, а не к Approval Engine.

**Method/path:** `POST /requests/{request_id}/comments`  
**Operation name:** `add_request_comment`

**Swagger summary**

```text
Add a comment to a request
```

**Swagger description**

```text
UC-06 / FR-REQ-06 / BR-28.
Adds a free comment to the current employee's own request.
The comment text must be non-empty.
```

Body:

```json
{
  "text": "Additional information."
}
```

Endpoint предусмотрен Stage 4.1 и реализован в Stage 6.1 (`POST /requests/{request_id}/comments`). Требования явно разрешают free comment в `in_approval`; полный список других допустимых статусов остаётся RR-COMMENT-01.

---

## 11. Error mapping

### 11.1. Применяемые error codes

| Error code | HTTP | Approval API condition |
| :--- | :---: | :--- |
| `ERR_UNAUTHORIZED` | 401 | Нет валидного JWT |
| `ERR_FORBIDDEN` | 403 | Роль не разрешает endpoint |
| `ERR_FORBIDDEN_APPROVAL` | 403 | Task отсутствует, пользователь не assignee или выполняется self-approval; message: `Нет полномочий на заявку` |
| `ERR_INVALID_STATE` | 409 | Состояние request или текущего stage не допускает действие |
| `ERR_TASK_DONE` | 409 | Task уже имеет статус `completed`/`cancelled` |
| `ERR_VALIDATION` | 422 | Невалидный UUID/body, отсутствующий или пустой required comment |
| `ERR_INTERNAL` | 500 | Непредвиденная ошибка; mutation rollback |

### 11.2. Decision conflict mapping

- закрытая task со статусом `completed` или `cancelled` → `409 ERR_TASK_DONE`;
- недопустимое состояние request или несоответствие текущего stage → `409 ERR_INVALID_STATE`;
- конкурентный проигравший запрос → `409 ERR_TASK_DONE`;
- проигравший конкурентный запрос не выполняет никаких side effects.

### 11.3. Коды, которые не используются

- `ERR_CONFLICT` не существует в Error Matrix и не вводится.
- `ERR_CONFLICT_VERSION` имеет статус Future / Reserved и не используется в MVP.
- `ERR_DUP_ACTION` в текущем Approval API не используется.
- `ERR_NOT_FOUND` не используется для поиска ApprovalTask: отсутствующая и чужая task возвращают одинаковый `403 ERR_FORBIDDEN_APPROVAL`.
- `ERR_ROUTE_CONFIG` относится к submit, а не к decision: Approval Engine читает уже созданный RouteInstance.
- `ERR_INACTIVE_TYPE` не применяется к решениям по существующей заявке.

---

## 12. Traceability

| API | UC | FR | BR |
| :--- | :--- | :--- | :--- |
| GET `/approval-tasks` | UC-07 | FR-APP-01 | BR-14, BR-16 |
| GET `/approval-tasks/{task_id}` | UC-07 | FR-APP-02, FR-REQ-04, FR-REQ-05 | BR-14, BR-15, BR-26 |
| POST `/approval-tasks/{task_id}/approve` | UC-07 | FR-APP-03, FR-APP-06, FR-APP-07, FR-AUDIT-02 | BR-02, BR-03, BR-15, BR-17, BR-21, BR-25, BR-26 |
| POST `/approval-tasks/{task_id}/return` | UC-09 | FR-APP-05, FR-REQ-08, FR-REQ-09, FR-AUDIT-02 | BR-05, BR-06, BR-15, BR-21, BR-25, BR-26 |
| POST `/approval-tasks/{task_id}/reject` | UC-08 | FR-APP-04, FR-AUDIT-02 | BR-04, BR-15, BR-21, BR-25, BR-26 |
| POST `/requests/{request_id}/comments` (related) | UC-06 | FR-REQ-06 | BR-28 |

Все предлагаемые операции связаны с существующими UC/FR/BR. Новые requirement ID не созданы.

---

## 13. Gaps и противоречия

Следующие расхождения зафиксированы без изменения требований:

1. ~~**Approval API отсутствует в backend.**~~ **Closed.** Queue/detail/decision реализованы.
2. **Auth contract устарел в Stage 4.1.** `api-contract-analysis.md` описывает demo-header, а текущий runtime и ADR-AUTH-JWT-01 используют JWT.
3. ~~**Comments не подключены.**~~ **Closed (Stage 6.1).** Free comments и отдача в карточке реализованы; decision comments — через Approval API.
4. **Approver не может открыть Request API card.** `GET /requests/{request_id}` защищён ролью `employee` и ownership инициатора. Stage 4.1 предлагает aggregate card через task, но RR-API-03 не закрыт.
5. ~~**Смежные API отсутствуют.**~~ **Closed (Stage 6.1).** `POST .../comments`, `POST .../cancel` и `GET .../history` реализованы.
6. ~~**Дата задачи отсутствует в backend model.**~~ **Closed.** `ApprovalTask.created_at` есть в модели и миграции.
7. **Error envelope.** Stage 4.1 помечает envelope как recommended/open, но текущий backend уже использует обязательный `{error_code, message, details}`.
8. **Notifications.** BR-29 находится в backlog; Notification API и транзакционная запись notification в текущий Approval contract не входят.
9. **OpenAPI расходится с требуемым стилем.** Существующие Approval descriptions в `openapi.yaml` длиннее нового правила 1–3 коротких предложений; этот документ задаёт краткие Swagger descriptions, не изменяя YAML.

---

## 14. Decisions and remaining Open Questions

### 14.1. Зафиксированные решения

#### OQ-02 — Authorization на task (RESOLVED)

- `GET /approval-tasks/{task_id}` возвращает `403 ERR_FORBIDDEN_APPROVAL` и для чужой, и для отсутствующей task.
- Decision endpoints используют то же правило.
- Message: `Нет полномочий на заявку`.
- API не раскрывает, существует ли task, к которой у пользователя нет полномочий.

#### OQ-03 — Terminal status ApprovalTask (RESOLVED)

- approve: actor task → `completed`, sibling open tasks → `cancelled`;
- return: actor task → `completed`, sibling open tasks → `cancelled`;
- reject: actor task → `completed`, sibling open tasks → `cancelled`.

`completed` означает завершение task собственным решением assignee. `cancelled` означает прекращение task без собственного решения вследствие другого решения или завершения этапа.

#### OQ-04 — `ApprovalTask.created_at` (RESOLVED)

`ApprovalTask.created_at` имеет тип `timestamptz`, обязателен (`NOT NULL`), устанавливается при создании task и после создания не изменяется. Поле является датой создания approval task и используется для сортировки очереди.

#### OQ-06 — Concurrent decision (RESOLVED)

При first-approve-wins конкурентный проигравший запрос получает `409 ERR_TASK_DONE` и не выполняет никаких side effects. `ERR_DUP_ACTION` в текущем Approval API не используется.

#### OQ-09 — Approve comment (RESOLVED)

Comment для approve optional. Отсутствующее поле, `""` и строка только из whitespace означают approve без Comment. Непустой после trim текст сохраняется как decision comment. Пустой Comment не создаётся.

#### OQ-10 — Approval queue (RESOLVED)

`GET /approval-tasks` возвращает массив без pagination envelope и без `total`. Используются `page` и `page_size`. Сортировка: `created_at ASC, id ASC`.

### 14.2. Remaining Open Questions

Следующие вопросы остаются открытыми и этим решением не изменяются.

#### OQ-01 — Approver card route (RR-API-03)

Достаточно ли aggregate `GET /approval-tasks/{task_id}`, или approver также должен получить доступ к `GET /requests/{request_id}`? Настоящий контракт использует aggregate и не меняет существующий Request API до решения вопроса.

#### OQ-05 — Допустимые статусы free comments (RR-COMMENT-01)

BR-28 однозначно разрешает free comments инициатора в `in_approval`. FR-REQ-06 сформулирован шире («в статусах, включая `in_approval`»), но полный набор статусов не указан.

#### OQ-07 — Порядок `comments[]`

Требования не определяют ascending/descending порядок комментариев. В отличие от request history, хронологический порядок для comments не зафиксирован.

#### OQ-08 — История в aggregate task card

FR-APP-02 упоминает историю «в рамках прав», а Stage 4.1 выносит её в отдельный `GET /requests/{request_id}/history`. Нужно подтвердить, возвращает ли task card саму историю или только обеспечивает доступ к отдельному endpoint.

---

## 15. Итоговые ограничения реализации

Реализация Approval API:

- использует только существующие статусы и decision enum;
- читает RouteInstance и FieldValueVersion, не изменяя их;
- проверяет role, assignee, open status, current stage и BR-21 на backend;
- привязывает каждое решение к FieldValueVersion задачи;
- обеспечивает first-approve-wins на persistence level;
- выполняет decision, task updates, request transition и HistoryEvent атомарно;
- не создаёт новые error codes;
- не предоставляет admin право approve без роли `approver` и собственной задачи;
- не расширяет scope notifications до отдельного решения по backlog BR-29.
