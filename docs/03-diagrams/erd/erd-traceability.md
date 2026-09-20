# ERD-MAP — Traceability (Stage 3.4)

**Продукт:** Employee Service  
**ID:** ERD-MAP  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [README.md](./README.md), [Snapshot Model](./snapshot-model.md)

---

## 1. Назначение

Показать, какие требования, процессы и архитектурные модули поддерживаются сущностями / связями логической модели данных. Новые FR/BR **не** вводятся.

---

## 2. Сущности → требования

| Entity | FR | BR | UC (основные) |
| :--- | :--- | :--- | :--- |
| User, Role, UserRole | FR-AUTH-01…03, FR-CAB-01 | BR-16, BR-27 | UC-01, UC-02 |
| RequestType, RequestFieldDefinition | FR-CAT-01…03, FR-ADMIN-01…02 | BR-10, BR-18, BR-26 | UC-03, UC-04, UC-11 |
| Dictionary, DictionaryItem | FR-ADMIN-06, FR-CAT-03 | — | UC-11 |
| ApprovalRoute, ApprovalStage, StageAssignment | FR-ADMIN-03…05 | BR-02, BR-12, BR-18 | UC-12 |
| Request | FR-REQ-01…09, FR-CAB-02, FR-ADMIN-07 | BR-01, BR-07, BR-19, BR-20, BR-27 | UC-04…06, UC-10, UC-15 |
| RequestFieldValue | FR-REQ-02, FR-REQ-09 | BR-26 | UC-04, UC-05 |
| RouteInstance* | FR-REQ-03, FR-REQ-09 | BR-08, BR-09, BR-22 | UC-05 |
| FieldValueVersion | FR-REQ-03, FR-REQ-09 | BR-22, BR-26 | UC-05 |
| ApprovalTask | FR-APP-01…07 | BR-03…06, BR-15, BR-17, BR-21 | UC-07…09 |
| Comment | FR-REQ-06, FR-APP-03…05 | BR-25, BR-28 | UC-05, UC-07…09 |
| HistoryEvent | FR-AUDIT-01…02, FR-ADMIN-08 | BR-24; retention NFR-LOG-02, NFR-LOG-03 п.2 | UC-14 |
| Notification | FR-NOTIF-01…03, FR-CAB-03 | BR-11, BR-23, BR-29 | UC-13 |

---

## 3. Критичные BR → поддержка моделью

| BR | Как поддерживается |
| :--- | :--- |
| BR-01 | Request.initiator_id; видимость — слой AuthZ, данные позволяют фильтр |
| BR-02 | sequence_no на live и snapshot stages; current_stage_number |
| BR-03 | ApprovalTask.status open→completed/cancelled на одном stage_number |
| BR-04 / BR-05 / BR-17 | Request.status + закрытие задач этапа |
| BR-06 / BR-22 | current_stage_number сохранён (OQ-A); RouteInstance keep; новая FieldValueVersion |
| BR-07 | status enum + constraint cancel only draft/returned |
| BR-08 / BR-09 | RouteInstance 1—0..1 write-once; config tables изолированы |
| BR-10 | RequestType.is_active |
| BR-11 / BR-23 / BR-29 | Notification entity; TX — runtime/architecture |
| BR-12 | StageAssignment role/user; нет org entities |
| BR-13 / BR-14 | данные + AuthZ; Approver через наличие ApprovalTask |
| BR-15 | ApprovalTask.assignee_id |
| BR-16 | UserRole M:N |
| BR-18 | валидация route на activate/submit (логические constraints C-11) |
| BR-19 / BR-20 | status draft → in_approval |
| BR-21 | initiator ≠ assignee на действиях |
| BR-24 | HistoryEvent; **без** обязательного полного snapshot payload |
| BR-25 | Comment.kind=decision + text required for reject/return |
| BR-26 | RequestFieldValue (live) vs FieldValueVersion (frozen) |
| BR-27 | create Request только с employee; нет «admin-as-initiator» сущности |
| BR-28 | Comment.kind=free при in_approval |

---

## 4. NFR retention (не смешивать)

| Store | NFR | Retention | ERD |
| :--- | :--- | :--- | :--- |
| HistoryEvent (прикладной аудит) | NFR-LOG-02, NFR-LOG-03 п.2 | **60 дней** | Да |
| Technical API logs | NFR-LOG-01, NFR-LOG-03 п.1 | **14 дней** | **Нет** (infra) |

---

## 5. BPMN → сущности

| BPMN | Сущности |
| :--- | :--- |
| BPMN-01 Request lifecycle | Request, RequestFieldValue, RouteInstance*, FieldValueVersion, ApprovalTask, HistoryEvent, Notification, Comment |
| BPMN-02 Approval stage | ApprovalTask, RouteInstance*, Request, Comment, HistoryEvent, Notification |
| BPMN-03 Admin configure | RequestType, FieldDefinition, ApprovalRoute/Stage/Assignment, Dictionary*; **не** мутирует in-flight RouteInstance |

---

## 6. UML → сущности

| UML | Сущности |
| :--- | :--- |
| UML-CL-01 | Все основные классы + уточнения RequestFieldValue, RouteInstance children |
| UML-SM-01 | Request.status, current_stage_number, наличие snapshots |
| UML-SEQ-01 | RouteInstance create-once; FieldValueVersion append; HistoryEvent |
| UML-SEQ-02 | ApprovalTask first-approve; Comment decision; BR-21/25 |
| UML-SEQ-03 | live config only; isolation BR-09 |
| UML-UC-01 | покрытие актёров через Role/UserRole |

---

## 7. Architecture modules → сущности

| Module | Owns / reads |
| :--- | :--- |
| Auth / Authorization | User, Role, UserRole |
| Cabinet | User profile fields; entry to Notification |
| Catalog | RequestType, RequestFieldDefinition (active) |
| Request | Request, RequestFieldValue, Comment |
| Submit Orchestrator | оркестрация → Snapshot + ApprovalTask + Audit + Notification |
| Snapshot | RouteInstance*, FieldValueVersion |
| Approval Engine | ApprovalTask; reads RouteInstance |
| Admin Config | live config entities; не пишет RouteInstance заявок |
| Audit | HistoryEvent |
| Notification | Notification |
| Persistence | все выше в одной PostgreSQL |

---

## 8. RBAC / ACL → данные

| Правило | Данные |
| :--- | :--- |
| ACL employee own requests | Request.initiator_id |
| ACL approver via tasks | ApprovalTask.assignee_id (+ история задач) |
| ACL admin all | Role.code=admin (без отдельной «всей» таблицы) |
| Hidden/foreign → 404 | AuthZ поверх тех же ключей (NFR-SEC-05) |
| No role switcher | UserRole union |
| Admin не создаёт заявки | отсутствие обходного initiator override |

---

## 9. Snapshot model mapping

| Инвариант | Entity / relation |
| :--- | :--- |
| Route create-once | RouteInstance.request_id unique; created only on first submit |
| Route immutable | no update path for children after create |
| Schema/value each submit | FieldValueVersion 0..N per Request (submit_number) |
| Resubmit values | append FieldValueVersion (не replace) |
| FieldValueVersion | Версии значений по submit_number; канон — [snapshot-model.md](./snapshot-model.md) |
| History without full payload | HistoryEvent.action/from/to/comment only |

Детали: [snapshot-model.md](./snapshot-model.md).

---

## 10. Границы трассировки

- Не трассируются будущие OpenAPI paths.
- Не добавляются сущности «для удобства диаграммы» сверх утверждённого плана.
- Technical logs намеренно вне матрицы сущностей.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия ERD traceability |
