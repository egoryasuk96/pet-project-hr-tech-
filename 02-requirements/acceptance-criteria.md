# Acceptance Criteria

**Проект:** Employee Service  
**Документ:** Acceptance Criteria  
**Версия:** 1.0  
**Статус:** Draft (Этап 2)

Формат преимущественно Given / When / Then. Каждый AC имеет ID и ссылки на FR/BR.

---

## 1. Создание заявки

### AC-APP-01 — Создание draft
**Related:** FR-REQ-01, BR-19

Given пользователь с ролью `employee` аутентифицирован  
And существует активный тип заявки «Отпуск»  
When он создаёт заявку этого типа  
Then система сохраняет заявку со статусом `draft`  
And инициатор равен текущему пользователю  
And в истории есть событие создания

---

## 2. Submit

### AC-APP-02 — Первый submit из draft
**Related:** FR-REQ-03, BR-08, BR-20

Given заявка в статусе `draft` с заполненными обязательными полями  
And у типа настроен валидный маршрут (≥1 этап, у каждого этапа ≥1 назначение)  
When инициатор выполняет submit  
Then статус заявки становится `in_approval`  
And создан snapshot маршрута  
And созданы задачи согласования для первого этапа  
And согласующие первого этапа получают in-app уведомления  
And в истории есть событие submit

### AC-APP-02b — Submit при невалидном маршруте
**Related:** FR-REQ-03, BR-18, ERR_ROUTE_CONFIG

Given заявка в `draft`  
And маршрут типа без этапов или без назначений  
When инициатор выполняет submit  
Then система возвращает ERR_ROUTE_CONFIG  
And статус остаётся `draft`  
And задачи не создаются

---

## 3. Создание задачи первого этапа

### AC-APP-03 — Задачи первого этапа после submit
**Related:** FR-REQ-03, FR-APP-01, BR-20

Given успешный submit заявки с маршрутом из двух этапов  
And на этап 1 назначены пользователь A (user) и роль `approver` (пользователи B и C имеют роль)  
When submit завершён  
Then созданы открытые задачи для всех assignees этапа 1 согласно правилам назначения  
And в очереди A, B и C видны соответствующие задачи  
And текущий этап заявки = этап 1

---

## 4. Approve

### AC-APP-04 — Успешный approve
**Related:** FR-APP-03, BR-15

Given у согласующего A есть открытая задача по заявке в `in_approval`  
And A не является инициатором  
When A выполняет approve  
Then задача A переходит в завершённое состояние  
And в истории есть событие approve

---

## 5. Переход на следующий этап и завершение маршрута

### AC-APP-05 — Переход на следующий этап
**Related:** FR-APP-06, BR-02

Given маршрут из 2 этапов, заявка на этапе 1  
When выполнен успешный approve этапа 1  
Then текущий этап становится этапом 2  
And создаются задачи этапа 2  
And статус заявки остаётся `in_approval`  
And согласующие этапа 2 получают уведомления

### AC-APP-05b — Завершение маршрута
**Related:** FR-APP-07, BR-17

Given заявка на последнем этапе snapshot  
When выполнен успешный approve этого этапа  
Then статус заявки = `approved`  
And открытых задач нет  
And инициатор получает уведомление о завершении

---

## 6. Reject

### AC-APP-06 — Reject завершает заявку
**Related:** FR-APP-04, BR-04

Given заявка в `in_approval` на любом этапе  
And у согласующего есть открытая задача  
When он выполняет reject (с комментарием)  
Then статус заявки = `rejected`  
And все открытые задачи текущего этапа закрыты  
And задачи следующих этапов не создаются  
And инициатор получает уведомление  
And в истории есть reject

---

## 7. Return

### AC-APP-07 — Return на доработку
**Related:** FR-APP-05, FR-REQ-08, BR-05

Given заявка в `in_approval` на этапе N  
When согласующий выполняет return (с комментарием)  
Then статус = `returned`  
And сохранён признак текущего этапа N для повторного submit  
And открытые задачи этапа N закрыты  
And инициатор получает уведомление  
And инициатор может редактировать поля заявки

---

## 8. Повторный submit

### AC-APP-08 — Resubmit с того же этапа
**Related:** FR-REQ-09, BR-06, BR-22

Given заявка в `returned` после return на этапе 2 из 3  
And инициатор изменил значения полей  
When инициатор выполняет submit  
Then статус = `in_approval`  
And snapshot маршрута не пересоздаётся (идентичен сохранённому)  
And создаются задачи этапа 2 (не этапа 1)  
And в истории есть событие повторной отправки

---

## 9. First-approve wins

### AC-APP-09 — Достаточно одного approve
**Related:** FR-APP-03, BR-03

Given на текущем этапе открыты задачи у согласующих A и B  
When A выполняет approve  
Then этап считается пройденным  
And задача B закрывается системой без возможности решения  
And B при попытке approve получает ERR_TASK_DONE или ERR_DUP_ACTION  
And заявка переходит на следующий этап или в `approved` по правилам маршрута

---

## 10. Snapshot маршрута

### AC-APP-10 — Изоляция от изменений конфигурации
**Related:** FR-REQ-03, FR-ADMIN-03–05, BR-08, BR-09

Given заявка уже отправлена (есть snapshot с этапами E1→E2, assignees X)  
When администратор меняет маршрут типа (добавляет E3 или меняет assignees на Y)  
And согласующий выполняет approve по заявке  
Then согласование продолжается по исходному snapshot (E1→E2, assignees X)  
And новый этап E3 для этой заявки не появляется

### AC-APP-10b — Новый submit использует новую конфигурацию
**Related:** BR-08, BR-09

Given администратор изменил маршрут типа  
When сотрудник создаёт новую заявку и делает первый submit  
Then snapshot новой заявки соответствует актуальной конфигурации на момент submit

---

## 11. Права доступа

### AC-ACC-01 — Сотрудник не видит чужую заявку
**Related:** FR-REQ-04, BR-01, ACL-01

Given сотрудник S1 создал заявку R  
And сотрудник S2 аутентифицирован  
When S2 запрашивает карточку R  
Then система возвращает ERR_NOT_FOUND (или ERR_FORBIDDEN — единообразно по NFR-SEC-05)  
And данные заявки не раскрываются

### AC-ACC-02 — Согласующий не действует по чужой задаче
**Related:** FR-APP-03–05, BR-15, ACL-02

Given открытая задача назначена пользователю A  
And пользователь B не является assignee этой задачи  
When B пытается approve/reject/return  
Then ERR_FORBIDDEN_APPROVAL  
And состояние заявки не меняется

### AC-ACC-03 — Запрет самосогласования
**Related:** BR-21, ACL-03

Given инициатор заявки также имеет роль `approver` и попал в назначение этапа  
When он пытается approve/reject/return по своей заявке  
Then ERR_FORBIDDEN_APPROVAL  
And статус заявки не меняется

### AC-ACC-04 — Админка только для admin
**Related:** FR-ADMIN-01, ACL-04

Given пользователь без роли `admin`  
When он пытается создать/изменить тип заявки  
Then ERR_FORBIDDEN

### AC-ACC-05 — Admin видит реестр
**Related:** FR-ADMIN-07, BR-13

Given пользователь с ролью `admin`  
When он открывает реестр заявок  
Then он видит заявки всех инициаторов

---

## 12. Неактивный тип заявки

### AC-CAT-01 — Неактивный тип скрыт и недоступен
**Related:** FR-CAT-01, FR-REQ-01, BR-10

Given тип T был активен, затем admin установил `is_active = false`  
When сотрудник открывает каталог  
Then T отсутствует в списке  
When сотрудник пытается создать заявку типа T (прямой запрос)  
Then ERR_INACTIVE_TYPE  
And новая заявка не создаётся

### AC-CAT-01b — Уже созданные заявки живут
**Related:** BR-10, BR-09

Given по типу T уже есть заявка в `in_approval`  
When admin деактивирует T  
Then существующая заявка продолжает согласование  
And тип T не показывается в каталоге для новых заявок

---

## 13. Отмена

### AC-REQ-07 — Отмена только draft/returned
**Related:** FR-REQ-07, BR-07

Given заявка в статусе `draft`  
When инициатор отменяет её  
Then статус = `cancelled`

Given заявка в статусе `returned`  
When инициатор отменяет её  
Then статус = `cancelled`

Given заявка в статусе `in_approval`  
When инициатор пытается отменить  
Then ERR_INVALID_STATE  
And статус остаётся `in_approval`

---

## 14. Сводка AC

| ID | Тема |
| :--- | :--- |
| AC-APP-01 | Создание draft |
| AC-APP-02 | Первый submit |
| AC-APP-02b | Submit при плохом маршруте |
| AC-APP-03 | Задачи первого этапа |
| AC-APP-04 | Approve |
| AC-APP-05 | Переход на следующий этап |
| AC-APP-05b | Завершение маршрута |
| AC-APP-06 | Reject |
| AC-APP-07 | Return |
| AC-APP-08 | Повторный submit |
| AC-APP-09 | First-approve wins |
| AC-APP-10 | Snapshot изоляция |
| AC-APP-10b | Новый submit — новая конфигурация |
| AC-ACC-01 | Чужая заявка |
| AC-ACC-02 | Чужая задача |
| AC-ACC-03 | Самосогласование |
| AC-ACC-04 | Админка forbidden |
| AC-ACC-05 | Реестр admin |
| AC-CAT-01 | Неактивный тип |
| AC-CAT-01b | Живые заявки после деактивации |
| AC-REQ-07 | Отмена |

**Количество AC: 21**

---

## 15. Open Questions

| ID | Вопрос | Предложение |
| :--- | :--- | :--- |
| OQ-AC-01 | Точный HTTP для чужой заявки | 404 + ERR_NOT_FOUND |
| OQ-AC-02 | Обязательность комментария в AC reject/return | Обязателен (согласовать с OQ-FR-01) |

---

## 16. Трассировка

| AC | FR | BR |
| :--- | :--- | :--- |
| AC-APP-01 | FR-REQ-01 | BR-19 |
| AC-APP-02 | FR-REQ-03 | BR-08, BR-20 |
| AC-APP-03 | FR-REQ-03, FR-APP-01 | BR-20 |
| AC-APP-04 | FR-APP-03 | BR-15 |
| AC-APP-05 | FR-APP-06 | BR-02 |
| AC-APP-05b | FR-APP-07 | BR-17 |
| AC-APP-06 | FR-APP-04 | BR-04 |
| AC-APP-07 | FR-APP-05 | BR-05 |
| AC-APP-08 | FR-REQ-09 | BR-06, BR-22 |
| AC-APP-09 | FR-APP-03 | BR-03 |
| AC-APP-10 | FR-REQ-03, FR-ADMIN-03 | BR-08, BR-09 |
| AC-ACC-01 | FR-REQ-04 | BR-01 |
| AC-ACC-02 | FR-APP-03–05 | BR-15 |
| AC-ACC-03 | FR-APP-03–05 | BR-21 |
| AC-CAT-01 | FR-CAT-01, FR-REQ-01 | BR-10 |
| AC-REQ-07 | FR-REQ-07 | BR-07 |
