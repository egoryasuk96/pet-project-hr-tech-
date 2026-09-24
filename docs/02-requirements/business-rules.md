# Бизнес-правила

**Продукт:** Employee Service  
**Документ:** Business Rules  
**ID:** DOC-BR  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные артефакты:** [Vision & Scope](../01-vision-and-scope/vision-scope.md), [Глоссарий](../01-vision-and-scope/glossary.md), [ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md), [Backlog](../backlog.md)

---

## 1. Назначение

Документ фиксирует бизнес-правила **MVP Baseline**, обязательные для реализации и проверки. Правила имеют устойчивые ID `BR-XX` и используются в FR, UC и AC.  
Правила вне Baseline сохранены в [docs/backlog.md](../backlog.md).

---

## 2. Правила доступа и видимости

### BR-01 — Видимость заявок сотрудника
Сотрудник (`employee`) видит только заявки, где он является инициатором.  
**Связи:** FR-REQ-04, UC-06, AC-ACC-01

### BR-14 — Видимость заявок согласующего
Согласующий (`approver`) может просматривать **полную карточку** заявки, по которой у него есть задача согласования — **активная или завершённая** (включая `cancelled` после first-approve), в пределах RBAC. Чужие заявки без связанной задачи недоступны.  
**Связи:** FR-APP-01, FR-APP-02, FR-REQ-04, UC-07, ACL / RBAC

### BR-15 — Действие только по своей задаче
Согласующий может выполнить approve / reject / return только по задаче, где он является assignee (лично или через роль, по которой задача создана для него), и только если задача в статусе открыта.  
**Связи:** FR-APP-03, FR-APP-04, FR-APP-05, AC-ACC-02

### BR-16 — Одна роль на пользователя
У каждого пользователя ровно одна системная роль (`users.role_id` → `employee` | `approver` | `admin`). Таблица M:N `UserRole` в Target **нет** ([ADR-ORG-01](../03-diagrams/architecture/adr-org-model.md)).

1. После авторизации пользователь видит разделы и действия, разрешённые **его** ролью.
2. Выбор «активной роли» не требуется.
3. Администратор может изменить `role_id` пользователя в Admin UI.
4. Роль участвует в выборе доступных `ProcessTransition` (Action Engine).
5. Право выполнить approve/reject/return дополнительно требует быть assignee открытой `ApprovalTask` (BR-15), независимо от роли `approver`.

**Legacy / Previous:** модель с несколькими ролями и union permissions (M:N UserRole) — не Target.

**Связи:** матрица RBAC; ADR-ORG-01; login/JWT — [ADR-AUTH-JWT-01](../03-diagrams/architecture/adr-jwt-core-api.md)

---

## 3. Правила маршрута и согласования

### BR-02 — Последовательный маршрут
Маршрут согласования выполняется строго последовательно: следующий этап начинается только после успешного завершения предыдущего. Параллельные этапы в MVP не используются.  
**Связи:** FR-APP-06, UC-07, AC-APP-05

### BR-03 — First-approve wins
Если на одном этапе несколько согласующих, первый успешный `approve` завершает этап. Все остальные **активные** задачи этого этапа переводятся в статус `cancelled`. Затем система либо создаёт задачи следующего этапа, либо переводит заявку в `approved`, если этап был последним.  
**Связи:** FR-APP-03, FR-APP-06, FR-APP-07, AC-APP-09

### BR-04 — Reject завершает заявку
Решение `reject` на любом этапе переводит заявку в статус `rejected` и завершает маршрут. Последующие этапы не создаются.  
**Связи:** FR-APP-04, UC-08, AC-APP-06

### BR-05 — Return на доработку
Решение `return` переводит заявку в статус `returned`, закрывает открытые задачи текущего этапа и возвращает заявку инициатору на доработку. Номер этапа возврата сохраняется для аудита; при повторном submit согласование начнётся с первого этапа (BR-06).  
**Связи:** FR-REQ-08, FR-APP-05, UC-09, AC-APP-07

### BR-17 — Завершение маршрута
Если выполнен `approve` на последнем этапе live-маршрута, заявка переходит в статус `approved` (`status_id`).  
**Связи:** FR-APP-07, AC-APP-05b

### BR-18 — Валидация маршрута при активации и при submit
Маршрут считается валидным, если содержит минимум один этап и каждый этап имеет хотя бы одно назначение (роль и/или пользователь).

1. При **публикации / активации** типа заявки (`is_active = true`) система проверяет валидность маршрута. Некорректный маршрут не позволяет активировать тип (ERR_ROUTE_CONFIG или ERR_VALIDATION).
2. При **submit** маршрут проверяется повторно. Некорректный маршрут не позволяет отправить заявку (ERR_ROUTE_CONFIG). Тип при submit также должен быть активен.

**Связи:** FR-REQ-03, AC-APP-02b, ERR_ROUTE_CONFIG; активация типа (admin) — [docs/backlog.md](../backlog.md)

### BR-12 — Нет auto-routing по оргструктуре
Система не определяет согласующего автоматически через оргструктуру или «непосредственного руководителя». Назначения задаются явно: роль и/или конкретный пользователь.  
В Baseline явные назначения задаются seed/test data. Admin UI для настройки этих назначений — [docs/backlog.md](../backlog.md).  
**Связи:** Vision §12, FR-REQ-03; Admin UI — FR-ADMIN-05 в [docs/backlog.md](../backlog.md)

---

## 4. Правила жизненного цикла заявки

### BR-06 — Повторная отправка после return
После `return` инициатор может изменить значения полей заявки (в статусе `returned`) и повторно отправить её на согласование. Повторный submit возобновляет согласование **с первого этапа** актуального (live) маршрута: `current_stage_id` → первый `ApprovalStage`, новые `ApprovalTask` по live assignments. Snapshot маршрута / версий значений **не** создаётся ([ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md)).  
**Связи:** FR-REQ-09, UC-05, AC-APP-08

### BR-07 — Отмена только draft и returned
Инициатор может отменить заявку только в статусах `draft` и `returned`. Отмена переводит заявку в `cancelled`. Отмена из `in_approval`, `approved`, `rejected`, `cancelled` запрещена.  
**Связи:** FR-REQ-07, UC-10, AC-REQ-07

### BR-19 — Создание заявки как draft
Создание заявки (без submit) сохраняет её в статусе `draft`. Редактирование полей до первой отправки допускается только инициатором и только в `draft` (и в `returned` после возврата — см. BR-06).  
**Связи:** FR-REQ-01, FR-REQ-02, UC-04

### BR-20 — Submit переводит в in_approval
Успешный submit из `draft` или повторный submit из `returned` переводит заявку в статус «На согласовании» (`status_id`), выставляет `current_stage_id` на первый live stage и создаёт `ApprovalTask` по live `StageAssignment` (BR-08 / BR-06; [ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md)).  
**Связи:** FR-REQ-03, UC-05, AC-APP-02, AC-APP-03

### BR-21 — Запрет самосогласования
Инициатор заявки не может выполнять approval-задачу по собственной заявке: действия approve / reject / return запрещены, даже если инициатор назначен на этап как согласующий (лично или через роль).  
**Связи:** FR-APP-03–05, UC-07–09, AC-ACC-03, ERR_FORBIDDEN_APPROVAL

### BR-25 — Обязательность комментария при reject и return
При `reject` и `return` комментарий **обязателен** (непустой текст). При `approve` комментарий **необязателен**.  
**Связи:** FR-APP-03–05, UC-07–09, AC-APP-04, AC-APP-06, AC-APP-07, ERR_VALIDATION

### BR-26 — Схема полей: актуальная (live) при edit и согласовании
1. При **редактировании** заявки в статусах `draft` и `returned` используется **актуальная** схема полей типа заявки.
2. При сохранении полей и при submit выполняется валидация по этой схеме; при несоответствии — ошибка валидации.
3. После successful submit согласующие читают текущие `RequestFieldValue`. Сущность **FieldValueVersion** **не** используется.
4. Маршрут — live: BR-08 / BR-09 / BR-22 ([ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md)).

**Связи:** FR-REQ-02, FR-REQ-03, FR-REQ-09, FR-CAT-03, UC-04, UC-05, AC-DRAFT-01, AC-DRAFT-02

### BR-28 — Свободные комментарии инициатора в in_approval
Инициатор может оставлять свободные комментарии к своей заявке в статусе `in_approval` (в дополнение к комментариям решений согласующих). Комментарии других сотрудников к чужим заявкам запрещены.  
**Связи:** FR-REQ-06, UC-06, AC-REQ-06

## 5. Правила конфигурации маршрута и каталога

### BR-08 — Submit использует live-маршрут
При успешной отправке заявка читает **актуальный** `ApprovalRoute` типа (этапы и назначения), получает `current_stage_id` и `ApprovalTask` для assignees. **RouteInstance не создаётся** ([ADR-LIVE-CFG-01](../03-diagrams/architecture/adr-live-config.md)).  
**Связи:** FR-REQ-03, AC-APP-10

### BR-09 — Изменение live-конфигурации и незавершённые заявки
Изменение live-конфигурации (тип, маршрут, этапы, назначения, ProcessTransition, схема полей) **может влиять** на ещё не завершённые заявки (snapshot нет).

**Ограничение админки:** нельзя удалять / деактивировать этап, на который есть open `ApprovalTask` или заявки in_approval с этим `current_stage_id`.

Версионирование процессов и snapshot — **out of scope**.  
**Связи:** FR-REQ-03, UC-05, AC-APP-10; ADR-LIVE-CFG-01

### BR-22 — Повторный submit: live-маршрут с первого этапа
При повторной отправке из `returned`: берётся актуальный live-маршрут; `current_stage_id` → первый этап; создаются новые `ApprovalTask`; FieldValueVersion **не** создаётся.  
**Связи:** FR-REQ-09, BR-06, BR-26, AC-APP-08, AC-DRAFT-02

### BR-10 — Неактивный тип скрыт в каталоге
Тип заявки с `active = false` не отображается в каталоге и недоступен для создания новой заявки. Уже созданные заявки продолжают обрабатываться (с учётом live config, BR-09).  
**Связи:** FR-CAT-01, FR-REQ-01, AC-CAT-01

---

## 6. Правила аудита

### BR-24 — История обязательна для значимых событий
По заявке фиксируется история как минимум для: создания; submit; решений approve/reject/return; перехода этапа; завершения маршрута; отмены; изменений полей при доработке (returned). Полный snapshot payload значений в HistoryEvent **не** обязателен.  
**Связи:** FR-AUDIT-01, FR-AUDIT-02, UC-14

---

## 7. Сводка ID (Baseline)

| ID | Кратко |
| :--- | :--- |
| BR-01 | Сотрудник видит только свои заявки |
| BR-02 | Маршрут последовательный |
| BR-03 | First-approve wins |
| BR-04 | Reject завершает заявку |
| BR-05 | Return → returned |
| BR-06 | После return — правка и повторный submit с первого этапа |
| BR-07 | Отмена только draft/returned |
| BR-08 | Submit читает live-маршрут; RouteInstance нет |
| BR-09 | Live config может влиять на in-flight; ограничение удаления этапов |
| BR-10 | Неактивный тип скрыт в каталоге |
| BR-12 | Нет оргструктурного auto-routing |
| BR-14 | Approver видит заявки со своими задачами |
| BR-15 | Действие только по своей открытой задаче |
| BR-16 | Одна роль на User (`role_id`); Admin может менять роль |
| BR-17 | Approve последнего этапа → approved |
| BR-18 | Валидация маршрута при активации и при submit |
| BR-19 | Создание → draft |
| BR-20 | Submit → in_approval + tasks первого live stage |
| BR-21 | Запрет самосогласования |
| BR-22 | Resubmit: live-маршрут с первого этапа; без FieldValueVersion |
| BR-24 | Минимальный набор audit-событий |
| BR-25 | Комментарий обязателен при reject/return; для approve нет |
| BR-26 | Edit и согласование — актуальная live-схема; без версий значений |
| BR-28 | Свободные комментарии инициатора в in_approval |

**Количество BR (Baseline): 24**  
Backlog BR: см. [docs/backlog.md](../backlog.md).

---

## 8. Согласованность с Vision & Scope

Проверка BR Baseline против Vision & Scope: **противоречий по ядру MVP не выявлено**. Scope не расширялся.

Замечание по нумерации UC: в Vision перечислены сценарии ядра (каталог…отмена и др.); детальные UC Baseline — см. [use-cases.md](./use-cases.md). Уточнение детализации, не конфликт scope.

---

## 9. Закрытые решения (бывшие Open Questions)

| Бывший OQ | Решение | Где зафиксировано |
| :--- | :--- | :--- |
| OQ-BR-01 | Самосогласование запрещено | BR-21 |
| OQ-BR-02 | Свободные комментарии инициатора в in_approval | BR-28 |
| OQ-BR-03 | Остальные задачи этапа → `cancelled` | BR-03 |
| OQ-FR-01 / OQ-AC-02 (бывш. OQ-UC) | Комментарий обязателен при reject/return; для approve нет | BR-25 |
| OQ-FR-02 | Схема: актуальная (live) при edit и согласовании; без FieldValueVersion | BR-26; ADR-LIVE-CFG-01 |
| OQ-FR-03 | Уведомление в одной транзакции с событием | BR-29; Target notifications |
| OQ-FR-04 | Валидация маршрута при активации и при submit | BR-18 |
| OQ-HOME-01 | После login — разделы по единственной роли пользователя | BR-16 |
| OQ-NFR-01 | JWT TTL = 8 часов | [ADR-AUTH-JWT-01](../03-diagrams/architecture/adr-jwt-core-api.md) |
| OQ-NFR-02 / OQ-ERR-01 / OQ-AC-01 | Чужой скрываемый ресурс → 404 | NFR-SEC-05 |
| OQ-NFR-03 | Perf baseline ≥ 1000 заявок / 5000 history | NFR-PERF-04 |
| OQ-NFR-04 | Password hash: bcrypt или эквивалент | [ADR-AUTH-JWT-01](../03-diagrams/architecture/adr-jwt-core-api.md) / ADR-SEC-01 |
| OQ-NFR-LOG | Retention техлогов = 14 дней | NFR-LOG-03 |
| OQ-RBAC-01 | Admin не создаёт заявки от сотрудника | [docs/backlog.md](../backlog.md) (admin) |
| OQ-RBAC-02 | Approver видит полную карточку по своей задаче | BR-14 |
| OQ-ERR-02 | Optimistic locking в админке не реализуется | error-matrix |
| OQ-ERR-03 | Пустой каталог → HTTP 200 + [] | FR-CAT-01 / error-matrix |
| HTTPS внешний стенд | Обязателен | NFR-SEC-06 |
| Multi-instance | Вне MVP | [docs/backlog.md](../backlog.md) (scalability) |
| Retention истории заявок | 60 дней в MVP | NFR-LOG-03 |
| Выбор активной роли | Не требуется; одна роль на User | BR-16 |
| OQ-A / OQ-B | Resubmit после return — с **первого** этапа (OQ-B); live-маршрут без RouteInstance | BR-06; ADR-LIVE-CFG-01 |

---

## 10. Оставшиеся Open Questions / TBD

Обязательных открытых вопросов по ядру MVP нет.

---

## 11. Трассировка (Baseline)

| BR | FR (основные) | UC | AC |
| :--- | :--- | :--- | :--- |
| BR-01 | FR-REQ-04 | UC-06 | AC-ACC-01 |
| BR-02 | FR-APP-06 | UC-07 | AC-APP-05 |
| BR-03 | FR-APP-03, FR-APP-06, FR-APP-07 | UC-07 | AC-APP-09 |
| BR-04 | FR-APP-04 | UC-08 | AC-APP-06 |
| BR-05 | FR-APP-05, FR-REQ-08 | UC-09 | AC-APP-07 |
| BR-06 | FR-REQ-09 | UC-05 | AC-APP-08 |
| BR-07 | FR-REQ-07 | UC-10 | AC-REQ-07 |
| BR-08 | FR-REQ-03 | UC-05 | AC-APP-10 |
| BR-09 | FR-REQ-03 | UC-05 | AC-APP-10, AC-APP-10b, AC-DRAFT-02 |
| BR-10 | FR-CAT-01 | UC-03 | AC-CAT-01 |
| BR-12 | FR-REQ-03; FR-ADMIN-05 — backlog | UC-05; UC-12 — backlog | AC-APP-02b |
| BR-14 | FR-APP-02, FR-REQ-04 | UC-07 | AC-ACC-06 |
| BR-15 | FR-APP-03–05 | UC-07–09 | AC-ACC-02 |
| BR-16 | см. backlog (AUTH FR) | — | — |
| BR-17 | FR-APP-07 | UC-07 | AC-APP-05b |
| BR-18 | FR-REQ-03 | UC-05 | AC-APP-02b |
| BR-19 | FR-REQ-01, FR-REQ-02 | UC-04 | AC-APP-01, AC-DRAFT-01 |
| BR-20 | FR-REQ-03 | UC-05 | AC-APP-02, AC-APP-03 |
| BR-21 | FR-APP-03–05 | UC-07–09 | AC-ACC-03 |
| BR-22 | FR-REQ-09 | UC-05 | AC-APP-08, AC-DRAFT-02 |
| BR-24 | FR-AUDIT-01, FR-AUDIT-02 | UC-14 | — |
| BR-25 | FR-APP-03–05 | UC-07–09 | AC-APP-04, AC-APP-06, AC-APP-07 |
| BR-26 | FR-REQ-02, FR-REQ-03 | UC-04, UC-05 | AC-DRAFT-01, AC-DRAFT-02 |
| BR-28 | FR-REQ-06 | UC-06 | AC-REQ-06 |

Backlog BR/FR/UC/AC — [docs/backlog.md](../backlog.md).
