# UML-CL-01 — Conceptual Class Diagram (предметная модель)

**Продукт:** Employee Service  
**ID:** UML-CL-01  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [uml-description.md](./uml-description.md), [Snapshot Model](../erd/snapshot-model.md)

---

## 1. Назначение

Аналитическая (conceptual) модель сущностей предметной области Employee Service — мост между глоссарием / BR и ERD.

### Важно: это не ERD

| Conceptual Class (здесь) | ERD ([erd/](../erd/)) |
| :--- | :--- |
| Классы анализа, смысл предметной области | Таблицы, колонки, типы SQL |
| Связи и кратности на уровне бизнеса | PK / FK / индексы / нормализация |
| Без DTO, слоёв приложения, API | Физическая схема PostgreSQL |

Новые бизнес-правила **не вводятся**. Атрибуты — на уровне анализа (без технических id-стратегий).

---

## 2. Каталог классов

### 2.1. Пользователи и роли

| Класс | Атрибуты (анализ) | Смысл |
| :--- | :--- | :--- |
| **User** | fullName, email, position, department, active | Пользователь системы |
| **Role** | code (`employee` / `approver` / `admin`) | Системная роль; у User — множество ролей (BR-16) |

### 2.2. Каталог и конфигурация

| Класс | Атрибуты (анализ) | Смысл |
| :--- | :--- | :--- |
| **RequestType** | name, description, isActive | Тип заявки / услуга каталога |
| **RequestFieldDefinition** | code, name, dataType, required, order | Поле схемы формы типа |
| **Dictionary** | name | Справочник |
| **DictionaryItem** | code, name, isActive | Элемент справочника |
| **ApprovalRoute** | — | Маршрут типа (конфиг) |
| **ApprovalStage** | name, sequence | Этап маршрута (конфиг) |
| **StageAssignment** | assignmentKind (role / user) | Явное назначение на этап (BR-12) |

### 2.3. Экземпляр заявки и snapshot-сущности

| Класс | Атрибуты (анализ) | Смысл |
| :--- | :--- | :--- |
| **Request** | status, currentStageNumber | Экземпляр заявки; инициатор = User |
| **RequestFieldValue** | fieldCode, value | Working values заявки (live schema в draft/returned); не FieldValueVersion. Канон: Snapshot Model / DD §4.2 |
| **RouteInstance** | stagesOrder, assignmentsCopy | Экземпляр маршрута при **первом** submit (BR-08); при resubmit не rebuild (BR-22). Ранее: RouteSnapshot |
| **FieldValueVersion** | submitNumber, fieldSchemaCopy, fieldValuesCopy | Версия схемы+значений на каждый successful submit (BR-26); решение bound to version. Ранее: SchemaValueSnapshot |

### 2.4. Согласование, комментарии, уведомления, аудит

| Класс | Атрибуты (анализ) | Смысл |
| :--- | :--- | :--- |
| **ApprovalTask** | status (`open` / `completed` / `cancelled`), stageNumber | Задача согласующего по этапу RouteInstance |
| **Comment** | text, kind (free / decision) | Свободный комментарий инициатора или комментарий решения |
| **Notification** | text, read, eventType | In-app уведомление (BR-11) — **Future / backlog** |
| **HistoryEvent** | action, fromState, toState, at, comment | Событие истории (BR-24) |

---

## 3. Ключевые связи и ограничения (notes)

| Тема | Ограничение (существующие BR) |
| :--- | :--- |
| RouteInstance | `Request` имеет не более одного после первого submit; создаётся только из `draft` |
| RequestFieldValue | Working values; мутабельны в `draft`/`returned` по live schema (BR-26) |
| FieldValueVersion | Append-only на каждый successful submit; решение bound to version |
| Задачи | `ApprovalTask` из назначений **RouteInstance**, не из live `StageAssignment` |
| First-approve | При approve прочие `open` задачи того же stageNumber → `cancelled` (BR-03) |
| Self-approval | Исполнитель задачи не может быть инициатором той же `Request` (BR-21) |
| Comment on decision | Для decision reject/return `Comment.text` обязателен (BR-25); для approve — нет |
| Visibility | Сотрудник видит свои Request; approver — по своим Task (BR-01, BR-14) |
| Config isolation | Изменение live-маршрута не изменяет существующие `RouteInstance` (BR-09; admin — backlog) |
| Канон | [Snapshot Model](../erd/snapshot-model.md) |

---

## 4. Диаграмма (Mermaid)

```mermaid
classDiagram
  direction TB

  class User {
    fullName
    email
    position
    department
    active
  }
  class Role {
    code
  }
  class RequestType {
    name
    description
    isActive
  }
  class RequestFieldDefinition {
    code
    name
    dataType
    required
    order
  }
  class Dictionary {
    name
  }
  class DictionaryItem {
    code
    name
    isActive
  }
  class ApprovalRoute
  class ApprovalStage {
    name
    sequence
  }
  class StageAssignment {
    assignmentKind
  }
  class Request {
    status
    currentStageNumber
  }
  class RequestFieldValue {
    fieldCode
    value
  }
  class RouteInstance {
    stagesOrder
    assignmentsCopy
  }
  class FieldValueVersion {
    submitNumber
    fieldSchemaCopy
    fieldValuesCopy
  }
  class ApprovalTask {
    status
    stageNumber
  }
  class Comment {
    text
    kind
  }
  class Notification {
    text
    read
    eventType
  }
  class HistoryEvent {
    action
    fromState
    toState
    at
    comment
  }

  User "many" -- "many" Role : has
  User "1" --> "many" Request : initiates
  RequestType "1" --> "many" RequestFieldDefinition : defines
  RequestType "1" --> "0..1" ApprovalRoute : has
  ApprovalRoute "1" --> "many" ApprovalStage : ordered
  ApprovalStage "1" --> "many" StageAssignment : assigns
  StageAssignment --> Role : byRole
  StageAssignment --> User : byUser
  RequestFieldDefinition --> Dictionary : optional
  Dictionary "1" --> "many" DictionaryItem : contains

  RequestType "1" --> "many" Request : typedAs
  Request "1" --> "0..*" RequestFieldValue : workingValues
  Request "1" --> "0..1" RouteInstance : firstSubmit
  Request "1" --> "0..*" FieldValueVersion : eachSubmit
  Request "1" --> "many" ApprovalTask : has
  ApprovalTask --> User : assignee
  ApprovalTask --> FieldValueVersion : decidedOn
  Request "1" --> "many" Comment : has
  Request "1" --> "many" HistoryEvent : auditedBy
  User "1" --> "many" Notification : receives

  note for RequestFieldValue "Working values (draft/returned).\nНе FieldValueVersion. См. Snapshot Model."
  note for RouteInstance "Создаётся только при первом submit (BR-08).\nПри resubmit не rebuild (BR-22).\nКонфиг не ретроактивен (BR-09)."
  note for FieldValueVersion "Новая версия на каждый successful submit (BR-26).\nРешение bound to version. См. Snapshot Model."
  note for ApprovalTask "First-approve: прочие open → cancelled (BR-03).\nИсполнитель ≠ инициатор Request (BR-21)."
  note for Comment "decision reject/return: text обязателен (BR-25)."
```

---

## 5. Трассировка

| Тип | ID |
| :--- | :--- |
| **UC** | косвенно UC-03…UC-15 (структура предметной области) |
| **FR** | FR-CAT-*, FR-REQ-*, FR-APP-*, FR-AUDIT-*; FR-ADMIN-01…06, FR-NOTIF-* — **Future / backlog** где применимо |
| **BR** | BR-01, BR-03, BR-08, BR-09, BR-11–16, BR-21, BR-22, BR-24–27 |
| **AC** | AC-APP-08…10b, AC-DRAFT-01, AC-DRAFT-02, AC-ACC-* (через visibility/self-approval) |
| **Глоссарий** | термины Vision / глоссария |

---

## 6. Границы

- Нет таблиц БД, PK/FK, индексов, миграций.
- Нет API DTO и слоёв приложения.
- Нет параллельных этапов и оргструктурного auto-routing (out of scope Vision).
- Новые сущности «для удобства реализации» не добавляются.
