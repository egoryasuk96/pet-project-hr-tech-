# Диаграммы процессов BPMN (TO-BE)

**Проект:** Employee Service  
**Этап:** 3.1 — BPMN TO-BE  
**Версия:** 1.0  
**Статус:** Draft  
**Источник требований:** Этап 2 (`02-requirements/`)

---

## 1. Назначение

Документ фиксирует TO-BE бизнес-процессы MVP Employee Service в нотации BPMN 2.0 и связывает их с FR / BR / UC / AC / RBAC.

Новые бизнес-правила не вводятся; scope Этапа 2 не расширяется.

---

## 2. Соглашения по нотации BPMN 2.0

| Элемент | Использование в артефактах |
| :--- | :--- |
| **Pool** | Граница процесса / системы (Employee Service) |
| **Lane** | Роль участника: `employee` (инициатор), `approver`, `admin`, Система |
| **Start Event** | Начало экземпляра процесса |
| **End Event** | Завершение ветки / процесса (в т.ч. по статусу заявки) |
| **Intermediate Event** | Промежуточные события (при необходимости) |
| **User Task** | Действие человека (роль в Lane) |
| **Service Task** | Автоматическое действие системы |
| **Call Activity** | Вызов другого описанного процесса (BPMN-02 из BPMN-01) |
| **Exclusive Gateway (XOR)** | Развилка по одному исходящему пути |
| **Sequence Flow** | Порядок шагов внутри Pool |
| **Message Flow** | Передача сообщения между участниками (in-app уведомления) |
| **Text Annotation** | Ссылка на BR / пояснение без новой логики |

**Mermaid:** `stateDiagram-v2` допускается только как **дополнительная** схема состояний/логики. Основное описание — таблицы элементов BPMN 2.0 и Sequence / Message Flow.

---

## 3. Snapshot (разделение по BR-08, BR-22, BR-26)

| Вид snapshot | Когда создаётся | После return / resubmit |
| :--- | :--- | :--- |
| **Route snapshot** | При **первом** submit из `draft` (BR-08) | **Не изменяется** (BR-22) |
| **Schema/value snapshot** | При **каждом** успешном submit — первом и повторном (BR-26, BR-22) | **Создаётся заново** (обновляется) по итогам валидации актуальной схемы |

Изменение конфигурации типа/маршрута администратором не меняет route snapshot уже отправленных заявок (BR-09).

---

## 4. Список диаграмм

| ID | Файл | Тип | Кратко |
| :--- | :--- | :--- | :--- |
| BPMN-01 | [to-be-request-lifecycle.md](./to-be-request-lifecycle.md) | Collaboration | Жизненный цикл заявки: draft → согласование → approved / rejected / cancelled; return/resubmit; cancel |
| BPMN-02 | [to-be-approval-stage.md](./to-be-approval-stage.md) | Subprocess | Обработка этапа: approve / reject / return; first-approve wins; переход этапа |
| BPMN-03 | [to-be-admin-configure.md](./to-be-admin-configure.md) | Process | Настройка типа заявки, полей, маршрута, этапов, назначений; активация |

---

## 5. Сводная трассировка

| Тип | ID | BPMN |
| :--- | :--- | :--- |
| UC | UC-04, UC-05, UC-10 | BPMN-01 |
| UC | UC-07, UC-08, UC-09 | BPMN-01 (вызов), BPMN-02 |
| UC | UC-11, UC-12 | BPMN-03 |
| FR | FR-REQ-01, FR-REQ-02, FR-REQ-03, FR-REQ-07, FR-REQ-08, FR-REQ-09 | BPMN-01 |
| FR | FR-APP-01…07 | BPMN-02 (итоги FR-APP-06/07 также в BPMN-01) |
| FR | FR-NOTIF-01, FR-AUDIT-02 | BPMN-01, BPMN-02 |
| FR | FR-ADMIN-01…05 (FR-ADMIN-06 кратко) | BPMN-03 |
| BR | BR-06, BR-07, BR-08, BR-18, BR-19, BR-20, BR-22, BR-23, BR-24, BR-26, BR-29 | BPMN-01 |
| BR | BR-02, BR-03, BR-04, BR-05, BR-14, BR-15, BR-17, BR-21, BR-25, BR-29 | BPMN-02 |
| BR | BR-02, BR-08, BR-09, BR-10, BR-12, BR-18, BR-26, BR-27 | BPMN-03 |
| AC | AC-APP-01, AC-APP-02, AC-APP-02b, AC-APP-03, AC-APP-05, AC-APP-05b, AC-APP-08, AC-REQ-07, AC-DRAFT-01, AC-DRAFT-02, AC-NOTIF-01 | BPMN-01 |
| AC | AC-APP-04, AC-APP-04b, AC-APP-05, AC-APP-05b, AC-APP-06, AC-APP-06b, AC-APP-07, AC-APP-07b, AC-APP-09, AC-ACC-02, AC-ACC-03, AC-ACC-06 | BPMN-02 |
| AC | AC-ADMIN-01, AC-APP-10, AC-APP-10b, AC-CAT-01, AC-CAT-01b, AC-DRAFT-01 | BPMN-03 |
| RBAC/ACL | дорожки employee / approver / admin; ACL-02, ACL-03, ACL-04, ACL-07, ACL-09 | BPMN-01…03 |

---

## 6. Что не моделируется отдельными BPMN

Следующие UC / FR / AC отражают вход, просмотр или доступ, а не отдельный процесс согласования. В BPMN 3.1 они не выносятся в отдельные диаграммы (могут упоминаться аннотацией как контекст):

- UC-01, UC-02, UC-03, UC-06, UC-13, UC-14, UC-15  
- FR-AUTH-*; FR-CAB-*; FR-CAT-* (кроме старта создания в BPMN-01); FR-REQ-04…06 (просмотр/свободный комментарий); FR-ADMIN-07, FR-ADMIN-08  
- AC-AUTH-01, AC-ACC-01, AC-ACC-04, AC-ACC-05, AC-CAT-02, AC-REQ-06  

---

## 7. Связанные артефакты

- [functional-requirements.md](../../02-requirements/functional-requirements.md)  
- [business-rules.md](../../02-requirements/business-rules.md)  
- [use-cases.md](../../02-requirements/use-cases.md)  
- [acceptance-criteria.md](../../02-requirements/acceptance-criteria.md)  
- [rbac-matrix.md](../../02-requirements/rbac-matrix.md)  
