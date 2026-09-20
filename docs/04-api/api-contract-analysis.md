# API Contract Analysis

**Продукт:** Employee Service

**Этап:** Stage 4.1

**Статус:** аналитический документ для подготовки API-контракта

**Основание:** Baseline v1.0 требований и диаграмм

## 1. Scope

Документ определяет предлагаемый REST-контракт MVP на уровне операций, payload, проверок, RBAC и ошибок. Он не является OpenAPI-спецификацией и не изменяет зафиксированную бизнес-логику.

### 1.1. В scope

- каталог активных типов заявок;
- создание, редактирование, submit/resubmit, просмотр и отмена своих заявок;
- свободные комментарии инициатора;
- очередь и карточка задач согласования;
- approve, reject, return;
- история заявки и версии значений;
- RBAC ролей `employee` и `approver`, а также зафиксированное в RBAC исключение чтения каталога для `admin`;
- snapshot- и lifecycle-ограничения.

### 1.2. Вне scope Baseline

- login/password, JWT и профиль;
- Admin API для типов, полей, маршрутов, назначений и справочников;
- in-app уведомления;
- admin-реестр заявок;
- optimistic locking и `ERR_CONFLICT_VERSION`;
- создание задач, RouteInstance, FieldValueVersion и HistoryEvent напрямую клиентом;
- OpenAPI и backend-реализация.

### 1.3. Общие соглашения анализа

- Пути предложены по REST-соглашению: существительные во множественном числе, действия — подресурсы.
- Идентификаторы ресурсов имеют логический тип `UUID` согласно ERD Data Dictionary.
- Текущий пользователь и его роли определяются техническим demo-header stub по ADR-AUTH-DEMO-01. Имена заголовков не зафиксированы — см. §10.
- Права пользователя с несколькими ролями объединяются (BR-16).
- Error Matrix рекомендует envelope `{ error_code, message, details }` только как ориентир для будущего контракта; обязательный формат ещё не зафиксирован — см. §10.
- Списки заявок и задач поддерживают пагинацию; `page_size` имеет default 20 и максимум 100 (NFR-PERF-03). `page_size = 101` → `ERR_VALIDATION`.
- Способ навигации между страницами и response envelope в существующих документах не зафиксированы — см. §10.

## 2. Baseline API Operations

| Method | Path | UC | FR | Roles | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GET | `/request-types` | UC-03 | FR-CAT-01 | employee, admin | Получить каталог активных типов |
| GET | `/request-types/{type_id}` | UC-03 | FR-CAT-02 | employee, admin | Получить описание активного типа |
| GET | `/request-types/{type_id}/schema` | UC-03, UC-04 | FR-CAT-03 | employee, admin | Получить актуальную схему формы |
| POST | `/requests` | UC-04 | FR-REQ-01 | employee | Создать draft выбранного типа |
| GET | `/requests` | UC-06 | FR-CAB-02, FR-REQ-05 | employee | Получить список своих заявок |
| GET | `/requests/{request_id}` | UC-06 | FR-REQ-04, FR-REQ-05, FR-REQ-06 | employee (own) | Получить карточку своей заявки |
| PATCH | `/requests/{request_id}` | UC-04, UC-09 | FR-REQ-02 | employee (initiator) | Сохранить working values по live-схеме |
| POST | `/requests/{request_id}/submit` | UC-05 | FR-REQ-03, FR-REQ-09 | employee (initiator) | Выполнить submit или resubmit |
| POST | `/requests/{request_id}/cancel` | UC-10 | FR-REQ-07 | employee (initiator) | Отменить draft/returned |
| POST | `/requests/{request_id}/comments` | UC-06 | FR-REQ-06 | employee (initiator) | Добавить свободный комментарий |
| GET | `/requests/{request_id}/history` | UC-14 | FR-AUDIT-01 | employee (own), approver (via own task) | Получить события и прошлые версии |
| GET | `/approval-tasks` | UC-07 | FR-APP-01 | approver | Получить свои открытые задачи |
| GET | `/approval-tasks/{task_id}` | UC-07 | FR-APP-02, FR-REQ-04, FR-REQ-05 | approver (assignee) | Получить задачу и полную карточку заявки |
| POST | `/approval-tasks/{task_id}/approve` | UC-07 | FR-APP-03, FR-APP-06, FR-APP-07 | approver (assignee) | Согласовать текущий этап |
| POST | `/approval-tasks/{task_id}/reject` | UC-08 | FR-APP-04 | approver (assignee) | Отклонить заявку |
| POST | `/approval-tasks/{task_id}/return` | UC-09 | FR-APP-05, FR-REQ-08 | approver (assignee) | Вернуть заявку на доработку |

**Количество Baseline operations: 16.**

FR-AUDIT-02, FR-APP-06, FR-APP-07 и FR-REQ-08 являются системными side effects, а не самостоятельными клиентскими операциями. Они выполняются атомарно внутри соответствующих submit/decision операций.

## 3. Request/Response Contracts

Ниже перечислены поля аналитического уровня. Физические типы хранения и JSON Schema будут определены на этапе OpenAPI/реализации.

### 3.1. GET `/request-types`

**Request**

- Body: отсутствует.
- Query: отсутствует; операция всегда фильтрует `is_active = true`.

**Response**

- `200 OK`.
- Body: массив `{ id, name, description }`.
- При отсутствии активных типов: `200 OK` и `[]`.

**Validation**

- Возвращаются только активные типы (BR-10, AC-CAT-01).

**Errors**

- `ERR_FORBIDDEN` — роль не разрешает просмотр.
- `ERR_INTERNAL` — непредвиденная ошибка.

### 3.2. GET `/request-types/{type_id}`

**Request**

- Path: `type_id: UUID`.
- Body: отсутствует.

**Response**

- `200 OK`.
- Body: `{ id, name, description }`.

**Validation**

- Тип должен существовать и быть активным.

**Errors**

- `ERR_NOT_FOUND` (`404`) — тип не существует.
- `ERR_NOT_FOUND` (`404`) — тип неактивен; расхождение с формулировкой FR-CAT-02 вынесено в §10.
- `ERR_FORBIDDEN` (`403`) — роль не разрешает просмотр.
- `ERR_INTERNAL` (`500`).

### 3.3. GET `/request-types/{type_id}/schema`

**Request**

- Path: `type_id: UUID`.
- Body: отсутствует.

**Response**

- `200 OK`.
- Body: `{ request_type_id, fields }`.
- `fields[]`: `{ code, name, data_type, required, order_no, dictionary_id }`.
- `data_type`: `text | date | number | catalog`.
- Пустой `fields` допустим.

**Validation**

- Поля упорядочены по `order_no`.
- Схема является live-конфигурацией на момент запроса.
- Тип должен быть активным.

**Errors**

- `ERR_NOT_FOUND` (`404`) — тип не существует.
- `ERR_NOT_FOUND` (`404`) — тип неактивен; расхождение с формулировкой FR-CAT-02 вынесено в §10.
- `ERR_FORBIDDEN` (`403`).
- `ERR_INTERNAL` (`500`).

### 3.4. POST `/requests`

**Request**

- Body: `{ request_type_id: UUID }`.
- `initiator_id` клиент не передаёт: он определяется текущим пользователем.

**Response**

- `201 Created`.
- Body: `{ id, request_type_id, initiator_id, status: "draft", current_stage_number: null, created_at, updated_at }`.

**Validation**

- Текущий пользователь имеет роль `employee`.
- Тип существует и активен.
- Создание RouteInstance и FieldValueVersion не выполняется.
- Событие создания пишется атомарно с Request (FR-AUDIT-02, BR-24).

**Errors**

- `ERR_INACTIVE_TYPE` (`409`) — тип неактивен.
- `ERR_NOT_FOUND` (`404`) — тип не существует.
- `ERR_VALIDATION` (`422`) — некорректный `request_type_id`.
- `ERR_FORBIDDEN` (`403`).
- `ERR_INTERNAL` (`500`).

### 3.5. GET `/requests`

**Request**

- Query: `status?` — одно из `draft | in_approval | returned | approved | rejected | cancelled`.
- Query: `page_size?` — default 20, максимум 100.
- Остальные параметры навигации по страницам не зафиксированы — см. §10.
- Body: отсутствует.

**Response**

- `200 OK`.
- Body: пагинированное представление; envelope и метаданные навигации не зафиксированы — см. §10.
- Каждый элемент списка содержит `{ id, request_type: { id, name }, status, current_stage, created_at, updated_at }`.
- `current_stage`: `{ number, name } | null`; обязателен при `in_approval`.
- Пустой список допустим.

**Validation**

- Возвращаются только заявки, где текущий пользователь — `initiator_id` (BR-01).
- Фильтр `status` не расширяет область видимости.

**Errors**

- `ERR_VALIDATION` (`422`) — неизвестный status или невалидная пагинация.
- `ERR_FORBIDDEN` (`403`) — нет роли `employee`.
- `ERR_INTERNAL` (`500`).

### 3.6. GET `/requests/{request_id}`

**Request**

- Path: `request_id: UUID`.
- Body: отсутствует.

**Response**

- `200 OK`.
- Body:
  - `{ id, request_type, initiator, status, current_stage, created_at, updated_at }`;
  - `schema` и `values`;
  - `value_source: "working" | "submitted_version"`;
  - `submit_number` при snapshot-based отображении;
  - `comments[]`: `{ id, kind, text, author, approval_task_id, created_at }`.

**Validation**

- Endpoint предназначен для своей заявки employee.
- Для `draft`/`returned` показываются working values по live-схеме.
- Для `in_approval`, `approved`, `rejected` показывается последняя FieldValueVersion.
- Чужая заявка скрывается через `404`, без раскрытия факта существования.
- Правило показа значений для `cancelled` после `returned` не определено — см. §10.

**Errors**

- `ERR_NOT_FOUND` (`404`) — заявка отсутствует или чужая.
- `ERR_FORBIDDEN` (`403`) — роль не разрешает операцию.
- `ERR_INTERNAL` (`500`).

### 3.7. PATCH `/requests/{request_id}`

**Request**

- Path: `request_id: UUID`.
- Body: `{ values: [{ field_code, value }] }`.
- `value` — логический носитель значения; формат проверяется по `data_type`.

**Response**

- `200 OK`.
- Body: `{ id, status, schema, values, updated_at }`, где `schema` — текущая live-схема.

**Validation**

- Только инициатор.
- Только `draft` или `returned`.
- Коды, типы значений и catalog values проверяются по live-схеме.
- Частично заполненный draft допустим; обязательность полностью проверяется при submit.
- FieldValueVersion не изменяется и не создаётся.
- При изменении `returned` фиксируется HistoryEvent (BR-24).

**Errors**

- `ERR_NOT_FOUND` (`404`) — заявка отсутствует или чужая.
- `ERR_INVALID_STATE` (`409`) — статус не `draft`/`returned`.
- `ERR_VALIDATION` (`422`) — неизвестный field code, неверный формат/тип/catalog value.
- `ERR_FORBIDDEN` (`403`) — роль не разрешает операцию.
- `ERR_INTERNAL` (`500`).

### 3.8. POST `/requests/{request_id}/submit`

**Request**

- Path: `request_id: UUID`.
- Body: отсутствует.

**Response**

- `200 OK`.
- Body: `{ id, status: "in_approval", current_stage, submit_number, updated_at }`.

**Validation**

- Только инициатор; исходный статус только `draft` или `returned`.
- Тип активен.
- Working values валидируются по live-схеме, включая обязательные поля.
- Live-маршрут валидируется: минимум один этап и минимум одно explicit role/user assignment на каждом этапе (BR-12, BR-18).
- Первый successful submit создаёт RouteInstance один раз.
- Каждый successful submit создаёт новую append-only FieldValueVersion.
- Resubmit не перестраивает RouteInstance, устанавливает этап 1 и создаёт новые задачи этапа 1.
- Request, snapshots, задачи и HistoryEvent фиксируются атомарно.

**Errors**

- `ERR_NOT_FOUND` (`404`) — заявка отсутствует или чужая.
- `ERR_INVALID_STATE` (`409`) — статус не `draft`/`returned`.
- `ERR_INACTIVE_TYPE` (`409`) — тип неактивен.
- `ERR_ROUTE_CONFIG` (`409`) — нет этапов или назначений.
- `ERR_VALIDATION` (`422`) — значения не соответствуют live-схеме.
- `ERR_FORBIDDEN` (`403`).
- `ERR_INTERNAL` (`500`) — транзакция откатывается.

### 3.9. POST `/requests/{request_id}/cancel`

**Request**

- Path: `request_id: UUID`.
- Body: отсутствует.

**Response**

- `200 OK`.
- Body: `{ id, status: "cancelled", updated_at }`.

**Validation**

- Только инициатор.
- Только `draft` или `returned`.
- Смена статуса и HistoryEvent атомарны.

**Errors**

- `ERR_NOT_FOUND` (`404`) — заявка отсутствует или чужая.
- `ERR_INVALID_STATE` (`409`) — иной статус.
- `ERR_FORBIDDEN` (`403`).
- `ERR_INTERNAL` (`500`).

### 3.10. POST `/requests/{request_id}/comments`

**Request**

- Path: `request_id: UUID`.
- Body: `{ text: string }`.
- `kind`, `author_id` и `approval_task_id` клиент не задаёт; создаётся `kind = "free"`.

**Response**

- `201 Created`.
- Body: `{ id, request_id, author_id, kind: "free", text, created_at }`.

**Validation**

- Только инициатор своей заявки.
- `text` после trim непустой.
- Свободный комментарий явно допустим в `in_approval`; полный список допустимых статусов не зафиксирован — см. §10.

**Errors**

- `ERR_NOT_FOUND` (`404`) — заявка отсутствует или чужая.
- `ERR_VALIDATION` (`422`) — пустой текст.
- `ERR_FORBIDDEN` (`403`) — роль не разрешает операцию.
- `ERR_INTERNAL` (`500`).

### 3.11. GET `/requests/{request_id}/history`

**Request**

- Path: `request_id: UUID`.
- Body: отсутствует.

**Response**

- `200 OK`.
- Body:
  - `events[]`: `{ id, actor, action, from_state, to_state, comment, at, value_version_id? }`;
  - `field_value_versions[]`: `{ id, submit_number, schema_document, values_document, created_at }`.
- События выдаются в хронологическом порядке; прошлые решения трассируются к соответствующей версии.

**Validation**

- Employee — только собственная заявка.
- Approver — заявка, по которой у него есть собственная задача любого статуса.
- История read-only; HistoryEvent и FieldValueVersion не изменяются через API.

**Errors**

- `ERR_NOT_FOUND` (`404`) — заявка отсутствует или не видна.
- `ERR_FORBIDDEN` (`403`) — роль не разрешает чтение истории.
- `ERR_INTERNAL` (`500`).

### 3.12. GET `/approval-tasks`

**Request**

- Query: `page_size?` — default 20, максимум 100.
- Остальные параметры навигации по страницам не зафиксированы — см. §10.
- Имплицитный фильтр: `assignee_id = current_user` и `status = open`.
- Body: отсутствует.

**Response**

- `200 OK`.
- Body: пагинированное представление; envelope и метаданные навигации не зафиксированы — см. §10.
- Каждый элемент списка содержит `{ id, request_id, request_type: { id, name }, stage: { number, name }, status: "open", created_at }`.
- Пустая очередь допустима.

**Validation**

- Только роль `approver`.
- Чужие и закрытые задачи не входят в очередь.

**Errors**

- `ERR_VALIDATION` (`422`) — невалидная пагинация.
- `ERR_FORBIDDEN` (`403`).
- `ERR_INTERNAL` (`500`).

### 3.13. GET `/approval-tasks/{task_id}`

**Request**

- Path: `task_id: UUID`.
- Body: отсутствует.

**Response**

- `200 OK`.
- Body:
  - `task`: `{ id, request_id, stage_number, assignee_id, status, decision, value_version_id }`;
  - `request`: полная карточка со snapshot-based `schema` и `values`, статусом, этапом, комментариями;
  - `available_actions`: для `open` задачи; пустой список для completed/cancelled.

**Validation**

- Task принадлежит текущему approver.
- Своя задача видима в любом статусе.
- Карточка использует FieldValueVersion, к которой относится задача/решение; для открытой задачи — текущую версию.

**Errors**

- `ERR_NOT_FOUND` (`404`) или `ERR_FORBIDDEN_APPROVAL` (`403`) для чужой задачи — неоднозначность, см. §10.
- `ERR_FORBIDDEN` (`403`) — нет роли `approver`.
- `ERR_INTERNAL` (`500`).

### 3.14. POST `/approval-tasks/{task_id}/approve`

**Request**

- Path: `task_id: UUID`.
- Body: `{ comment?: string }`.

**Response**

- `200 OK`.
- Body: `{ task: { id, status: "completed", decision: "approve", value_version_id }, request: { id, status, current_stage } }`.
- `request.status` остаётся `in_approval` при переходе на следующий этап либо становится `approved` на последнем этапе.

**Validation**

- Только assignee своей открытой задачи.
- Assignee не является инициатором.
- Комментарий необязателен; переданный комментарий сохраняется как decision comment.
- First-approve-wins: sibling open tasks этапа → `cancelled`.
- Следующий этап и его задачи берутся только из RouteInstance.
- Решение привязывается к FieldValueVersion задачи.
- Решение, задачи, статус/этап и аудит изменяются атомарно.

**Errors**

- `ERR_FORBIDDEN_APPROVAL` (`403`) — не assignee или самосогласование.
- `ERR_TASK_DONE` (`409`) — задача уже завершена/cancelled.
- `ERR_DUP_ACTION` (`409`) — повтор в гонке/ретрае.
- `ERR_INVALID_STATE` (`409`) — состояние заявки/задачи не допускает approve.
- `ERR_INTERNAL` (`500`).

### 3.15. POST `/approval-tasks/{task_id}/reject`

**Request**

- Path: `task_id: UUID`.
- Body: `{ comment: string }`.

**Response**

- `200 OK`.
- Body: `{ task: { id, status: "completed", decision: "reject", value_version_id }, request: { id, status: "rejected", current_stage } }`.

**Validation**

- Только assignee своей открытой задачи; self-approval запрещён.
- `comment` после trim обязателен.
- Все открытые задачи текущего этапа закрываются; задачи следующих этапов не создаются.
- Решение привязано к текущей FieldValueVersion.
- Решение, задачи, статус и аудит изменяются атомарно.

**Errors**

- `ERR_FORBIDDEN_APPROVAL` (`403`).
- `ERR_TASK_DONE` (`409`).
- `ERR_DUP_ACTION` (`409`).
- `ERR_INVALID_STATE` (`409`).
- `ERR_VALIDATION` (`422`) — пустой/отсутствующий comment.
- `ERR_INTERNAL` (`500`).

### 3.16. POST `/approval-tasks/{task_id}/return`

**Request**

- Path: `task_id: UUID`.
- Body: `{ comment: string }`.

**Response**

- `200 OK`.
- Body: `{ task: { id, status: "completed", decision: "return", value_version_id }, request: { id, status: "returned", current_stage } }`.
- `current_stage` сохраняет этап возврата для аудита.

**Validation**

- Только assignee своей открытой задачи; self-approval запрещён.
- `comment` после trim обязателен.
- Все открытые задачи текущего этапа закрываются.
- RouteInstance и существующие FieldValueVersion не меняются.
- Решение, задачи, статус и аудит изменяются атомарно.

**Errors**

- `ERR_FORBIDDEN_APPROVAL` (`403`).
- `ERR_TASK_DONE` (`409`).
- `ERR_DUP_ACTION` (`409`).
- `ERR_INVALID_STATE` (`409`).
- `ERR_VALIDATION` (`422`) — пустой/отсутствующий comment.
- `ERR_INTERNAL` (`500`).

## 4. RBAC Matrix

`R` — read, `C` — create, `U` — update, `A` — action, `—` — нет доступа. Ограничения ownership/assignee обязательны поверх роли.

| Operation | Employee | Approver | Admin |
| :--- | :---: | :---: | :---: |
| GET `/request-types` | R | — | R |
| GET `/request-types/{type_id}` | R | — | R |
| GET `/request-types/{type_id}/schema` | R | — | R |
| POST `/requests` | C | — | — |
| GET `/requests` | R (own) | — | — |
| GET `/requests/{request_id}` | R (own) | — | — |
| PATCH `/requests/{request_id}` | U (own draft/returned) | — | — |
| POST `/requests/{request_id}/submit` | A (own) | — | — |
| POST `/requests/{request_id}/cancel` | A (own) | — | — |
| POST `/requests/{request_id}/comments` | C (own) | — | — |
| GET `/requests/{request_id}/history` | R (own) | R (via own task) | — |
| GET `/approval-tasks` | — | R (own open) | — |
| GET `/approval-tasks/{task_id}` | — | R (own, any status) | — |
| POST `/approval-tasks/{task_id}/approve` | — | A (own open) | — |
| POST `/approval-tasks/{task_id}/reject` | — | A (own open) | — |
| POST `/approval-tasks/{task_id}/return` | — | A (own open) | — |

Примечания:

1. Admin-доступ к каталогу указан в исходной RBAC Matrix как удобство проверки, но Admin API и полноценная admin-модель остаются backlog.
   Он распространяется на чтение списка активных типов, описания выбранного активного типа и схемы формы; создавать заявки `admin` не может.
2. `approver` без `employee` не получает employee permissions.
3. Пользователь с обеими ролями получает union permissions, но self-approval всё равно запрещён.
4. Employee-запрос чужой заявки возвращает `404 ERR_NOT_FOUND` (ACL-01).
5. Decision по чужой задаче или собственной заявке возвращает `403 ERR_FORBIDDEN_APPROVAL` (ACL-02/03).

## 5. Error Mapping

| Endpoint | Error ID | HTTP status | Condition |
| :--- | :--- | :---: | :--- |
| Все защищённые Baseline endpoints | ERR_FORBIDDEN | 403 | Роль не позволяет операцию |
| Все Baseline endpoints | ERR_INTERNAL | 500 | Непредвиденная ошибка; для mutation — rollback |
| GET `/request-types/{type_id}` | ERR_NOT_FOUND | 404 | Тип не существует |
| GET `/request-types/{type_id}` | ERR_NOT_FOUND | 404 | Тип неактивен; до разрешения расхождения FR-CAT-02/Error Matrix |
| GET `/request-types/{type_id}/schema` | ERR_NOT_FOUND | 404 | Тип не существует |
| GET `/request-types/{type_id}/schema` | ERR_NOT_FOUND | 404 | Тип неактивен; до разрешения расхождения FR-CAT-02/Error Matrix |
| POST `/requests` | ERR_NOT_FOUND | 404 | Тип не существует |
| POST `/requests` | ERR_INACTIVE_TYPE | 409 | Тип неактивен |
| POST `/requests` | ERR_VALIDATION | 422 | Некорректный body |
| GET `/requests` | ERR_VALIDATION | 422 | Некорректный status или page_size |
| GET `/requests/{request_id}` | ERR_NOT_FOUND | 404 | Нет заявки или она чужая |
| PATCH `/requests/{request_id}` | ERR_NOT_FOUND | 404 | Нет заявки или она чужая |
| PATCH `/requests/{request_id}` | ERR_INVALID_STATE | 409 | Не draft/returned |
| PATCH `/requests/{request_id}` | ERR_VALIDATION | 422 | Значения не соответствуют live-схеме |
| POST `/requests/{request_id}/submit` | ERR_NOT_FOUND | 404 | Нет заявки или она чужая |
| POST `/requests/{request_id}/submit` | ERR_INVALID_STATE | 409 | Не draft/returned |
| POST `/requests/{request_id}/submit` | ERR_INACTIVE_TYPE | 409 | Тип неактивен |
| POST `/requests/{request_id}/submit` | ERR_ROUTE_CONFIG | 409 | Маршрут без этапов/назначений |
| POST `/requests/{request_id}/submit` | ERR_VALIDATION | 422 | Working values не проходят live-схему |
| POST `/requests/{request_id}/cancel` | ERR_NOT_FOUND | 404 | Нет заявки или она чужая |
| POST `/requests/{request_id}/cancel` | ERR_INVALID_STATE | 409 | Не draft/returned |
| POST `/requests/{request_id}/comments` | ERR_NOT_FOUND | 404 | Нет заявки или она чужая |
| POST `/requests/{request_id}/comments` | ERR_VALIDATION | 422 | Пустой comment |
| GET `/requests/{request_id}/history` | ERR_NOT_FOUND | 404 | Нет права видеть заявку |
| GET `/approval-tasks` | ERR_VALIDATION | 422 | Некорректный page_size |
| GET `/approval-tasks/{task_id}` | ERR_NOT_FOUND | 404 | Нет задачи/связи с текущим approver |
| GET `/approval-tasks/{task_id}` | ERR_FORBIDDEN_APPROVAL | 403 | Альтернативный вариант для чужой задачи; требует решения |
| POST decision endpoints | ERR_FORBIDDEN_APPROVAL | 403 | Не assignee или self-approval |
| POST decision endpoints | ERR_TASK_DONE | 409 | Задача completed/cancelled |
| POST decision endpoints | ERR_DUP_ACTION | 409 | Повтор бизнес-действия в гонке/ретрае |
| POST decision endpoints | ERR_INVALID_STATE | 409 | Состояние не допускает решение |
| POST `/approval-tasks/{task_id}/reject` | ERR_VALIDATION | 422 | Нет непустого comment |
| POST `/approval-tasks/{task_id}/return` | ERR_VALIDATION | 422 | Нет непустого comment |

`ERR_CONFLICT_VERSION` не используется в Baseline. `ERR_INVALID_CREDENTIALS` и `ERR_UNAUTHORIZED` относятся к backlog auth.

## 6. Snapshot / Lifecycle Constraints

### 6.1. Lifecycle coverage

| From | Operation | To | Guard / effect |
| :--- | :--- | :--- | :--- |
| initial | POST `/requests` | `draft` | Тип активен; initiator = current user |
| `draft` | POST `.../submit` | `in_approval` | Live validation; RouteInstance; FieldValueVersion #1; stage-1 tasks |
| `returned` | POST `.../submit` | `in_approval` | RouteInstance unchanged; новая FieldValueVersion; stage → 1 |
| `draft` / `returned` | POST `.../cancel` | `cancelled` | Только initiator |
| `in_approval` | POST `.../approve` | `in_approval` | Не последний этап; first-approve-wins; next-stage tasks |
| `in_approval` | POST `.../approve` | `approved` | Последний этап |
| `in_approval` | POST `.../reject` | `rejected` | Непустой comment; закрытие задач |
| `in_approval` | POST `.../return` | `returned` | Непустой comment; этап возврата сохраняется |

`approved`, `rejected`, `cancelled` — терминальные статусы. Cancel из `in_approval` запрещён.

### 6.2. Live и snapshot-based данные

| Data | Live / working | Snapshot-based |
| :--- | :--- | :--- |
| Request type name/description | Каталог и draft edit читают live RequestType | Источники не требуют отдельного snapshot типа |
| Form schema | Draft/returned edit и submit validation используют live RequestFieldDefinition | Каждый successful submit копирует схему в FieldValueVersion |
| Field values | RequestFieldValue изменяется в draft/returned | Каждый successful submit копирует значения в FieldValueVersion |
| Approval route | Live ApprovalRoute проверяется и копируется при первом submit | RouteInstance используется для всех in-flight решений и resubmit |
| Assignments | Только explicit role/user StageAssignment; no organization auto-routing | RouteInstanceAssignment определяет assignees и задачи |
| Decision | Не читает live field values/route | Привязано к FieldValueVersion и этапу RouteInstance |
| History | Новые HistoryEvent добавляются при значимых действиях | Старые events и FieldValueVersion read-only |

### 6.3. Неизменяемость и запрет прямых мутаций

- После первого successful submit RouteInstance, его этапы и назначения write-once.
- Resubmit не пересобирает RouteInstance.
- FieldValueVersion append-only; существующие версии нельзя patch/delete.
- В `in_approval`, `approved`, `rejected`, `cancelled` endpoint редактирования working values недоступен.
- В `returned` разрешено менять только working values; последняя submitted version остаётся неизменной до создания новой версии.
- `request_type_id`, `initiator_id`, status и `current_stage_number` нельзя задавать через PATCH.
- ApprovalTask, decision, HistoryEvent, RouteInstance и FieldValueVersion нельзя создавать/изменять напрямую клиентом.
- Изменения live schema/route/assignments не влияют на существующий RouteInstance и прошлые FieldValueVersion.

### 6.4. Проверка обязательных правил

| Rule | API enforcement |
| :--- | :--- |
| Self-approval forbidden | Все decision endpoints сравнивают initiator и assignee; `ERR_FORBIDDEN_APPROVAL` |
| Comments required for reject/return | Required non-empty `comment`; `ERR_VALIDATION` |
| First-approve-wins | Approve атомарно completes winner и cancels sibling tasks |
| RouteInstance on successful submit | Создаётся только при first submit после всех validation checks |
| FieldValueVersion on submit/resubmit | Новая версия при каждом successful submit |
| Live config does not alter in-flight | Decisions и next stage читают RouteInstance/current FieldValueVersion |
| Explicit user/role assignment | Submit принимает только snapshot валидных StageAssignment |
| No organization auto-routing | Department/position не используются для назначения |

## 7. Future / Backlog API

Ниже приведены candidate operations для уже зафиксированных backlog UC/FR. Они не входят в Baseline и не детализируются до уровня контракта на этом этапе.

| # | Method | Candidate path | UC / FR | Purpose |
| ---: | :--- | :--- | :--- | :--- |
| 1 | POST | `/auth/sessions` | UC-01; FR-AUTH-01 | Login и выпуск JWT |
| 2 | GET | `/users/me` | UC-01, UC-02; FR-AUTH-02, FR-CAB-01 | Текущий пользователь и профиль |
| 3 | GET | `/admin/request-types` | UC-11; FR-ADMIN-01 | Список типов для admin |
| 4 | POST | `/admin/request-types` | UC-11; FR-ADMIN-01 | Создать тип |
| 5 | PATCH | `/admin/request-types/{type_id}` | UC-11; FR-ADMIN-01 | Изменить/активировать тип |
| 6 | DELETE | `/admin/request-types/{type_id}` | UC-11; FR-ADMIN-01 | Удалить тип в рамках CRUD |
| 7 | PUT | `/admin/request-types/{type_id}/fields` | UC-11; FR-ADMIN-02 | Заменить конфигурацию полей |
| 8 | GET | `/admin/request-types/{type_id}/route` | UC-12; FR-ADMIN-03–05 | Прочитать route aggregate |
| 9 | PUT | `/admin/request-types/{type_id}/route` | UC-12; FR-ADMIN-03–05 | Сохранить этапы и explicit assignments |
| 10 | GET | `/admin/dictionaries` | UC-11; FR-ADMIN-06 | Список справочников |
| 11 | POST | `/admin/dictionaries` | UC-11; FR-ADMIN-06 | Создать справочник |
| 12 | PATCH | `/admin/dictionaries/{dictionary_id}` | UC-11; FR-ADMIN-06 | Изменить справочник |
| 13 | DELETE | `/admin/dictionaries/{dictionary_id}` | UC-11; FR-ADMIN-06 | Удалить справочник |
| 14 | PUT | `/admin/dictionaries/{dictionary_id}/items` | UC-11; FR-ADMIN-06 | Сохранить элементы справочника |
| 15 | GET | `/admin/requests` | UC-15; FR-ADMIN-07 | Реестр всех заявок с фильтрами |
| 16 | GET | `/admin/requests/{request_id}` | UC-15; FR-ADMIN-07, FR-REQ-04 | Карточка любой заявки |
| 17 | GET | `/admin/requests/{request_id}/history` | UC-14, UC-15; FR-ADMIN-08 | История любой заявки |
| 18 | GET | `/notifications` | UC-13; FR-CAB-03, FR-NOTIF-02 | Свои уведомления |
| 19 | PATCH | `/notifications/{notification_id}` | UC-13; FR-NOTIF-03 | Установить `read = true` |

**Количество Future / Backlog candidate operations: 19.**

FR-AUTH-03 и FR-NOTIF-01 являются cross-cutting/system behavior, а не самостоятельными клиентскими endpoints.

## 8. Traceability

### 8.1. UC → API

| UC | Covered by |
| :--- | :--- |
| UC-03 | GET `/request-types`; GET `/request-types/{type_id}`; GET `.../schema` |
| UC-04 | GET `.../schema`; POST `/requests`; PATCH `/requests/{request_id}` |
| UC-05 | POST `/requests/{request_id}/submit` |
| UC-06 | GET `/requests`; GET `/requests/{request_id}`; POST `.../comments` |
| UC-07 | GET `/approval-tasks`; GET `/approval-tasks/{task_id}`; POST `.../approve` |
| UC-08 | GET `/approval-tasks/{task_id}`; POST `.../reject` |
| UC-09 | POST `.../return`; PATCH `/requests/{request_id}`; POST `.../submit` |
| UC-10 | POST `/requests/{request_id}/cancel` |
| UC-14 | GET `/requests/{request_id}/history` |

### 8.2. FR → API

| FR | Covered by |
| :--- | :--- |
| FR-CAB-02 | GET `/requests` |
| FR-CAT-01 | GET `/request-types` |
| FR-CAT-02 | GET `/request-types/{type_id}` |
| FR-CAT-03 | GET `/request-types/{type_id}/schema` |
| FR-REQ-01 | POST `/requests` |
| FR-REQ-02 | PATCH `/requests/{request_id}` |
| FR-REQ-03, FR-REQ-09 | POST `/requests/{request_id}/submit` |
| FR-REQ-04, FR-REQ-05 | GET `/requests/{request_id}`; GET `/approval-tasks/{task_id}` |
| FR-REQ-06 | GET request/task card; POST `/requests/{request_id}/comments`; decision bodies |
| FR-REQ-07 | POST `/requests/{request_id}/cancel` |
| FR-REQ-08 | Side effect of POST `.../return` |
| FR-APP-01 | GET `/approval-tasks` |
| FR-APP-02 | GET `/approval-tasks/{task_id}` |
| FR-APP-03 | POST `.../approve` |
| FR-APP-04 | POST `.../reject` |
| FR-APP-05 | POST `.../return` |
| FR-APP-06, FR-APP-07 | Side effects of POST `.../approve` |
| FR-AUDIT-01 | GET `/requests/{request_id}/history` |
| FR-AUDIT-02 | Atomic side effect of all significant mutations |

### 8.3. AC → API

| AC | Covered by |
| :--- | :--- |
| AC-APP-01 | POST `/requests` |
| AC-APP-02, AC-APP-02b, AC-APP-03 | POST `.../submit`; GET `/approval-tasks` |
| AC-APP-04, AC-APP-04b | POST `.../approve` |
| AC-APP-05, AC-APP-05b, AC-APP-09 | POST `.../approve`; GET `/approval-tasks` |
| AC-APP-06, AC-APP-06b | POST `.../reject` |
| AC-APP-07, AC-APP-07b | POST `.../return`; PATCH request |
| AC-APP-08 | PATCH request; POST `.../submit`; GET history |
| AC-APP-10, AC-APP-10b | POST `.../submit`; all decision endpoints |
| AC-ACC-01 | GET/PATCH/action endpoints for request ownership |
| AC-ACC-02, AC-ACC-03 | All decision endpoints |
| AC-ACC-06 | GET `/approval-tasks/{task_id}` |
| AC-CAT-01, AC-CAT-02 | GET `/request-types`; POST `/requests` |
| AC-CAT-01b | GET request/task card; decision endpoints read snapshots |
| AC-DRAFT-01 | GET `.../schema`; PATCH request; POST `.../submit` |
| AC-DRAFT-02 | GET request/task card; POST `.../submit`; GET history |
| AC-REQ-06 | POST `.../comments`; GET request card |
| AC-REQ-07 | POST `.../cancel` |

Все 9 Baseline UC, 22 Baseline FR и 27 Baseline AC имеют API coverage либо явно являются системным side effect.

## 9. Gap Analysis

| Check | Result | Gap / disposition |
| :--- | :--- | :--- |
| Requirement без API operation | Нет непокрытых Baseline FR | FR-AUDIT-02, FR-REQ-08, FR-APP-06/07 корректно покрываются side effects |
| API operation без requirement | Не найдено | Все 16 Baseline operations трассируются к UC/FR |
| UC без API coverage | Не найдено | Все 9 Baseline UC покрыты |
| AC без API coverage | Не найдено | Все 27 Baseline AC покрыты operation или side effect |
| Error без endpoint | Есть ожидаемые | `ERR_CONFLICT_VERSION` — Future/Reserved; `ERR_INVALID_CREDENTIALS`, `ERR_UNAUTHORIZED` — auth backlog |
| Endpoint без понятного RBAC | Не найдено | Для всех Baseline operations определены role + ownership/assignee |
| Admin RBAC | Расхождений не найдено | `admin` имеет только чтение каталога/схемы в Baseline RBAC; остальные admin-функции остаются backlog |
| Несогласованная UC-трассировка | Найдено | FR-CAT-03 в собственной карточке связан с UC-04, но UC-03 также прямо включает запрос схемы; контракт ссылается на оба |
| Неактивный type detail/schema | Найдено | FR-CAT-02 допускает `ERR_NOT_FOUND / ERR_INACTIVE_TYPE`, но Error Matrix ограничивает `ERR_INACTIVE_TYPE` операциями create/submit; до review в GET используется `ERR_NOT_FOUND` |
| Dictionary data для catalog field | Найдено | FR-CAT-03 требует ссылку на справочник, но read operation для его активных items в Baseline не определена |
| Дата задачи в очереди | Найдено | FR-APP-01 требует дату в элементе очереди, но у ApprovalTask в Data Dictionary отсутствует поле создания/даты |
| Card values после cancel из returned | Найдено | Не определено, показывать последние working values или последнюю submitted FieldValueVersion |
| Free comment statuses | Найдено | FR-REQ-06 говорит «в статусах, включая in_approval», но не перечисляет полный допустимый набор |
| Task detail visibility error | Найдено | FR-APP-02 допускает `ERR_NOT_FOUND / ERR_FORBIDDEN_APPROVAL`, без однозначного условия выбора |
| Demo identity contract | Найдено | ADR фиксирует HTTP header stub, но не имена/формат role и user headers |
| Error response envelope | Найдено | Error Matrix содержит только рекомендуемый ориентир `{ error_code, message, details }`, а не утверждённый обязательный контракт |
| Pagination contract | Найдено | Зафиксированы `page_size`, default 20 и max 100, но не способ навигации и не response envelope |

## 10. REQUIRES REVIEW

Следующие пункты должны быть решены перед фиксацией OpenAPI. В этом документе новые требования и error IDs не создаются.

1. **Demo headers.** Определить точные имена, обязательность и формат заголовков demo user/roles. Также выбрать существующую ошибку для отсутствующего/некорректного header либо дополнить Error Matrix отдельным решением.
2. **Inactive type read.** Устранить расхождение FR-CAT-02 и Error Matrix. До отдельного решения GET type detail/schema использует `ERR_NOT_FOUND`, поскольку `ERR_INACTIVE_TYPE` в Error Matrix определён только для create/submit.
3. **Dictionary items.** Определить, включаются ли активные items в response `/request-types/{type_id}/schema` или требуется отдельный Baseline read endpoint. Без этого поле `catalog` нельзя полностью отрисовать по API.
4. **ApprovalTask date.** Определить источник даты для очереди FR-APP-01: добавить поле времени создания в модель на отдельном согласованном этапе либо исключить его из contract response. Сейчас поле требуется FR, но отсутствует в Data Dictionary.
5. **Approver card route.** Подтвердить, что полная карточка approver возвращается aggregate-ответом `GET /approval-tasks/{task_id}`, а не через отдельный доступ approver к `GET /requests/{request_id}`.
6. **Task visibility error.** Выбрать `ERR_NOT_FOUND` или `ERR_FORBIDDEN_APPROVAL` для чтения чужой/несуществующей задачи. Для decision endpoints остаётся `ERR_FORBIDDEN_APPROVAL`.
7. **Cancelled card data.** Определить источник `schema/values` для заявки, отменённой из `returned`: последние working values либо последняя FieldValueVersion.
8. **Free comment states.** Зафиксировать полный набор статусов заявки, в которых инициатор может добавлять свободный комментарий. Требования явно гарантируют `in_approval`, но формулировка шире одного статуса.
9. **History pagination.** Определить, нужна ли пагинация истории. NFR-PERF-03 требует её только для списков заявок и задач.
10. **Pagination contract.** Для списков заявок и задач зафиксированы только `page_size`, default 20 и max 100. Нужно определить page/cursor-механизм и response envelope; до решения они не считаются частью Baseline-контракта.
11. **Error response envelope.** Подтвердить рекомендуемый Error Matrix формат `{ error_code, message, details }` как обязательный либо определить другой формат на этапе контракта. Сейчас зафиксированы error IDs и HTTP statuses, но не обязательная JSON-схема envelope.
12. **Traceability convention for OpenAPI.** Правило `.cursor/rules/20-api.mdc` ожидает `x-requirement: US-XXX`, но проект использует UC/FR/AC ID и не содержит User Story ID. До OpenAPI нужно согласовать фактический формат ссылок.
