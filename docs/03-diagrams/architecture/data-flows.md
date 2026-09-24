# ARCH-FLOW — Основные потоки данных и взаимодействия

**Продукт:** Employee Service  
**ID:** ARCH-FLOW  
**Версия:** 1.2  
**Статус:** Target architecture (Frozen Target)  
**Связанные документы:** [architecture-description.md](./architecture-description.md), [ADR-LIVE-CFG-01](./adr-live-config.md), [ADR-ACTION-01](./adr-configurable-actions.md), [ADR-AUTH-JWT-01](./adr-jwt-core-api.md), [ADR-UI-01](./adr-static-web-client.md)

---

## 1. Назначение

Показать, как контейнеры и логические модули взаимодействуют в ключевых сценариях, уже описанных BPMN-01…03 и UML-SEQ-01…03. Порядок бизнес-правил **не меняется**; добавляется только архитектурная раскладка.

Транзакционные границы ниже — **ADR-детализация** поверх уже требуемой атомарности (NFR-REL-01; BR-29). Они не создают новых FR/BR/NFR.

**Клиент:** `Web_Static` — статический HTML/JS ([ADR-UI-01](./adr-static-web-client.md)). REST передаёт `Authorization: Bearer` JWT ([ADR-AUTH-JWT-01](./adr-jwt-core-api.md)). Demo-header — не AuthN.

**Workflow (live):** `Request → Process/RequestType → live ApprovalRoute → ApprovalStage → StageAssignment`; transitions — `ProcessTransition` → Action Engine.

---

## 2. Поток A — Первый submit и resubmit (UC-05)

**Требования:** BR-08, BR-18, BR-20, BR-22, BR-24, BR-26; FR-REQ-03/09; FR-AUDIT-02; BR-23/29 (notifications).

Primary path: `POST /requests/{id}/actions/{action_id}` (Action Engine). Legacy aliases `POST .../submit` — deprecated thin wrappers.

### 2.1. Шаги (логический)

1. HTTP Layer принимает команду; AuthN (JWT → user); AuthZ (инициатор, статус `draft`|`returned`).
2. Action Engine: lookup `ProcessTransition`; effect `status_only` (submit).
3. Request / Catalog: валидация полей по **актуальной** схеме; проверка типа активен; валидация маршрута (BR-18).
4. **Одна транзакция БД** (**ADR-TX-01**):
   - lock Request;
   - статус → `in_approval`; `current_stage_id` → первый live **ApprovalStage** (BR-08, BR-20);
   - создать ApprovalTask из **live** StageAssignment (BR-08);
   - при resubmit (`returned`) — снова первый live-этап (BR-06, BR-22);
   - Audit: HistoryEvent submit/resubmit (BR-24);
   - Notification: in-app (BR-23/29).
5. Commit. Ошибка Audit/tasks/Notification → rollback.

### 2.2. Sequence (Mermaid)

```mermaid
sequenceDiagram
  actor Init as Инициатор
  participant Web as Web_Static
  participant API as HTTP_Layer
  participant Auth as Auth_JWT
  participant Act as Action_Engine
  participant Appr as Approval_Engine
  participant Aud as Audit
  participant Ntf as Notification
  participant DB as PostgreSQL

  Init->>Web: Submit / Resubmit
  Web->>API: REST + Bearer JWT
  API->>Auth: resolve user from JWT
  API->>Act: POST actions action_id
  Note over Act,DB: ADR-TX-01 одна транзакция БД
  Act->>Act: lock Request; ProcessTransition lookup
  Act->>Act: validate live schema + route + active type
  Act->>Appr: current_stage_id = first live stage
  Act->>Appr: create tasks from live StageAssignment
  Act->>Aud: write HistoryEvent
  Act->>Ntf: create in-app notifications
  Act->>DB: commit
  API-->>Web: in_approval
  Web-->>Init: статус обновлён
```

---

## 3. Поток B — Primary mutation: approve / reject / return (и прочие actions)

**Требования:** BR-03, BR-04, BR-05, BR-14, BR-15, BR-17, BR-21, BR-25; FR-APP-*; FR-AUDIT-02; BR-23/29.

**Discovery:** `GET /requests/{id}/available-actions`.  
**Execute:** `POST /requests/{id}/actions/{action_id}`.

Legacy `/approval-tasks/{id}/approve|return|reject` — disabled stubs (не CURRENT mutation path).

### 3.1. Шаги

1. AuthN (JWT); AuthZ: роль / open задача / ownership (BR-15); actor ≠ initiator (BR-21); иначе `FORBIDDEN_APPROVAL`.
2. Action Engine:
   - lock Request;
   - ProcessTransition lookup (process, from_status, action, role, active);
   - reject/return → непустой комментарий (BR-25) иначе `VALIDATION`;
   - effect `approve_advance` или `status_only`.
3. Транзакция (**ADR-TX-02**):
   - **Approve (`approve_advance`):** задача completed; sibling open → `cancelled` (BR-03); next live stage; next tasks или `approved` (BR-17);
   - **Reject / Return (`status_only`):** статус + закрытие open задач этапа (BR-04/05);
   - HistoryEvent + Notification в той же TX (BR-24, BR-29).
4. Повтор по уже закрытой/cancelled задаче → `TASK_DONE` / `INVALID_STATE` (NFR-REL-02) без повторной мутации.

### 3.2. Sequence: execute action (Mermaid)

```mermaid
sequenceDiagram
  actor A as Согласующий
  participant Web as Web_Static
  participant API as HTTP_Layer
  participant Auth as Auth_JWT
  participant Act as Action_Engine
  participant Appr as Approval_Engine
  participant Aud as Audit
  participant Ntf as Notification
  participant DB as PostgreSQL

  A->>Web: Available actions / Execute
  Web->>API: GET available-actions / POST actions
  Note over Web,API: Authorization Bearer JWT
  API->>Auth: resolve user + role_id
  API->>Act: execute action_id
  Note over Act,DB: ADR-TX-02 одна транзакция
  Act->>Act: lock Request; ProcessTransition lookup
  Act->>Appr: task / stage updates per effect
  alt approve_advance next stage
    Appr->>Appr: current_stage_id = next; create live tasks
  else final or status_only
    Appr->>Appr: status = to_status; close tasks
  end
  Act->>Aud: HistoryEvent
  Act->>Ntf: in-app notifications
  Act->>DB: commit
  API-->>Web: OK
```

---

## 4. Поток C — Admin configure (UC-11, UC-12) — Future

**Статус:** Future / [backlog](../../backlog.md). Соответствует BPMN-03, UML-SEQ-03.

**Требования (когда вернётся):** BR-09, BR-10, BR-12, BR-18, BR-27; FR-ADMIN-01…06.

1. AuthZ: роль `admin`; admin не создаёт заявки за сотрудников (BR-27).
2. Admin Config пишет **live** конфигурацию (тип, поля, этапы, назначения, справочники, ProcessTransition).
3. **In-flight caveat (ADR-LIVE-CFG-01):** правки live config **могут** затронуть in-flight; guard BR-09 на удаление stage с open tasks.
4. Activate: валидация маршрута (BR-18); иначе тип остаётся неактивным.
5. Deactivate: скрытие из каталога (BR-10); in-flight продолжают.
6. Audit конфигурационных изменений — по мере наличия событий в BR-24 / admin history FR-ADMIN-08.

```mermaid
sequenceDiagram
  actor Adm as Администратор
  participant Web as Web_Static
  participant API as HTTP_Layer
  participant Auth as Auth_JWT
  participant Cfg as Admin_Config
  participant DB as PostgreSQL

  Note over Adm,DB: Future / backlog — ADR-TX-04
  Adm->>Web: Сохранить маршрут / активировать тип
  Web->>API: REST + Bearer JWT
  API->>Auth: resolve user; role admin
  API->>Cfg: save / activate
  Cfg->>Cfg: write live config only
  Note over Cfg: ADR-LIVE-CFG-01 in-flight caveat; BR-09 guard
  alt activate
    Cfg->>Cfg: validate route BR-18
  end
  Cfg->>DB: persist
  API-->>Web: OK / ROUTE_CONFIG
```

---

## 5. Поток D — Чтение: списки, карточка, история, уведомления

| Сценарий | Модули | Правила видимости | Scope |
| :--- | :--- | :--- | :--- |
| Свои заявки | Request + AuthZ | BR-01 | Target |
| Available actions | Action Engine + AuthZ | BR-14, BR-15, ProcessTransition | Target |
| История | Audit + AuthZ | FR-AUDIT-01; visibility как у заявки | Target |
| Уведомления | Notification + AuthZ | только получатель; FR-NOTIF-02/03 | Target |
| Очередь задач (list) | Approval Engine + AuthZ | BR-14, BR-15 | API stub / Future UI |
| Реестр admin | Admin / Request + AuthZ | BR-13 | Future / backlog |

Пагинация списков — NFR-PERF-03 (default 20 / max 100).

Чужой скрываемый ресурс для employee → `NOT_FOUND` / 404 (NFR-SEC-05).

---

## 6. Сводка транзакционных границ (ADR)

| ID | Граница | Что атомарно | Источник требования | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **ADR-TX-01** | Submit / resubmit (via Action Engine) | lock + status + current_stage_id + tasks + HistoryEvent + Notification | NFR-REL-01, BR-20, BR-29 | Target |
| **ADR-TX-02** | Execute action (approve / reject / return / …) | lock + transition + status/tasks + HistoryEvent + Notification | BR-03/04/05, NFR-REL-01, BR-29 | Target |
| **ADR-TX-03** | Cancel (via Action Engine) | status + HistoryEvent + Notification | BR-07, BR-24, BR-23 | Target |
| **ADR-TX-04** | Admin save/activate | запись live config; in-flight caveat ADR-LIVE-CFG-01 | BR-09 | **Future / backlog** |

Канонический mutation flow:  
`HTTP action → Action Engine → lock Request → ProcessTransition lookup → state/task update → HistoryEvent → Notification → commit`.

Детализация «один DB transaction на use case» — **предположение MVP** о реализации атомарности, уже требуемой NFR/BR.

---

## 7. Трассировка

| Поток | UC | BPMN | UML |
| :--- | :--- | :--- | :--- |
| A | UC-04, UC-05, UC-10 | BPMN-01 | UML-SEQ-01, UML-SM-01 |
| B | UC-07, UC-08, UC-09 | BPMN-02 | UML-SEQ-02, UML-SM-01 |
| C | UC-11, UC-12 (backlog) | BPMN-03 (Future) | UML-SEQ-03 (Future) |
| D | UC-06, UC-13, UC-14 | — | UML-UC-01 |

---

## 8. Границы

- Нет HTTP path / OpenAPI schema (см. `docs/04-api`).
- Нет диаграмм физической репликации БД.
- Порядок правил совпадает с требованиями / BPMN / UML.
- Новые потоки и ID не вводятся.

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.1 | 2026-09-23 | Live config flows; demo-header AuthN |
| 1.2 | 2026-09-24 | Bearer JWT; Action Engine primary mutation; Notification in TX |
