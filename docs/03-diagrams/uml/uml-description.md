# Диаграммы UML (аналитическая модель)

**Продукт:** Employee Service  
**ID:** UML-00  
**Версия:** 1.1  
**Статус:** Target architecture (docs E0–E1)  
**Связанные документы:** [BPMN](../bpmn/bpmn-description.md), [ADR-LIVE-CFG-01](../architecture/adr-live-config.md), [Architecture](../architecture/architecture-description.md)

---

## 1. Назначение

Документ фиксирует состав UML-артефактов MVP Employee Service и связывает их с FR / BR / UC / AC / RBAC.

UML дополняет BPMN:

| Слой | Что показывает |
| :--- | :--- |
| BPMN | TO-BE бизнес-процессы (lanes, tasks, gateways) |
| UML | Use cases, взаимодействия (sequence), состояния заявки, conceptual class model |

---

## 2. Соглашения

| Тема | Правило |
| :--- | :--- |
| **Формат хранения** | Markdown = source of truth; визуал — встроенный Mermaid |
| **Язык** | Русский |
| **Трассировка** | В каждом файле — таблица UC / FR / BR / AC / RBAC-ACL |
| **Логические роли на sequence** | Validation, TaskFactory, RouteReader, Audit — области ответственности анализа, **не** микросервисы |
| **Activity Diagram** | Не создаются: процесс покрыт BPMN-01…03 |

### 2.1. Live configuration (target)

Канон: [ADR-LIVE-CFG-01](../architecture/adr-live-config.md), [erd-domain-model.md](../erd/erd-domain-model.md).

| Механизм | Поведение |
| :--- | :--- |
| **ApprovalRoute / Stage / Assignment** | Live-конфиг; читается при submit и approve_advance |
| **Request.current_stage_id** | FK на live ApprovalStage |
| **ApprovalTask.stage_id** | FK на live ApprovalStage; задачи из live StageAssignment |
| **RequestFieldValue** | Working values — единственный носитель значений полей |
| **ProcessTransition** | Live-переходы; Action Engine / available_actions |

**Deprecated:** RouteInstance, FieldValueVersion — [snapshot-model.md](../erd/snapshot-model.md) (Deprecated), superseded ADR-SNAP-01.

### 2.2. Критичные правила на диаграммах

- First-approve wins (BR-03)
- Запрет самосогласования (BR-21)
- Комментарий обязателен при reject/return (BR-25)
- Live config может затронуть in-flight (ADR-LIVE-CFG-01)

---

## 3. Список артефактов

| ID | Файл | Тип UML | Статус | Кратко |
| :--- | :--- | :--- | :--- | :--- |
| UML-UC-01 | [use-case-overview.md](./use-case-overview.md) | Use Case | Baseline | Актёры и UC |
| UML-SM-01 | [state-request.md](./state-request.md) | State Machine | Baseline | Статусы; current_stage_id |
| UML-SEQ-01 | [sequence-submit.md](./sequence-submit.md) | Sequence | Baseline | Submit из live route |
| UML-SEQ-02 | [sequence-approval.md](./sequence-approval.md) | Sequence | Baseline | Approve по live stages |
| UML-SEQ-03 | [sequence-admin-configure.md](./sequence-admin-configure.md) | Sequence | **Future** | Admin; live config caveat |
| UML-CL-01 | [class-domain-model.md](./class-domain-model.md) | Class (conceptual) | Baseline | ERD v2; без snapshot |

---

## 4. Сводная трассировка

| Тип | ID | UML |
| :--- | :--- | :--- |
| UC | UC-04, UC-05, UC-10 | UML-SEQ-01, UML-SM-01 |
| UC | UC-07, UC-08, UC-09 | UML-SEQ-02, UML-SM-01 |
| UC | UC-11, UC-12 | UML-SEQ-03 |
| FR | FR-REQ-* | UML-SEQ-01, UML-SM-01, UML-CL-01 |
| FR | FR-APP-* | UML-SEQ-02, UML-SM-01, UML-CL-01 |
| BR | BR-06…08, BR-18–20, BR-22, BR-26 | UML-SEQ-01, UML-SM-01 |
| BR | BR-02…05, BR-14, BR-15, BR-17, BR-21, BR-25 | UML-SEQ-02 |
| BR | BR-09, BR-10, BR-12, BR-18, BR-27 | UML-SEQ-03 |

---

## 5. Что не моделируется в UML

| Тема | Причина |
| :--- | :--- |
| RouteInstance / FieldValueVersion | Deprecated (ADR-LIVE-CFG-01) |
| Activity Diagram | Дублирует BPMN |
| Component / Deployment | Архитектура — отдельный раздел |
| ERD / OpenAPI | Отдельные артефакты |

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия индекса UML |
| 1.1 | 2026-09-23 | Live config; snapshot deprecated |
