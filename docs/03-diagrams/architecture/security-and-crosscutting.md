# ARCH-SEC — Безопасность и сквозные аспекты

**Продукт:** Employee Service  
**ID:** ARCH-SEC  
**Версия:** 1.1  
**Статус:** Baseline v1.0  
**Связанные документы:** [architecture-description.md](./architecture-description.md), [ADR-AUTH-DEMO-01](./adr-demo-role-header.md), [ADR-UI-01](./adr-static-web-client.md), [Backlog](../../backlog.md)

---

## 1. Назначение

Свести на архитектурном уровне AuthN/AuthZ, ошибки, логирование, аудит, уведомления, производительность и масштабируемость — с разделением **требований Vision / Baseline**, **Baseline runtime** и **ADR / предположений MVP**.

---

## 2. Аутентификация (AuthN)

### 2.1. Baseline runtime

| Тема | Источник |
| :--- | :--- |
| Настоящий AuthN отсутствует; роль (и при необходимости user id) — HTTP-заголовок | Vision §12 п.7; [ADR-AUTH-DEMO-01](./adr-demo-role-header.md) |
| Экран выбора роли | ADR-AUTH-DEMO-01; [ADR-UI-01](./adr-static-web-client.md) |
| AuthZ опирается на заголовок + seed RBAC | BR-01, BR-14, BR-15, BR-21; AC-ACC-* |

### 2.2. Полная auth (backlog) — требования сохранены в backlog

| Тема | Источник |
| :--- | :--- |
| Login/password → JWT | FR-AUTH-01, NFR-SEC-01 ([backlog](../../backlog.md)) |
| Current user | FR-AUTH-02 |
| Access token TTL = 8 часов | NFR-SEC-04 |
| Refresh tokens **отсутствуют** в MVP полной auth | NFR-SEC-04 |
| Password только как безопасный hash; bcrypt **или** эквивалент | NFR-SEC-03 |
| Невалидный/просроченный JWT → 401 | NFR-SEC-01 |

### 2.3. ADR / предположения MVP

| ID | Решение | Статус |
| :--- | :--- | :--- |
| **ADR-SEC-01** | Для полной auth выбирается **bcrypt** как конкретный алгоритм (допустим и argon2 по NFR-SEC-03) | Остаётся для backlog auth; **не** новый NFR |
| **ADR-SEC-02** | ~~SPA хранит access JWT на клиенте и передаёт в заголовке Authorization~~ | **Статус: Superseded** для Baseline → [ADR-AUTH-DEMO-01](./adr-demo-role-header.md). Полный JWT на клиенте — backlog |
| **ADR-SEC-03** | ~~Проверка JWT на каждом защищённом запросе в Auth Module; без server-side session store~~ | **Статус: Superseded** для Baseline → Auth Module валидирует демо-заголовок (ADR-AUTH-DEMO-01). Полный JWT middleware возвращается с backlog auth; дух «без server-side session» сохраняется (NFR-SCL-01) |
| **ADR-AUTH-DEMO-01** | Демо-роль через заголовок + экран выбора роли | Baseline |

#### Исходный текст ADR-SEC-02 (Superseded)

> SPA хранит access JWT на клиенте и передаёт в заголовке Authorization. Способ хранения (localStorage / sessionStorage / memory) **не** зафиксирован в ранних версиях архитектуры.

#### Исходный текст ADR-SEC-03 (Superseded для Baseline)

> Проверка JWT на каждом защищённом запросе в Auth Module; без server-side session store. Следует духу NFR-SCL-01; детали middleware — ADR.

---

## 3. Авторизация (AuthZ / RBAC)

### 3.1. Требования

| Тема | Источник |
| :--- | :--- |
| Роли + ownership | BR-01, BR-14, BR-15, BR-16, BR-21; AC-ACC-*; (FR-AUTH-03 / полный JWT AuthN — backlog) |
| Employee — только свои заявки | BR-01 |
| Approver — полная карточка по своим задачам | BR-14 |
| Действия только по своей open задаче | BR-15 |
| Несколько ролей = union permissions | BR-16 |
| Запрет самосогласования | BR-21 → `ERR_FORBIDDEN_APPROVAL` |
| Admin — все заявки / не создаёт за сотрудников | BR-13, BR-27 — Future / backlog |
| Скрываемый чужой ресурс → **404** `ERR_NOT_FOUND` | NFR-SEC-05 |
| Нарушение прав на действие (в т.ч. чужая задача) → **403** | NFR-SEC-02, error-matrix |

### 3.2. Архитектурное размещение

- **Authorization Module** — единая точка authoritative проверок (**ADR-CMP-04**).
- FE может скрывать пункты меню по ролям (UX); обход UI не даёт прав.
- Self-approval проверяется **до** мутаций Approval Engine.

---

## 4. Обработка ошибок

### 4.1. Требования

| Тема | Источник |
| :--- | :--- |
| Единые коды error-matrix | error-matrix (требования) |
| Пользовательские сообщения на русском; без stack trace клиенту | NFR-USB-02, NFR-USB-03 |
| `ERR_INTERNAL` → rollback + tech log | error-matrix / практика надёжности NFR-REL |

### 4.2. ADR

| ID | Решение |
| :--- | :--- |
| **ADR-ERR-01** | HTTP Layer централизованно маппит доменные ошибки → HTTP status + код error-matrix |
| **ADR-ERR-02** | Валидационные отказы (пустой комментарий reject/return, schema) выполняются **до** записи TX, статус без изменений (как в UML-SEQ / AC) |

Ключевые коды для согласования (без изменения матрицы): `ERR_VALIDATION`, `ERR_FORBIDDEN_APPROVAL`, `ERR_TASK_DONE`, `ERR_DUP_ACTION`, `ERR_INVALID_STATE`, `ERR_ROUTE_CONFIG`, `ERR_NOT_FOUND`, `ERR_UNAUTHORIZED`.

---

## 5. Аудит и технические логи

### 5.1. Требования

| Тема | Источник |
| :--- | :--- |
| Прикладная история заявки (actor, time, action, from/to, comment) | BR-24, FR-AUDIT-*, NFR-LOG-02 |
| API tech log: method, path, status, latency, request_id, user_id; без паролей/токенов / секретов заголовка | NFR-LOG-01 |
| Retention tech logs 14 дней; history 60 дней | NFR-LOG-03 |
| Целостность: статус/задачи/история атомарно | NFR-REL-01 |

### 5.2. Архитектура

- **Audit Module** пишет HistoryEvent в той же TX, что бизнес-событие ([data-flows.md](./data-flows.md)).
- **HTTP Layer** пишет tech logs (**ADR-LOG-01**: структурированный лог с request_id).
- Политика cleanup/retention — требование NFR-LOG-03; механизм очистки — этап реализации, не Architecture.

---

## 6. Уведомления

### 6.1. Требования

| Тема | Источник | Scope |
| :--- | :--- | :--- |
| Только in-app | BR-11 | Backlog |
| Минимальный набор событий | BR-23 | Backlog |
| Создание в **одной транзакции** с бизнес-событием; failure → rollback | BR-29, AC-NOTIF-01 | Backlog |
| List / mark as read | FR-NOTIF-02/03 | Backlog |

### 6.2. Архитектура

- **Notification Module** — Future / [backlog](../../backlog.md); в Baseline TX шаги Notification опциональны «если в scope» ([data-flows.md](./data-flows.md)).
- Нет message broker / email gateway в MVP (out of scope).
- **ADR-NOTIF-01** (когда модуль вернётся): MVP использует pull (список при открытии / периодический refresh UI) без WebSocket и без нового NFR.

---

## 7. Производительность и масштабируемость

### 7.1. Требования

| Тема | Источник |
| :--- | :--- |
| Read p95 ≤ 500 ms; write p95 ≤ 1000 ms @ ≤20 users | NFR-PERF-01/02 |
| Pagination default 20 / max 100 | NFR-PERF-03 |
| Baseline ≥1000 requests / ≥5000 history | NFR-PERF-04 |
| Multi-instance **не** в MVP; API без server-side session store | NFR-SCL-01 |
| ≥50 типов; ≥10 этапов на маршрут | NFR-SCL-02 |

### 7.2. Архитектурные следствия (без новых NFR)

- Один монолит + одна БД достаточны для заявленных объёмов MVP.
- Отсутствие server-side session (демо-заголовок сейчас; JWT в backlog) снимает sticky-session ограничения (NFR-SCL-01).
- Индексы/кэш — решения реализации/ERD позже; в Architecture фиксируется только готовность модели конфига к NFR-SCL-02.

---

## 8. Надёжность snapshot и идемпотентность

| Тема | Источник | Архитектура |
| :--- | :--- | :--- |
| RouteInstance неизменяем прикладными операциями после первого submit | NFR-REL-03, BR-08/09/22 | Snapshot Module; Admin Config (Future) не пишет в RouteInstance заявок |
| Повтор approve/reject/return по завершённой задаче | NFR-REL-02 | Approval Engine: без повторной мутации; ошибка |

---

## 9. Поставка и секреты

| Тема | Источник |
| :--- | :--- |
| Локальный запуск и облачный деплой | NFR-DEP-01, NFR-AVL-01 — Python + Neon/local PG локально; Render + Neon в облаке; runtime: FastAPI + статика + PostgreSQL ([ADR-UI-01](./adr-static-web-client.md)) |
| Seed пользователи/типы | NFR-DEP-02 |
| Secrets через env (DB URL; JWT secret — при полной auth) | NFR-DEP-03 |
| HTTPS на внешнем демо | NFR-SEC-06 |

Cloud/K8s не проектируются.

---

## 10. Трассировка

| Область | FR / BR / NFR / ADR |
| :--- | :--- |
| AuthN Baseline | ADR-AUTH-DEMO-01, Vision §12 п.7 |
| AuthN backlog | FR-AUTH-01/02, NFR-SEC-01/03/04 |
| AuthZ | BR-01/14–16/21, NFR-SEC-02/05, ACL-*, AC-ACC-* |
| Errors | error-matrix, NFR-USB-02; ADR-ERR-* |
| Audit/logs | BR-24, FR-AUDIT-*, NFR-LOG-01…03, NFR-REL-01 |
| Notifications | FR-NOTIF-*, BR-11/23/29 — backlog |
| Perf/scale | NFR-PERF-*, NFR-SCL-* |
| Deploy | NFR-DEP-*, NFR-AVL-*, NFR-SEC-06 |
| UI | ADR-UI-01 |

---

## 11. Границы

- Не вводятся 2FA, SSO, refresh token, email/push.
- Не создаются новые коды ошибок.
- ADR помечены явно и не маскируются под FR/BR/NFR.
- NFR-DEP-01 задан в NFR; здесь только архитектурное отражение.
