# Глоссарий

**Продукт:** Employee Service  
**ID:** DOC-GLOSSARY  
**Версия:** 1.2  
**Статус:** Target architecture (docs E0–E1)  
**Связанные документы:** [Vision & Scope](./vision-scope.md), [ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md), [Business Rules](../02-requirements/business-rules.md), [Consistency Review](../consistency-review.md)

Термины ниже используются единообразно во всей документации и реализации MVP. Синонимы в скобках допустимы в UI-текстах, но в требованиях и API предпочтительны основные термины.

---

## A–Z / системные имена

### Employee Service
Веб-система личного кабинета сотрудника и сервиса подачи и согласования заявок. Название продукта pet-project.

### Approval Engine
Встроенный механизм последовательного согласования заявок по **live-маршруту** типа заявки (`ApprovalRoute` / `ApprovalStage` / `StageAssignment`). Не является внешним BPM-движком. При submit и approve_advance читает актуальную конфигурацию ([ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md)).

### Action Engine
Механизм расчёта доступных действий над заявкой (`available_actions`) и выполнения переходов по таблице **ProcessTransition** (process + from_status + action + role → to_status + effect). Эффект `approve_advance` продвигает заявку по live-этапам. См. [ADR-ACTION-01](../03-diagrams/architecture/adr-configurable-actions.md).

### First-approve wins
Правило этапа: если на этап назначено несколько согласующих, достаточно одного решения `approve` для перехода заявки на следующий этап (или в статус `approved`, если этап последний).

### Working Values
Текущие редактируемые значения полей заявки в статусах `draft` / `returned` (сущность **RequestFieldValue**). Единственный носитель значений полей в runtime; snapshot-версий нет.

### JWT
JSON Web Token — Target AuthN ([ADR-AUTH-JWT-01](../03-diagrams/architecture/adr-jwt-core-api.md)): `POST /auth/login`, Bearer. Demo-header ([ADR-AUTH-DEMO-01](../03-diagrams/architecture/adr-demo-role-header.md)) — superseded / historical.

---

## Устаревшие термины (historical / deprecated)

> Сущности ниже **не входят** в актуальную архитектуру. Оставлены для трассировки старых документов. Канон отказа: [ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md), superseded [ADR-SNAP-01](../03-diagrams/architecture/adr-snapshot-submit-versions.md).

### Экземпляр маршрута (RouteInstance) — *deprecated*
~~Набор этапов и назначений конкретной заявки, зафиксированный при первом submit.~~ Заменено: `Request.current_stage_id` → live `ApprovalStage`.

### FieldValueVersion — *deprecated*
~~Схема и значения полей на момент submit.~~ Заменено: working `RequestFieldValue` + `HistoryEvent`.

---

## Организационная модель

### Company (компания)
Юридическое лицо / организация в справочнике. Демо: одна company. См. [ADR-ORG-01](../03-diagrams/architecture/adr-org-model.md).

### Department (подразделение)
Подразделение внутри Company. Не используется для auto-routing согласования (BR-12).

### Employee (сотрудник)
Кадровая запись: ФИО, табельный номер, должность, department, manager. Связь с User — 0..1. Оргструктура — данные, не маршрутизация.

---

## Процесс и переходы (live config)

### Process (процесс)
Контейнер бизнес-процесса; владеет типами заявок и таблицей ProcessTransition.

### Status (статус)
Сущность с `id/code/name` (`draft`, `in_approval`, `returned`, `approved`, `rejected`, `cancelled`). Request хранит `status_id` (FK).

### Action (действие)
Сущность с `id/code/name` (`submit`, `cancel`, `approve`, `reject`, `return`). Используется в ProcessTransition и UI `available_actions`.

### ProcessTransition
Строка live-конфигурации: `(process_id, from_status_id, action_id, role_id) → to_status_id, effect`. Читается в runtime. Изменения **могут затронуть** in-flight заявки ([ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md)).

---

## Роли и участники

### Инициатор
Пользователь, создавший заявку. В типичном сценарии — сотрудник. Инициатор отслеживает статус, может отменить заявку в статусах `draft` и `returned`, а также доработать заявку после возврата.

### Сотрудник (`employee`)
Системная роль пользователя личного кабинета. Может создавать заявки из каталога, работать со своими заявками.

### Согласующий (`approver`)
Системная роль пользователя, участвующего в согласовании. Обрабатывает задачи согласования, на которые назначен лично или через роль.

### Администратор (`admin`)
Системная роль для настройки типов заявок, маршрутов, этапов, назначений, справочников (в MVP — backlog / Future).

### Assignee (назначенный)
Пользователь или носитель роли, указанный в **StageAssignment** live-маршрута и получающий **ApprovalTask**.

---

## Каталог и заявки

### Каталог заявок (каталог услуг)
Список активных типов заявок, доступных сотруднику для создания заявки (в MVP — seed).

### Тип заявки (Request Type)
Услуга каталога: название, описание, признак активности, схема полей формы и связанный **live** маршрут согласования.

### Схема полей типа (Request Schema)
Набор определений полей формы (**Request Field** / поле типа заявки), по которым инициатор заполняет заявку. Live-конфиг; при edit draft/returned — актуальная схема (BR-26).

### Поле типа заявки (Request Field)
Элемент схемы формы типа заявки. Определяет, какие данные сотрудник заполняет при создании заявки.

### Заявка (Request)
Экземпляр типа заявки, созданный инициатором. Содержит `status_id`, `current_stage_id` (FK на live `ApprovalStage`, nullable вне согласования), working values, историю и задачи согласования.

### Черновик (Draft)
Заявка в статусе `draft`, ещё не отправленная на согласование.

### Статус заявки
Текущее состояние жизненного цикла заявки в MVP:

| Код | Смысл |
| :--- | :--- |
| `draft` | Черновик; не на согласовании |
| `in_approval` | На согласовании (In Approval) |
| `returned` | Возвращена на доработку инициатору (Returned) |
| `approved` | Согласована по всем этапам маршрута (Approved) |
| `rejected` | Отклонена на одном из этапов (Rejected) |
| `cancelled` | Отменена инициатором (Cancelled) |

### Значение поля заявки
Конкретные данные, введённые инициатором по схеме полей типа заявки (**RequestFieldValue** / Working Values).

### Комментарий (Comment)
Текстовое пояснение к заявке или к решению по этапу (например, причина возврата или отклонения).

---

## Согласование

### Маршрут согласования (Route / маршрут)
Упорядоченная последовательность **live** этапов (`ApprovalRoute` → `ApprovalStage`). В MVP маршрут всегда последовательный. Читается в runtime при submit и approve_advance.

### Этап согласования (этап)
Один шаг live-маршрута с `sequence_no` и набором **StageAssignment**.

### Назначение на этап (StageAssignment)
Правило, кто может согласовать этап: роль и/или конкретный пользователь. При submit задачи создаются из **актуальных** StageAssignment текущего этапа.

### Задача согласования (Approval Task / ApprovalTask)
Рабочий элемент для согласующего: `request_id`, `stage_id` (live), `assignee_user_id`, `status`, `comment`, `created_at`, `completed_at`.

### Очередь задач
Список открытых задач согласования текущего пользователя-согласующего.

### Согласование (approve)
Положительное решение по задаче этапа.

### Отклонение (reject)
Отрицательное решение по задаче этапа. Завершает заявку со статусом `rejected`.

### Возврат на доработку (return)
Решение согласующего вернуть заявку инициатору (`returned`). После редактирования инициатор повторно отправляет заявку; согласование продолжается с **первого** live-этапа (BR-06).

### Отмена заявки
Действие инициатора → `cancelled`. В MVP только для `draft` и `returned`.

---

## Уведомления, история, администрирование

### Уведомление (in-app)
In-app сообщение: создание на событиях BR-23 и список (`GET /notifications`, UC-13) — **Target-active**. Mark-as-read (FR-NOTIF-03) и email/push — **Future / backlog**.

### История действий (HistoryEvent / история изменений)
Журнал значимых событий по заявке (UC-14, BR-24). Аудит без обязательного полного payload значений.

### Справочник / элемент справочника
Набор справочных значений для полей форм (настройка — backlog).

### Административная панель (админка)
Настройка типов, маршрутов, справочников — Future / [backlog](../backlog.md). Правки live-конфига **могут затронуть** in-flight заявки ([ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md)).

### Личный кабинет
Каталог и свои заявки — Target UI-срез. Профиль (UC-02 / FR-CAB-01) — backlog. Список уведомлений — Target; вход из «кабинета» (FR-CAB-03) — backlog.

---

## Технические термины MVP

### REST API
HTTP-интерфейс backend; контракт — OpenAPI.

### OpenAPI
Спецификация контракта REST API.

### PostgreSQL
Реляционная СУБД.

### MVP
Minimal Viable Product — минимально достаточная версия в утверждённых границах scope.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-18 | Первая версия глоссария |
| 1.1 | 2026-09-20 | RouteInstance / FieldValueVersion; EN-якоря терминов; Baseline v1.0 |
| 1.2 | 2026-09-23 | Live config; Process/Status/Action/Transition; org; Action Engine; snapshot → deprecated |
