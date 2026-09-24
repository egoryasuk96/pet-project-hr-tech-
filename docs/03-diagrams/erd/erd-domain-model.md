# ERD-DM — Logical Domain Model (ER Diagram)

**Продукт:** Employee Service  
**ID:** ERD-DM  
**Версия:** 2.0  
**Статус:** Target architecture (docs E0–E1)  
**Связанные документы:** [README.md](./README.md), [ADR-LIVE-CFG-01](../architecture/adr-live-config.md), [ADR-ACTION-01](../architecture/adr-configurable-actions.md), [ADR-ORG-01](../architecture/adr-org-model.md), [ADR-ID-01](../architecture/adr-id-strategy.md)

---

## 1. Назначение

Логическая ER-модель Employee Service после отказа от snapshot. Атрибуты — в [data-dictionary.md](./data-dictionary.md).

Это **не** DDL. Типы ID на логическом уровне: User — UUID; остальные сущности — integer ([ADR-ID-01](../architecture/adr-id-strategy.md)). Реализация смены типов — последующие этапы.

**Нет в модели:** `RouteInstance`, `RouteInstanceStage`, `RouteInstanceAssignment`, `FieldValueVersion`.

---

## 2. Диаграмма (Mermaid)

```mermaid
erDiagram
  COMPANY ||--o{ DEPARTMENT : has
  DEPARTMENT ||--o{ EMPLOYEE : has
  EMPLOYEE ||--o| EMPLOYEE : manager
  EMPLOYEE ||--o| USER : account
  ROLE ||--o{ USER : assigned

  PROCESS ||--o{ REQUEST_TYPE : owns
  PROCESS ||--o{ PROCESS_TRANSITION : defines
  STATUS ||--o{ PROCESS_TRANSITION : from_status
  STATUS ||--o{ PROCESS_TRANSITION : to_status
  ACTION ||--o{ PROCESS_TRANSITION : via
  ROLE ||--o{ PROCESS_TRANSITION : allowed

  REQUEST_TYPE ||--o{ REQUEST_FIELD_DEFINITION : defines
  REQUEST_TYPE ||--o| APPROVAL_ROUTE : has
  REQUEST_FIELD_DEFINITION }o--o| DICTIONARY : uses
  DICTIONARY ||--o{ DICTIONARY_ITEM : contains

  APPROVAL_ROUTE ||--o{ APPROVAL_STAGE : ordered
  APPROVAL_STAGE ||--o{ STAGE_ASSIGNMENT : assigns
  STAGE_ASSIGNMENT }o--o| ROLE : by_role
  STAGE_ASSIGNMENT }o--o| USER : by_user

  REQUEST_TYPE ||--o{ REQUEST : typed
  USER ||--o{ REQUEST : initiates
  STATUS ||--o{ REQUEST : current
  APPROVAL_STAGE ||--o{ REQUEST : current_stage

  REQUEST ||--o{ REQUEST_FIELD_VALUE : values
  REQUEST ||--o{ APPROVAL_TASK : tasks
  APPROVAL_STAGE ||--o{ APPROVAL_TASK : for_stage
  USER ||--o{ APPROVAL_TASK : assignee
  REQUEST ||--o{ COMMENT : comments
  COMMENT }|--|| USER : author
  COMMENT }o--o| APPROVAL_TASK : for_decision
  REQUEST ||--o{ HISTORY_EVENT : audit
  HISTORY_EVENT }o--o| USER : actor
  USER ||--o{ NOTIFICATION : receives
  NOTIFICATION }o--o| REQUEST : about
  NOTIFICATION }o--o| APPROVAL_TASK : about_task

  COMPANY {
    int id PK
    string name
    boolean active
  }

  DEPARTMENT {
    int id PK
    int company_id FK
    string name
    boolean active
  }

  EMPLOYEE {
    int id PK
    string employee_number
    string first_name
    string last_name
    string middle_name
    int department_id FK
    int manager_employee_id FK
    string position
    boolean active
  }

  USER {
    uuid id PK
    string login
    string password_hash
    int employee_id FK
    int role_id FK
    boolean is_active
  }

  ROLE {
    int id PK
    string code
    string name
  }

  PROCESS {
    int id PK
    string code
    string name
    string description
    boolean active
  }

  STATUS {
    int id PK
    string code
    string name
    string description
    boolean active
  }

  ACTION {
    int id PK
    string code
    string name
    string description
    boolean active
  }

  PROCESS_TRANSITION {
    int id PK
    int process_id FK
    int from_status_id FK
    int action_id FK
    int to_status_id FK
    int role_id FK
    string effect
    boolean is_active
    int sort_order
  }

  REQUEST_TYPE {
    int id PK
    int process_id FK
    string code
    string name
    string description
    boolean active
  }

  REQUEST_FIELD_DEFINITION {
    int id PK
    int request_type_id FK
    string code
    string name
    string data_type
    boolean required
    int order_no
    int dictionary_id FK
  }

  DICTIONARY {
    int id PK
    string name
  }

  DICTIONARY_ITEM {
    int id PK
    int dictionary_id FK
    string code
    string name
    boolean active
  }

  APPROVAL_ROUTE {
    int id PK
    int request_type_id FK
  }

  APPROVAL_STAGE {
    int id PK
    int route_id FK
    string name
    int sequence_no
  }

  STAGE_ASSIGNMENT {
    int id PK
    int stage_id FK
    string assignment_kind
    int role_id FK
    uuid user_id FK
  }

  REQUEST {
    int id PK
    int request_type_id FK
    uuid initiator_user_id FK
    int status_id FK
    int current_stage_id FK
    datetime created_at
    datetime updated_at
  }

  REQUEST_FIELD_VALUE {
    int id PK
    int request_id FK
    string field_code
    string value
  }

  APPROVAL_TASK {
    int id PK
    int request_id FK
    int stage_id FK
    uuid assignee_user_id FK
    string status
    string comment
    datetime created_at
    datetime completed_at
  }

  COMMENT {
    int id PK
    int request_id FK
    uuid author_id FK
    int approval_task_id FK
    string kind
    string text
    datetime created_at
  }

  HISTORY_EVENT {
    int id PK
    int request_id FK
    uuid actor_id FK
    string action
    string from_state
    string to_state
    string comment
    datetime at
  }

  NOTIFICATION {
    int id PK
    uuid recipient_id FK
    int request_id FK
    int approval_task_id FK
    string event_type
    string text
    boolean read
    datetime created_at
  }
```

**Notification.event_type** (PG enum `notification_event_type`):
`new_task`, `status_change`, `request_submitted`, `request_approved`, `request_rejected`, `request_returned`, `request_cancelled`.

**Notification** — in-app persistence (E4.2); delivery channels remain backlog.

**Конфиг live:** ApprovalRoute* и ProcessTransition. См. [ADR-LIVE-CFG-01](../architecture/adr-live-config.md).

---

## 3. Кардинальности

| От | К | Кардинальность | Notes |
| :--- | :--- | :--- | :--- |
| Company | Department | 1 — 0..N | Демо: одна company |
| Department | Employee | 1 — 0..N | |
| Employee | Employee (manager) | N — 0..1 | Только данные; не auto-routing |
| Employee | User | 1 — 0..1 | Учётная запись |
| Role | User | 1 — 0..N | Одна роль на User |
| Process | RequestType | 1 — 0..N | |
| Process | ProcessTransition | 1 — 0..N | Live transitions |
| RequestType | ApprovalRoute | 1 — 0..1 | Live route |
| ApprovalRoute | ApprovalStage | 1 — 1..N (валидный) | `sequence_no` |
| ApprovalStage | StageAssignment | 1 — 1..N (валидный) | |
| Request | Status | N — 1 | `status_id` |
| Request | ApprovalStage | N — 0..1 | `current_stage_id` live |
| Request | ApprovalTask | 1 — 0..N | Tasks на live `stage_id` |
| ApprovalTask | ApprovalStage | N — 1 | Обязательный `stage_id` |
| Request | RequestFieldValue | 1 — 0..N | Working values only |

---

## 4. Справочные коды (логические)

| Область | Примеры code | UI |
| :--- | :--- | :--- |
| Status | `draft`, `in_approval`, `returned`, `approved`, `rejected`, `cancelled` | `Status.name` |
| Action | `submit`, `cancel`, `approve`, `reject`, `return` | `Action.name` |
| ProcessTransition.effect | `status_only`, `approve_advance` | не для UI |
| Role | `employee`, `approver`, `admin` | `Role.name` |
| ApprovalTask.status | `open`, `completed`, `cancelled` | |

Статусы и действия — **сущности** с `id/code/name`, не только enum на Request.

---

## 5. Инварианты (logical)

| ID | Ограничение | Источник |
| :--- | :--- | :--- |
| C-01 | `initiator_user_id` обязателен | BR-19 |
| C-02 | Нет RouteInstance / FieldValueVersion | ADR-LIVE-CFG-01 |
| C-03 | ApprovalTask создаётся из **live** StageAssignment текущего stage | ADR-LIVE-CFG-01, BR-08 |
| C-04 | `task.stage_id` и при согласовании `request.current_stage_id` согласованы | ADR-ACTION-01 |
| C-05 | First-approve: sibling open tasks того же stage → cancelled | BR-03 |
| C-06 | Self-approval ban | BR-21 |
| C-07 | reject/return ⇒ непустой комментарий | BR-25 |
| C-08 | Cancel только draft \| returned | BR-07 |
| C-09 | Валидный маршрут: ≥1 stage, каждый ≥1 assignment | BR-18 |
| C-10 | Не удалять stage при open tasks / in_approval на этот stage | BR-09, ADR-LIVE-CFG-01 |
| C-11 | ProcessTransition live; влияет на in-flight | ADR-LIVE-CFG-01 |

Optimistic locking / process versioning — **не** моделируются.

---

## 6. Границы

- Нет snapshot-таблиц.
- Нет microservices / outbox / Kafka.
- Нет орг-auto-routing по manager.
- Notification delivery — backlog.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.1 | 2026-09-21 | ApprovalTask.created_at |
| 1.0 | 2026-09-19 | Logical ERD со snapshot |
| 2.0 | 2026-09-23 | Удалён snapshot; org; Process/Status/Action/Transition; status_id; current_stage_id; stage_id |
