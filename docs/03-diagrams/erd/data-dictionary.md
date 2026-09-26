# ERD-DD - Data Dictionary

**Продукт:** Employee Service  
**ID:** ERD-DD  
**Версия:** 2.1  
**Статус:** Target architecture (docs E0-E1)  
**Связанные документы:** [README.md](./README.md), [erd-domain-model.md](./erd-domain-model.md), [ADR-LIVE-CFG-01](../architecture/adr-live-config.md)

---

## 1. Соглашения

Логический словарь target-модели. Snapshot-сущности удалены ([ADR-LIVE-CFG-01](../architecture/adr-live-config.md)).

---

## 2. Request (runtime)

| Field | Type | Required | Nullable | Description | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
| status_id | int | yes | no | FK > Status | UML-SM-01 |
| current_stage_id | int | no | yes | FK > ApprovalStage | ADR-LIVE-CFG-01 |
| initiator_user_id | UUID | yes | no | FK > User | BR-19 |

Нет RouteInstance / FieldValueVersion.

---

## 3. RequestFieldValue (working values)

Единственный носитель значений полей (BR-26). Live schema при edit/submit.

---

## 4. ApprovalTask

| Field | Type | Required | Description | Source |
| :--- | :--- | :--- | :--- | :--- |
| stage_id | int | yes | FK > live ApprovalStage | BR-02 |
| assignee_user_id | UUID | yes | FK > User | BR-15 |
| comment | string | no | Decision comment | BR-25 |
| created_at | timestamptz | yes | Immutable | FR-APP-01 |
| completed_at | datetime | no | Completion | FR-APP-03 |

Нет value_version_id.

---

## 5. Live config (Process / Status / Action / Transition / Route)

Физическая схема PostgreSQL (совпадает с runtime). Канон поведения: [ADR-ACTION-01](../architecture/adr-configurable-actions.md), [ADR-LIVE-CFG-01](../architecture/adr-live-config.md).

Company, Department, Employee — ADR-ORG-01 (поля здесь не дублируются).  
StageAssignment — live assignments на этапе; in-flight caveat ADR-LIVE-CFG-01 (поля здесь не дублируются).

### 5.1. Process (`processes`)

Контейнер бизнес-процесса: владеет типами заявок и таблицей `process_transitions`. Глобальный каталог процессов (не snapshot).

| Field | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| id | int | no | — | PK |
| code | varchar | no | — | Стабильный код процесса |
| name | varchar | no | — | Отображаемое имя |
| description | varchar | yes | — | Описание |
| active | boolean | no | — | Активен ли процесс |

**FK:** нет.  
**Unique:** `uq_processes_code` (`code`).  
**Indexes:** `processes_pkey` (id); `uq_processes_code` (code).

### 5.2. Status (`statuses`)

Глобальный справочник статусов заявки (не привязан к `process_id`). Request хранит `status_id`. Финальность (`approved` / `rejected` / `cancelled`) задаётся кодом и графом переходов, колонки `is_final` нет.

| Field | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| id | int | no | — | PK |
| code | varchar | no | — | Код статуса (`draft`, `in_approval`, …) |
| name | varchar | no | — | Отображаемое имя |
| description | varchar | yes | — | Описание |
| active | boolean | no | — | Активен ли статус |

**FK:** нет.  
**Unique:** `uq_statuses_code` (`code`).  
**Indexes:** `statuses_pkey` (id); `uq_statuses_code` (code).

### 5.3. Action (`actions`)

Глобальный справочник действий (не привязан к `process_id`). Используется в `process_transitions` и UI `available_actions` (`code`: `submit`, `cancel`, `approve`, `reject`, `return`).

| Field | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| id | int | no | — | PK |
| code | varchar | no | — | Код действия |
| name | varchar | no | — | Отображаемое имя |
| description | varchar | yes | — | Описание |
| active | boolean | no | — | Активно ли действие |

**FK:** нет.  
**Unique:** `uq_actions_code` (`code`).  
**Indexes:** `actions_pkey` (id); `uq_actions_code` (code).

### 5.4. ProcessTransition (`process_transitions`)

Live-матрица переходов **по статусам**: `(process_id, from_status_id, action_id, role_id) → to_status_id + effect`. Узлы графа — `statuses`, не `approval_stages`. Продвижение по этапам маршрута — через `effect = approve_advance` и live `ApprovalStage.sequence_no`.

| Field | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| id | int | no | — | PK |
| process_id | int | no | — | FK → processes.id |
| from_status_id | int | no | — | FK → statuses.id (исходный статус) |
| action_id | int | no | — | FK → actions.id |
| to_status_id | int | no | — | FK → statuses.id (целевой статус) |
| role_id | int | no | — | FK → roles.id (роль, для которой переход доступен) |
| effect | process_transition_effect | no | — | `status_only` \| `approve_advance` |
| is_active | boolean | no | — | Участвует ли переход в runtime |
| sort_order | int | no | — | Порядок в матрице / UI |

**FK:**

| Column | References |
| :--- | :--- |
| process_id | processes.id |
| from_status_id | statuses.id |
| to_status_id | statuses.id |
| action_id | actions.id |
| role_id | roles.id |

**Unique:** нет (кроме PK).  
**Indexes:** `process_transitions_pkey` (id); `ix_process_transitions_process_id`; `ix_process_transitions_from_status_id`; `ix_process_transitions_to_status_id`; `ix_process_transitions_action_id`; `ix_process_transitions_role_id`.

### 5.5. ApprovalRoute (`approval_routes`)

Live-маршрут согласования для типа заявки (1:1 с `request_type_id`). Колонки `name` нет — идентификация через тип заявки.

| Field | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| id | int | no | — | PK |
| request_type_id | int | no | — | FK → request_types.id |

**FK:** `request_type_id` → `request_types.id`.  
**Unique:** `uq_approval_routes_request_type_id` (`request_type_id`).  
**Indexes:** `approval_routes_pkey` (id); `uq_approval_routes_request_type_id` (request_type_id).

### 5.6. ApprovalStage (`approval_stages`)

Упорядоченный этап live-маршрута (`sequence_no`). Линейная цепочка внутри статуса `in_approval`; не является узлом `process_transitions`.

| Field | Type | Nullable | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| id | int | no | — | PK |
| route_id | int | no | — | FK → approval_routes.id |
| name | varchar | no | — | Название этапа |
| sequence_no | int | no | — | Порядок этапа в маршруте |

**FK:** `route_id` → `approval_routes.id`.  
**Unique:** `uq_approval_stages_route_sequence` (`route_id`, `sequence_no`).  
**Indexes:** `approval_stages_pkey` (id); `uq_approval_stages_route_sequence` (route_id, sequence_no).

---

## 6. Deprecated (removed)

| Entity | Replacement |
| :--- | :--- |
| RouteInstance* | Live route + current_stage_id |
| FieldValueVersion | RequestFieldValue + HistoryEvent |

[snapshot-model.md](./snapshot-model.md) - Deprecated.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 2.1 | 2026-09-27 | §5: поля Process/Status/Action/ProcessTransition/ApprovalRoute/ApprovalStage по схеме БД |
| 2.0 | 2026-09-23 | Live config; snapshot removed |
| 1.1 | 2026-09-21 | ApprovalTask.created_at |
| 1.0 | 2026-09-19 | Первая версия |
