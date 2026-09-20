# ARCH-FLOW — Основные потоки данных и взаимодействия

**Продукт:** Employee Service  
**ID:** ARCH-FLOW  
**Версия:** 1.1  
**Статус:** Baseline v1.0  
**Связанные документы:** [architecture-description.md](./architecture-description.md), [Snapshot Model](../erd/snapshot-model.md), [ADR-AUTH-DEMO-01](./adr-demo-role-header.md), [ADR-UI-01](./adr-static-web-client.md)

---

## 1. Назначение

Показать, как контейнеры и логические модули взаимодействуют в ключевых сценариях, уже описанных BPMN-01…03 и UML-SEQ-01…03. Порядок бизнес-правил **не меняется**; добавляется только архитектурная раскладка.

Транзакционные границы ниже — **ADR-детализация** поверх уже требуемой атомарности (NFR-REL-01; BR-29 при наличии уведомлений в scope). Они не создают новых FR/BR/NFR.

**Клиент:** `Web_Static` — статический HTML/JS ([ADR-UI-01](./adr-static-web-client.md)). REST передаёт демо-роль заголовком ([ADR-AUTH-DEMO-01](./adr-demo-role-header.md)), не JWT.

---

## 2. Поток A — Первый submit и resubmit (UC-05)

**Требования:** BR-08, BR-18, BR-20, BR-22, BR-24, BR-26; FR-REQ-03/09; FR-AUDIT-02. Уведомления (BR-23/29, FR-NOTIF-01) — если в scope; иначе [backlog](../../backlog.md).

### 2.1. Шаги (логический)

1. HTTP Layer принимает команду submit; AuthN (демо-заголовок); AuthZ (инициатор, статус `draft`|`returned`).
2. Request / Catalog: валидация полей по **актуальной** схеме; проверка типа активен; валидация маршрута (BR-18).
3. **Submit Orchestrator** открывает транзакцию БД (**ADR-TX-01**):
   - если первый submit (`draft`) → Snapshot: **создать** RouteInstance (BR-08);
   - если resubmit (`returned`) → Snapshot: **не** rebuild RouteInstance (BR-22);
   - Snapshot: **новая** FieldValueVersion (BR-26; канон — [Snapshot Model](../erd/snapshot-model.md));
   - статус → `in_approval`; создать ApprovalTask текущего этапа по RouteInstance;
   - Audit: событие submit/resubmit (+ связь с версией значений, BR-24);
   - Notification: если в scope (иначе backlog).
4. Commit. Ошибка Audit/Snapshot (и Notification при наличии) → rollback.

### 2.2. Sequence (Mermaid)

```mermaid
sequenceDiagram
  actor Init as Инициатор
  participant Web as Web_Static
  participant API as HTTP_Layer
  participant AuthZ as Authorization
  participant Sub as Submit_Orchestrator
  participant Snap as Snapshot
  participant Appr as Approval_Engine
  participant Aud as Audit
  participant Ntf as Notification
  participant DB as PostgreSQL

  Init->>Web: Submit / Resubmit
  Web->>API: REST + demo role header
  API->>AuthZ: проверка инициатора и статуса
  API->>Sub: orchestrate submit
  Note over Sub,DB: ADR-TX-01 одна транзакция БД
  Sub->>Sub: validate live schema + route + active type
  alt первый submit из draft
    Sub->>Snap: create RouteInstance
  else resubmit из returned
    Sub->>Snap: keep RouteInstance
  end
  Sub->>Snap: append FieldValueVersion
  Sub->>Appr: create tasks for current stage
  Sub->>Aud: write HistoryEvent
  Note over Ntf: Notification — backlog / BR-29 если в scope
  Sub->>Ntf: create in-app notifications (если в scope)
  Sub->>DB: commit
  API-->>Web: in_approval
  Web-->>Init: статус обновлён
```

---

## 3. Поток B — Approve / Reject / Return (UC-07…09)

**Требования:** BR-03, BR-04, BR-05, BR-14, BR-15, BR-17, BR-21, BR-25; FR-APP-*; FR-AUDIT-02. Уведомления — backlog / BR-29 если в scope.

### 3.1. Шаги

1. AuthN (демо-заголовок); AuthZ: своя **open** задача (BR-15); actor ≠ initiator (BR-21); иначе `ERR_FORBIDDEN_APPROVAL`.
2. Approval Engine:
   - reject/return → непустой комментарий (BR-25) иначе `ERR_VALIDATION`;
   - approve → комментарий опционален.
3. Транзакция (**ADR-TX-02**):
   - **Approve:** задача completed; sibling open → `cancelled` (BR-03); читать RouteInstance (не live config); next tasks или `approved` (BR-17);
   - **Reject:** `rejected`; закрыть open задачи этапа (BR-04);
   - **Return:** `returned`; сохранить номер этапа; закрыть задачи этапа (BR-05);
   - Audit (+ Notification в той же TX, если в scope — BR-29).
4. Повтор по уже закрытой/cancelled задаче → `ERR_TASK_DONE` / `ERR_DUP_ACTION` (NFR-REL-02) без повторной мутации.

### 3.2. Sequence: approve + first-approve (Mermaid)

```mermaid
sequenceDiagram
  actor A as Согласующий_A
  participant Web as Web_Static
  participant API as HTTP_Layer
  participant AuthZ as Authorization
  participant Eng as Approval_Engine
  participant Snap as Snapshot
  participant Aud as Audit
  participant Ntf as Notification
  participant DB as PostgreSQL

  A->>Web: Approve
  Web->>API: REST + demo role header
  API->>AuthZ: own open task; not initiator
  API->>Eng: approve
  Note over Eng,DB: ADR-TX-02 одна транзакция
  Eng->>Eng: complete task A; cancel sibling open tasks
  Eng->>Snap: read RouteInstance next step
  alt есть следующий этап
    Eng->>Eng: create next stage tasks
  else последний этап
    Eng->>Eng: status = approved
  end
  Eng->>Aud: HistoryEvent
  Note over Ntf: Notification — backlog / если в scope
  Eng->>Ntf: in-app notifications (если в scope)
  Eng->>DB: commit
  API-->>Web: OK
```

---

## 4. Поток C — Admin configure (UC-11, UC-12) — Future

**Статус:** Future / [backlog](../../backlog.md). Соответствует BPMN-03, UML-SEQ-03.

**Требования (когда вернётся):** BR-09, BR-10, BR-12, BR-18, BR-27; FR-ADMIN-01…06.

1. AuthZ: роль `admin` (ACL-04); admin не создаёт заявки за сотрудников (BR-27).
2. Admin Config пишет **live** конфигурацию (тип, поля, этапы, назначения, справочники).
3. **Snapshot isolation (BR-09):** запись конфига **не** изменяет существующие RouteInstance in-flight заявок.
4. Activate: валидация маршрута (BR-18); иначе тип остаётся неактивным.
5. Deactivate: скрытие из каталога (BR-10); in-flight продолжают по своим snapshot.
6. Audit конфигурационных изменений — по мере наличия событий в BR-24 / admin history FR-ADMIN-08.

```mermaid
sequenceDiagram
  actor Adm as Администратор
  participant Web as Web_Static
  participant API as HTTP_Layer
  participant AuthZ as Authorization
  participant Cfg as Admin_Config
  participant DB as PostgreSQL

  Note over Adm,DB: Future / backlog — ADR-TX-04
  Adm->>Web: Сохранить маршрут / активировать тип
  Web->>API: REST + demo role header
  API->>AuthZ: роль admin
  API->>Cfg: save / activate
  Cfg->>Cfg: write live config only
  Note over Cfg: BR-09 не трогает RouteInstance заявок
  alt activate
    Cfg->>Cfg: validate route BR-18
  end
  Cfg->>DB: persist
  API-->>Web: OK / ERR_ROUTE_CONFIG
```

---

## 5. Поток D — Чтение: списки, карточка, история, уведомления

| Сценарий | Модули | Правила видимости | Scope |
| :--- | :--- | :--- | :--- |
| Свои заявки | Request + AuthZ | BR-01 | Baseline |
| Очередь задач | Approval Engine + AuthZ | BR-14, BR-15 | Baseline |
| История | Audit + AuthZ | FR-AUDIT-01; visibility как у заявки | Baseline |
| Реестр admin | Admin / Request + AuthZ | BR-13 | Future / backlog |
| Уведомления | Notification + AuthZ | только получатель; FR-NOTIF-02/03 | Future / backlog |

Пагинация списков — NFR-PERF-03 (default 20 / max 100).

Чужой скрываемый ресурс для employee → `ERR_NOT_FOUND` / 404 (NFR-SEC-05).

---

## 6. Сводка транзакционных границ (ADR)

| ID | Граница | Что атомарно | Источник требования | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **ADR-TX-01** | Submit / resubmit | status + snapshots + tasks + audit (+ notifications если в scope) | NFR-REL-01, BR-20; BR-29 — backlog | Baseline core |
| **ADR-TX-02** | Approve / reject / return | status/tasks (вкл. first-approve cancel) + audit (+ notifications если в scope) | BR-03/04/05, NFR-REL-01; BR-29 — backlog | Baseline core |
| **ADR-TX-03** | Cancel | status + audit (+ notification инициатору при наличии в BR-23) | BR-07, BR-24; BR-23 — backlog | Baseline core |
| **ADR-TX-04** | Admin save/activate | запись live config; **без** мутации RouteInstance заявок | BR-09 | **Future / backlog** |

Детализация «один DB transaction на use case» — **предположение MVP** о реализации атомарности, уже требуемой NFR/BR. Альтернативы (outbox и т.п.) не вводятся в MVP.

---

## 7. Трассировка

| Поток | UC | BPMN | UML |
| :--- | :--- | :--- | :--- |
| A | UC-04, UC-05, UC-10 | BPMN-01 | UML-SEQ-01, UML-SM-01 |
| B | UC-07, UC-08, UC-09 | BPMN-02 | UML-SEQ-02, UML-SM-01 |
| C | UC-11, UC-12 (backlog) | BPMN-03 (Future) | UML-SEQ-03 (Future) |
| D | UC-06, UC-14; UC-13/15 backlog | — | UML-UC-01 |

---

## 8. Границы

- Нет HTTP path / OpenAPI.
- Нет диаграмм физической репликации БД.
- Порядок правил совпадает с требованиями / BPMN / UML.
- Новые потоки и ID не вводятся.
