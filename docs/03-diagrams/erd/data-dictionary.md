# ERD-DD — Data Dictionary

**Продукт:** Employee Service  
**ID:** ERD-DD  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [README.md](./README.md), [Snapshot Model](./snapshot-model.md)

---

## 1. Соглашения

| Тема | Правило |
| :--- | :--- |
| **Type** | Логический тип анализа (`UUID`, `string`, `boolean`, `int`, `datetime`, `enum`, `JSON`) |
| **Physical** | Не фиксируется (не `varchar(n)`, не `jsonb`) |
| **Required** | Обязательность на логическом уровне сущности |
| **Nullable** | Допустимость отсутствия значения |
| **Источник** | FR / BR / UC / NFR / glossary / Architecture ADR, где уместно |

---

## 2. Identity / RBAC

### 2.1. User

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Идентификатор пользователя | PK | FR-AUTH-02 |
| login | string | yes | no | Учётная запись для входа | unique | FR-AUTH-01 |
| password_hash | string | yes | no | Хэш пароля (не plaintext) | NFR-SEC-03 | FR-AUTH-01 |
| full_name | string | yes | no | ФИО | — | FR-CAB-01 |
| email | string | yes | no | Email | — | FR-CAB-01 |
| position | string | no | yes | Должность (профиль) | Не ключ маршрутизации | Vision, FR-CAB-01 |
| department | string | no | yes | Отдел (профиль) | Не орг-auto-routing (BR-12) | Vision, FR-CAB-01 |
| is_active | boolean | yes | no | Признак активной УЗ | — | glossary |

### 2.2. Role

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Идентификатор роли | PK | BR-16 |
| code | enum | yes | no | `employee` \| `approver` \| `admin` | unique | glossary, RBAC |

### 2.3. UserRole

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| user_id | UUID | yes | no | Пользователь | FK → User; PK composite | BR-16 |
| role_id | UUID | yes | no | Роль | FK → Role; PK composite | BR-16 |

**Constraints:** роли объединяются (union); role switcher отсутствует (BR-16, AC-AUTH-01).

---

## 3. Configuration (live)

### 3.1. RequestType

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Тип заявки | PK | FR-ADMIN-01 |
| name | string | yes | no | Название | — | FR-ADMIN-01, FR-CAT-01 |
| description | string | no | yes | Описание услуги | — | FR-CAT-02 |
| is_active | boolean | yes | no | Видимость в каталоге | activate только при валидном маршруте (BR-18) | BR-10, FR-ADMIN-01 |

### 3.2. RequestFieldDefinition

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Поле схемы | PK | FR-ADMIN-02 |
| request_type_id | UUID | yes | no | Тип | FK → RequestType | FR-CAT-03 |
| code | string | yes | no | Код поля | unique per type | FR-ADMIN-02 |
| name | string | yes | no | Отображаемое имя | — | FR-ADMIN-02 |
| data_type | enum | yes | no | `text` \| `date` \| `number` \| `catalog` | — | glossary |
| required | boolean | yes | no | Обязательность значения | — | FR-ADMIN-02 |
| order_no | int | yes | no | Порядок на форме | — | FR-ADMIN-02 |
| dictionary_id | UUID | no | yes | Справочник | FK → Dictionary; для catalog | FR-ADMIN-02, FR-ADMIN-06 |

### 3.3. Dictionary

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Справочник | PK | FR-ADMIN-06 |
| name | string | yes | no | Имя справочника | — | FR-ADMIN-06 |

### 3.4. DictionaryItem

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Элемент | PK | FR-ADMIN-06 |
| dictionary_id | UUID | yes | no | Справочник | FK → Dictionary | FR-ADMIN-06 |
| code | string | yes | no | Код | unique per dictionary | FR-ADMIN-06 |
| name | string | yes | no | Наименование | — | FR-ADMIN-06 |
| is_active | boolean | yes | no | Активность | — | FR-ADMIN-06 |

### 3.5. ApprovalRoute

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Маршрут (live) | PK | FR-ADMIN-03 |
| request_type_id | UUID | yes | no | Тип | FK → RequestType; 1—0..1 | FR-ADMIN-03 |

### 3.6. ApprovalStage

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Этап (live) | PK | FR-ADMIN-04 |
| route_id | UUID | yes | no | Маршрут | FK → ApprovalRoute | FR-ADMIN-04 |
| name | string | yes | no | Имя этапа | — | FR-ADMIN-04 |
| sequence_no | int | yes | no | Порядок (последовательный) | unique per route; BR-02 | BR-02, FR-ADMIN-04 |

### 3.7. StageAssignment

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Назначение | PK | FR-ADMIN-05 |
| stage_id | UUID | yes | no | Этап | FK → ApprovalStage | FR-ADMIN-05 |
| assignment_kind | enum | yes | no | role / user / both | — | BR-12 |
| role_id | UUID | no | yes | Роль | FK → Role; ≥1 из role/user | BR-12 |
| user_id | UUID | no | yes | Пользователь | FK → User; ≥1 из role/user | BR-12 |

**Constraints:** нет auto-routing по оргструктуре (BR-12). Live assignments **не** меняют существующие RouteInstance (BR-09).

---

## 4. Runtime — Request

### 4.1. Request

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Заявка | PK | FR-REQ-01 |
| initiator_id | UUID | yes | no | Инициатор | FK → User | BR-01, BR-19 |
| request_type_id | UUID | yes | no | Тип | FK → RequestType | FR-REQ-01 |
| status | enum | yes | no | Жизненный цикл | см. glossary | UML-SM-01 |
| current_stage_number | int | no | yes | Текущий этап; после return — этап возврата (аудит); при resubmit → 1 | Обязателен в in_approval; после return может хранить N до resubmit | BR-05, BR-06 |
| created_at | datetime | yes | no | Создание | — | — |
| updated_at | datetime | yes | no | Обновление | — | — |

**Relations:** 0..1 RouteInstance; 0..N FieldValueVersion; 0..N RequestFieldValue, ApprovalTask, Comment, HistoryEvent.

**Constraints:** cancel только draft/returned (BR-07); admin не создаёт от имени сотрудника (BR-27).

### 4.2. RequestFieldValue (working values)

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Значение | PK | FR-REQ-02 |
| request_id | UUID | yes | no | Заявка | FK → Request | FR-REQ-02 |
| field_code | string | yes | no | Код поля | Соответствует схеме (live при edit) | BR-26 |
| value | string | no | yes | Значение (логический носитель) | Валидация по data_type / catalog | FR-REQ-02, BR-26 |

**Constraints:** мутации в `draft`/`returned` по **live** схеме; не являются FieldValueVersion.

---

## 5. Snapshots

### 5.1. RouteInstance

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Snapshot маршрута | PK | BR-08 |
| request_id | UUID | yes | no | Заявка | FK → Request; **unique** (1—0..1) | BR-08 |
| created_at | datetime | yes | no | Момент first submit | write-once | BR-08 |

**Constraints:** создаётся только при первом successful submit; immutable; не пересоздаётся при resubmit (BR-22).

### 5.2. RouteInstanceStage

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Этап snapshot | PK | BR-08 |
| route_snapshot_id | UUID | yes | no | Snapshot | FK → RouteInstance | BR-08 |
| name | string | yes | no | Имя на момент submit | — | BR-08 |
| sequence_no | int | yes | no | Порядок | unique per snapshot | BR-02, BR-08 |

### 5.3. RouteInstanceAssignment

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Назначение snapshot | PK | BR-08 |
| snapshot_stage_id | UUID | yes | no | Этап snapshot | FK → RouteInstanceStage | BR-08 |
| assignment_kind | enum | yes | no | role / user / both | — | BR-12 |
| role_id | UUID | no | yes | Роль на момент snapshot | FK → Role | BR-08 |
| user_id | UUID | no | yes | User на момент snapshot | FK → User | BR-08 |

**Constraints:** ApprovalTask строятся из этих назначений (не из live StageAssignment для in-flight).

### 5.4. FieldValueVersion

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Версия схемы+значений | PK | BR-26 |
| request_id | UUID | yes | no | Заявка | FK → Request | BR-26, BR-22 |
| submit_number | int | yes | no | Номер successful submit (1, 2, …) | unique per request | BR-26 |
| schema_document | JSON | yes | no | Копия схемы полей на момент submit | Логический документ | BR-26 |
| values_document | JSON | yes | no | Копия значений на момент submit | Логический документ | BR-26 |
| created_at | datetime | yes | no | Момент данного successful submit | — | BR-26 |

**Constraints:** append-only на каждый successful submit; прошлые версии не переписываются; решение согласующего привязано к версии. Канон: [snapshot-model.md](./snapshot-model.md).

---

## 6. Approval / Comments

### 6.1. ApprovalTask

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Задача | PK | FR-APP-01 |
| request_id | UUID | yes | no | Заявка | FK → Request | FR-APP-02 |
| stage_number | int | yes | no | Номер этапа snapshot | Соответствует RouteInstanceStage.sequence_no | BR-02 |
| assignee_id | UUID | yes | no | Исполнитель | FK → User | BR-15 |
| status | enum | yes | no | `open` \| `completed` \| `cancelled` | First-approve → siblings cancelled | BR-03 |
| decision | enum | no | yes | `approve` \| `reject` \| `return` | Только после решения | FR-APP-03…05 |
| value_version_id | UUID | no | yes | Версия значений, на которой принято решение | FK → FieldValueVersion | BR-26 |

**Constraints:** действие только по своей open задаче (BR-15); assignee ≠ initiator (BR-21); повтор по closed → ошибка (NFR-REL-02).

### 6.2. Comment

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Комментарий | PK | FR-REQ-06 |
| request_id | UUID | yes | no | Заявка | FK → Request | FR-REQ-06 |
| author_id | UUID | yes | no | Автор | FK → User | FR-REQ-06 |
| approval_task_id | UUID | no | yes | Задача (для decision) | FK → ApprovalTask | FR-APP-03…05 |
| kind | enum | yes | no | `free` \| `decision` | — | BR-25, BR-28 |
| text | string | yes | no | Текст | Для reject/return decision — непустой | BR-25 |
| created_at | datetime | yes | no | Время | — | — |

**Constraints:** free comments инициатора в `in_approval` (BR-28); approve-комментарий необязателен (BR-25).

---

## 7. Audit / Notifications

HistoryEvent — Baseline. **Notification** — **Future / backlog** (сущность сохранена; см. §7.2).

### 7.1. HistoryEvent

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Событие истории | PK | FR-AUDIT-02 |
| request_id | UUID | yes | no | Заявка | FK → Request | FR-AUDIT-01 |
| actor_id | UUID | no | yes | Актор | FK → User; system events могут быть без user | BR-24 |
| action | string | yes | no | Тип действия | Минимум набор BR-24 | BR-24, NFR-LOG-02 |
| from_state | string | no | yes | Исходное состояние | — | BR-24 |
| to_state | string | no | yes | Новое состояние | — | BR-24 |
| comment | string | no | yes | Комментарий события | Не полный snapshot payload | BR-24 |
| at | datetime | yes | no | Время | — | BR-24 |

**Retention:** прикладная история заявок — **60 дней** (NFR-LOG-03 п.2).  
**Не путать** с technical API logs (NFR-LOG-01, retention **14 дней**, NFR-LOG-03 п.1) — вне ERD.

### 7.2. Notification (**Future / backlog**)

Сущность сохраняется в модели; in-app уведомления (FR-NOTIF-*, BR-11/23/29) — не MVP Baseline, см. [docs/backlog.md](../../backlog.md).

| Field | Type | Required | Nullable | Description | Relations / Constraints | Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| id | UUID | yes | no | Уведомление | PK | FR-NOTIF-01 |
| recipient_id | UUID | yes | no | Получатель | FK → User | FR-NOTIF-02 |
| request_id | UUID | no | yes | Связанная заявка | FK → Request | BR-23 |
| approval_task_id | UUID | no | yes | Связанная задача | FK → ApprovalTask | BR-23 |
| event_type | enum | yes | no | Тип события | Минимум BR-23 | BR-23 |
| text | string | yes | no | Текст | In-app only | BR-11 |
| read | boolean | yes | no | Прочитано | default false; mark read idempotent | FR-NOTIF-03 |
| created_at | datetime | yes | no | Время создания | Та же TX, что бизнес-событие | BR-29 |

---

## 8. Вне словаря предметной ERD

| Тема | Почему вне DD |
| :--- | :--- |
| Technical API logs | NFR-LOG-01 / NFR-LOG-03 п.1; infra |
| JWT / client session storage | Stateless API |
| Отдельная сущность SubmitVersion / RequestVersion | Не вводится как ID требования; версионирование — **FieldValueVersion** ([snapshot-model.md](./snapshot-model.md)) |
| Org units / manager links | BR-12 out of scope |

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия Data Dictionary |
