# Диаграммы UML (аналитическая модель)

**Продукт:** Employee Service  
**ID:** UML-00  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные документы:** [BPMN](../bpmn/bpmn-description.md), [Snapshot Model](../erd/snapshot-model.md), [Architecture](../architecture/architecture-description.md)

---

## 1. Назначение

Документ фиксирует состав UML-артефактов MVP Employee Service для портфолио системного аналитика и связывает их с FR / BR / UC / AC / RBAC.

Новые бизнес-правила **не вводятся**; scope Этапа 2 и модели BPMN 3.1 **не расширяются и не противоречатся**.

UML дополняет BPMN:

| Слой | Что показывает |
| :--- | :--- |
| BPMN 3.1 | TO-BE бизнес-процессы (lanes, tasks, gateways) |
| UML 3.2 | Use cases, взаимодействия (sequence), состояния заявки, conceptual class model |

---

## 2. Соглашения

| Тема | Правило |
| :--- | :--- |
| **Формат хранения** | Markdown = source of truth; визуал — встроенный Mermaid |
| **Язык** | Русский |
| **Трассировка** | В каждом файле — таблица UC / FR / BR / AC / RBAC-ACL |
| **Логические роли на sequence** | Имена вроде Validation, Snapshot, TaskFactory, Audit, Notification — **только** области ответственности на уровне анализа. Это **не** микросервисы, **не** компоненты архитектуры и **не** API |
| **Activity Diagram** | Не создаются: процесс покрыт BPMN-01…03 |
| **ERD / API / архитектура** | Вне Этапа 3.2 |

### 2.1. RouteInstance / FieldValueVersion (без новых правил)

| Вид snapshot | Когда создаётся | После return / resubmit |
| :--- | :--- | :--- |
| **Route snapshot** | При **первом** submit из `draft` (BR-08) | **Не изменяется** (BR-22) |
| **Schema/value snapshot** | При **каждом** успешном submit (BR-26, BR-22) | **Обновляется** по итогам валидации актуальной схемы |

Изменение конфигурации администратором не меняет route snapshot уже отправленных заявок (BR-09).

### 2.2. Критичные правила, обязательные на диаграммах

- First-approve wins (BR-03)
- Запрет самосогласования (BR-21)
- Комментарий обязателен при reject/return; при approve — нет (BR-25)

---

## 3. Список артефактов

| ID | Файл | Тип UML | Статус | Кратко |
| :--- | :--- | :--- | :--- | :--- |
| UML-UC-01 | [use-case-overview.md](./use-case-overview.md) | Use Case | Baseline | Актёры и UC |
| UML-SM-01 | [state-request.md](./state-request.md) | State Machine | Baseline | Статусы заявки и переходы |
| UML-SEQ-01 | [sequence-submit.md](./sequence-submit.md) | Sequence | Baseline | Create / submit / resubmit / cancel |
| UML-SEQ-02 | [sequence-approval.md](./sequence-approval.md) | Sequence | Baseline | Approve / reject / return |
| UML-SEQ-03 | [sequence-admin-configure.md](./sequence-admin-configure.md) | Sequence | **Future** | Admin-конфиг; [backlog](../../backlog.md) |
| UML-CL-01 | [class-domain-model.md](./class-domain-model.md) | Class (conceptual) | Baseline | Предметная модель; **не ERD** |

---

## 4. Сводная трассировка

| Тип | ID | UML |
| :--- | :--- | :--- |
| UC | UC-01…UC-15 | UML-UC-01 |
| UC | UC-04, UC-05, UC-10 | UML-SEQ-01, UML-SM-01 |
| UC | UC-07, UC-08, UC-09 | UML-SEQ-02, UML-SM-01 |
| UC | UC-11, UC-12 | UML-SEQ-03 |
| FR | FR-REQ-*, FR-AUDIT-02; FR-NOTIF-01 — **Future / backlog** | UML-SEQ-01, UML-SM-01, UML-CL-01 |
| FR | FR-APP-* | UML-SEQ-02, UML-SM-01, UML-CL-01 |
| FR | FR-ADMIN-01…06 | UML-SEQ-03, UML-CL-01 |
| BR | BR-06…08, BR-18–20, BR-22, BR-26; BR-29 — **Future / backlog** | UML-SEQ-01, UML-SM-01 |
| BR | BR-02…05, BR-14, BR-15, BR-17, BR-21, BR-25 | UML-SEQ-02 |
| BR | BR-09, BR-10, BR-12, BR-18, BR-27 | UML-SEQ-03 |
| BR | BR-08, BR-09, BR-22, BR-26 (структура) | UML-CL-01 |
| AC | AC-APP-01…03, AC-APP-08, AC-REQ-07, AC-DRAFT-*; AC-NOTIF-01 — **Future / backlog** | UML-SEQ-01 |
| AC | AC-APP-04…07b, AC-APP-09, AC-ACC-02, AC-ACC-03, AC-ACC-06 | UML-SEQ-02 |
| AC | AC-ADMIN-01, AC-APP-10, AC-APP-10b, AC-CAT-01*, AC-ACC-04 | UML-SEQ-03 |

---

## 5. Что не моделируется в Этапе 3.2

| Тема | Причина |
| :--- | :--- |
| Activity Diagram | Дублирует BPMN-01…03 |
| Component / Deployment / Package | Архитектура — позже |
| ERD / физическая модель БД | Отдельный этап (`03-diagrams/erd/`) |
| Sequence с HTTP / OpenAPI path | Контракт API — позже |
| Отдельные sequence для login / profile / catalog / notifications | Достаточно Use Case (аналогично BPMN §6) |
| Новые статусы, роли, правила | Запрещено |

---

## 6. Связанные артефакты

- [Vision & Scope](../../01-vision-and-scope/vision-scope.md)
- [Глоссарий](../../01-vision-and-scope/glossary.md)
- [functional-requirements.md](../../02-requirements/functional-requirements.md)
- [business-rules.md](../../02-requirements/business-rules.md)
- [use-cases.md](../../02-requirements/use-cases.md)
- [acceptance-criteria.md](../../02-requirements/acceptance-criteria.md)
- [rbac-matrix.md](../../02-requirements/rbac-matrix.md)
- [bpmn-description.md](../bpmn/bpmn-description.md)

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия индекса UML (Этап 3.2) |
