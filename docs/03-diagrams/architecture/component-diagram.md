# ARCH-CMP — Component Diagram (логические модули)

**Продукт:** Employee Service  
**ID:** ARCH-CMP  
**Версия:** 1.1  
**Статус:** Baseline v1.0  
**Связанные документы:** [architecture-description.md](./architecture-description.md), [ADR-UI-01](./adr-static-web-client.md), [ADR-AUTH-DEMO-01](./adr-demo-role-header.md)

---

## 1. Назначение

Описать **логическое** разделение ответственности внутри лёгкого веб-клиента (static HTML/JS) и API-монолита. Имена модулей — **ADR / предположение MVP**: способ организации кода и зон ответственности, а не новые бизнес-требования и не микросервисы.

Соответствие областям анализа UML (Validation, Snapshot, TaskFactory, Audit, Notification): те же обязанности, теперь явно привязанные к модулям архитектуры. Notification / Admin — Future/backlog, если не в Baseline scope.

---

## 2. Frontend — UI-зоны (ADR-CMP-FE / ADR-CMP-02)

### 2.1. Baseline (пять экранов Vision)

| UI-зона | Ответственность | Роли |
| :--- | :--- | :--- |
| **Role Select UI** | Выбор демо-роли / демо-пользователя; запоминание и подстановка заголовка ([ADR-AUTH-DEMO-01](./adr-demo-role-header.md)) | вход в демо |
| **My Requests UI** | Список своих заявок | `employee` |
| **Create Request UI** | Каталог активных типов + форма создания / draft / submit | `employee` |
| **Request Card UI** | Карточка: поля, статус, комментарии, история, cancel / resubmit | `employee` (+ visibility) |
| **Approver Queue UI** | Очередь задач; карточка; approve / reject / return | `approver` |

**Граница ответственности FE:** отображение и ввод; навигация по ролям как UX.  
**Authoritative AuthZ и бизнес-правила** — только на backend.  
Стек UI: [ADR-UI-01](./adr-static-web-client.md) — static HTML+JS от FastAPI, без React/SPA.

### 2.2. Superseded / backlog UI (сохранено для истории)

| UI-зона | Бывшая ответственность | Статус |
| :--- | :--- | :--- |
| **Auth UI** | Форма входа; сохранение/очистка JWT на клиенте (**ADR-CNT-03**) | **Superseded** для Baseline → Role Select + ADR-AUTH-DEMO-01; полный login — [backlog](../../backlog.md) (UC-01) |
| **Cabinet UI** (профиль) | Профиль; вход в списки | Future / [backlog](../../backlog.md) |
| **Admin UI** | Типы, поля, маршрут, этапы, назначения, справочники, реестр | Future / [backlog](../../backlog.md) |
| **Notifications UI** | Список in-app; mark as read | Future / [backlog](../../backlog.md) |

---

## 3. Backend — логические модули (ADR-CMP-BE)

| Модуль | Граница ответственности | Ключевые требования / статус |
| :--- | :--- | :--- |
| **HTTP / API Layer** | Приём REST, request_id, пагинация, маппинг error-matrix → ответ; раздача статики | NFR-PERF-03, NFR-LOG-01, NFR-USB-02; ADR-UI-01 |
| **Auth Module** | Baseline: валидация демо-роли / user из заголовка ([ADR-AUTH-DEMO-01](./adr-demo-role-header.md)). Выпуск JWT / password hash — backlog | Vision §12 п.7; backlog FR-AUTH-*, NFR-SEC-01/03/04 |
| **Authorization Module** | RBAC + ownership; 404 vs 403; pre-check self-approval | BR-01/14–16/21, ACL-*, NFR-SEC-02/05 |
| **Catalog Module** | Активные типы; отдача live schema для edit | FR-CAT-*, BR-10, BR-26 (live при edit) |
| **Request Module** | Create draft, edit полей, card/list, free comments, cancel | FR-REQ-*, BR-07/19/28 |
| **Submit Orchestrator** | Координация первого submit и resubmit | UC-05, BR-08/18/20/22/26 |
| **Snapshot Module** | Route snapshot (create-once); schema/value snapshot (каждый успешный submit); immutability route | BR-08/09/22/26, NFR-REL-03 |
| **Approval Engine** | Задачи этапа; approve / reject / return; first-approve; next stage / final | FR-APP-*, BR-02–05/15/17/21/25 |
| **Audit Module** | Запись и чтение HistoryEvent | FR-AUDIT-*, BR-24, NFR-LOG-02 |
| **Persistence Adapter** | Доступ к PostgreSQL (логический слой) | NFR-MNT-02 (миграции — этап реализации) |
| **Cabinet Module** | Чтение профиля | **Future / backlog** (FR-CAB-01) |
| **Admin Config Module** | CRUD типа/полей/маршрута/этапов/назначений/справочников; activate | **Future / backlog** (FR-ADMIN-*, BPMN-03) |
| **Notification Module** | Создание in-app; list; mark read | **Future / backlog** (FR-NOTIF-*, BR-11/23/29) |

### 3.1. Замечание об оркестрации

**Submit Orchestrator** и **Approval Engine** — логические координаторы use case (ADR). Они вызывают Snapshot / Audit / Persistence внутри **одной транзакции БД**, где это требуют NFR-REL-01 (и BR-29, если уведомления в scope). Notification в Baseline — backlog; при отсутствии модуля шаг Notification в TX пропускается без изобретения новых правил.

---

## 4. Диаграмма модулей API (Mermaid)

Baseline-модули в сплошных узлах; Future — пунктиром.

```mermaid
flowchart TB
  subgraph http [HTTP_API_Layer]
    Handlers[REST handlers + static]
  end

  subgraph cross [Cross_cutting]
    AuthN[Auth_Module_demo_header]
    AuthZ[Authorization_Module]
  end

  subgraph domain [Domain_modules_Baseline]
    Cat[Catalog]
    Req[Request]
    Sub[Submit_Orchestrator]
    Snap[Snapshot]
    Appr[Approval_Engine]
    Audit[Audit]
  end

  subgraph future [Future_backlog]
    Cab[Cabinet]
    Adm[Admin_Config]
    Notif[Notification]
  end

  Pers[Persistence_Adapter]
  DB[(PostgreSQL)]

  Handlers --> AuthN
  Handlers --> AuthZ
  Handlers --> Cat
  Handlers --> Req
  Handlers --> Sub
  Handlers --> Appr
  Handlers --> Audit

  Sub --> Snap
  Sub --> Appr
  Sub --> Audit
  Appr --> Snap
  Appr --> Audit
  Req --> Audit

  Cat --> Pers
  Req --> Pers
  Snap --> Pers
  Appr --> Pers
  Audit --> Pers
  AuthN --> Pers
  AuthZ --> Pers
  Pers --> DB

  Handlers -.-> Cab
  Handlers -.-> Adm
  Handlers -.-> Notif
  Cab -.-> Pers
  Adm -.-> Pers
  Notif -.-> Pers
```

---

## 5. Где реализуются ключевые бизнес-правила

| Правило | Модуль-владелец | Примечание |
| :--- | :--- | :--- |
| BR-08 route snapshot при первом submit | Snapshot (+ Submit Orchestrator) | Create iff первый submit из `draft` |
| BR-22 route не пересоздаётся на resubmit | Snapshot (+ Submit Orchestrator) | Skip create; читать существующий |
| BR-26 schema/value на каждом успешном submit | Snapshot (+ Submit Orchestrator) | Upsert после валидации live schema |
| BR-09 конфиг не ретроактивен | Admin Config (Future) пишет live; runtime читает RouteInstance | Approval Engine / Submit не читают live assignments для in-flight |
| BR-03 first-approve wins | Approval Engine | В одной TX с закрытием sibling tasks |
| BR-21 self-approval | Authorization + Approval Engine | До мутаций → `ERR_FORBIDDEN_APPROVAL` |
| BR-25 comment reject/return | Approval Engine | До мутаций → `ERR_VALIDATION` |
| BR-01/14–16 RBAC | Authorization | FE не authoritative |
| BR-24 history | Audit | В TX с бизнес-событием (NFR-REL-01) |
| BR-11/23/29 notifications | Notification | **Backlog**; см. [backlog.md](../../backlog.md) |

---

## 6. Database (логический уровень)

Хранилище сущностей conceptual model UML-CL-01: User, Role, RequestType, RequestFieldDefinition, Dictionary*, ApprovalRoute/Stage/Assignment, Request, RouteInstance, FieldValueVersion, ApprovalTask, Comment, Notification, HistoryEvent.

**Не проектируется** в Architecture: таблицы, PK/FK, индексы, JSON vs нормализация snapshot.

---

## 7. ADR сводка по компонентам

| ID | Решение | Статус |
| :--- | :--- | :--- |
| **ADR-CMP-01** | Список модулей §3 — логическое разбиение монолита | Baseline |
| **ADR-CMP-02** | UI-зоны §2 — логическое разбиение клиента | Baseline для §2.1; **SPA-предположения superseded** → [ADR-UI-01](./adr-static-web-client.md) (исходная формулировка: «логическое разбиение SPA») |
| **ADR-CMP-03** | Submit Orchestrator выделен для оркестрации RouteInstance / FieldValueVersion | Baseline |
| **ADR-CMP-04** | Authorization — отдельный cross-cutting модуль, вызываемый до domain-мутаций | Baseline |
| **ADR-UI-01** | Static HTML+JS от FastAPI; без React SPA | Baseline |

Эти ADR **не** добавляют FR/BR/NFR.

---

## 8. Трассировка

| Тип | ID |
| :--- | :--- |
| **UC** | Baseline UI → UC ядра; UC-01/02/11–13/15 — backlog |
| **FR** | по областям модулей (§3); ADMIN/NOTIF/CAB — backlog |
| **BR** | §5 |
| **UML** | UML-SEQ-01…02 → модули Baseline; UML-SEQ-03 → Admin (Future) |
| **BPMN** | BPMN-01 → Submit/Request/Snapshot; BPMN-02 → Approval Engine; BPMN-03 → Admin Config (Future) |

---

## 9. Границы

- Модули ≠ deployable services.
- Нет API-контрактов и схемы БД.
- Нет новых сущностей сверх UML-CL-01.
- Новые UI-зоны / модули сверх уже перечисленных не вводятся.
