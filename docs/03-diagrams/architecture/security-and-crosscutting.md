# ARCH-SEC — Безопасность и сквозные аспекты

**Продукт:** Employee Service  
**ID:** ARCH-SEC  
**Версия:** 1.2  
**Статус:** Target architecture (Frozen Target)  
**Связанные документы:** [architecture-description.md](./architecture-description.md), [ADR-AUTH-JWT-01](./adr-jwt-core-api.md), [ADR-AUTH-DEMO-01](./adr-demo-role-header.md) (Superseded), [ADR-UI-01](./adr-static-web-client.md)

---

## 1. Назначение

Свести на архитектурном уровне AuthN/AuthZ, ошибки, логирование, аудит, уведомления, производительность и масштабируемость — с разделением **CURRENT/TARGET runtime**, **LEGACY/HISTORICAL** и **Future / backlog**.

---

## 2. Аутентификация (AuthN)

### 2.1. CURRENT / TARGET runtime

| Тема | Источник |
| :--- | :--- |
| Login/password → JWT access token (`POST /auth/login`) | FR-AUTH-01; [ADR-AUTH-JWT-01](./adr-jwt-core-api.md) |
| Защищённые запросы: `Authorization: Bearer <access_token>` | NFR-SEC-01 |
| Пользователь определяется из JWT `sub` → User | FR-AUTH-02 (`GET /me`) |
| RBAC через одну `User.role_id` (`employee` \| `approver` \| `admin`) | BR-16; ADR-ORG-01 |
| Access token TTL = 8 часов | NFR-SEC-04 |
| Refresh tokens **отсутствуют** | NFR-SEC-04 |
| Password только как bcrypt hash | NFR-SEC-03; ADR-SEC-01 |
| Невалидный/просроченный JWT → 401 | NFR-SEC-01 |
| Demo-header **не** AuthN | ADR-AUTH-DEMO-01 Superseded |

### 2.2. HISTORICAL — demo-header stub (не CURRENT)

| Тема | Источник |
| :--- | :--- |
| AuthN отсутствовал; роль — HTTP-заголовок + Role Select | [ADR-AUTH-DEMO-01](./adr-demo-role-header.md) — **Superseded** |

### 2.3. ADR / предположения MVP

| ID | Решение | Статус |
| :--- | :--- | :--- |
| **ADR-SEC-01** | Алгоритм хеша пароля — **bcrypt** (допустим argon2 по NFR-SEC-03) | Target-active |
| **ADR-AUTH-JWT-01** | JWT Bearer Core API + static UI (`sessionStorage`) | Accepted |
| **ADR-AUTH-DEMO-01** | Демо-роль через заголовок | **Superseded** |
| **ADR-SEC-02** | ~~SPA хранит access JWT…~~ | **Superseded** (React SPA); JWT на static клиенте — ADR-AUTH-JWT-01 |
| **ADR-SEC-03** | Проверка JWT на каждом защищённом запросе; без server-side session store | **Target-active** via ADR-AUTH-JWT-01 (дух NFR-SCL-01) |

#### Исходный текст ADR-SEC-02 (Superseded — React SPA)

> SPA хранит access JWT на клиенте и передаёт в заголовке Authorization. Способ хранения (localStorage / sessionStorage / memory) **не** зафиксирован в ранних версиях архитектуры.

#### Исходный текст ADR-SEC-03 (ранняя формулировка)

> Проверка JWT на каждом защищённом запросе в Auth Module; без server-side session store. Следует духу NFR-SCL-01; детали middleware — ADR.

**Примечание:** в раннем Baseline ADR-SEC-02/03 временно считались superseded в пользу demo-header. Для Frozen Target JWT-проверка снова CURRENT; React SPA storage — по-прежнему Historical.

---

## 3. Авторизация (AuthZ / RBAC)

### 3.1. Требования

| Тема | Источник |
| :--- | :--- |
| Роли + ownership | BR-01, BR-14, BR-15, BR-16, BR-21; AC-ACC-*; FR-AUTH-03 |
| Employee — только свои заявки | BR-01 |
| Approver — полная карточка / actions по своим задачам | BR-14, BR-15 |
| Несколько ролей = union permissions | **Legacy**; Target — одна роль (BR-16, ADR-ORG-01) |
| Запрет самосогласования | BR-21 → `FORBIDDEN_APPROVAL` |
| Admin — все заявки / не создаёт за сотрудников | BR-13, BR-27 — Future / backlog (Admin UI) |
| Скрываемый чужой ресурс → **404** `NOT_FOUND` | NFR-SEC-05 |
| Нарушение прав на действие → **403** | NFR-SEC-02, error-matrix |

### 3.2. Архитектурное размещение

- **Authorization Module** — единая точка authoritative проверок (**ADR-CMP-04**).
- FE может скрывать пункты меню по ролям (UX); обход UI не даёт прав.
- Self-approval проверяется **до** мутаций Action / Approval Engine.

---

## 4. Обработка ошибок

### 4.1. Требования

| Тема | Источник |
| :--- | :--- |
| Единые коды error-matrix | error-matrix (требования) |
| Пользовательские сообщения на русском; без stack trace клиенту | NFR-USB-02, NFR-USB-03 |
| Internal → rollback + tech log | error-matrix / NFR-REL |

### 4.2. ADR

| ID | Решение |
| :--- | :--- |
| **ADR-ERR-01** | HTTP Layer централизованно маппит доменные ошибки → HTTP status + код error-matrix |
| **ADR-ERR-02** | Валидационные отказы выполняются **до** записи TX |
| **ADR-ERR-03** | Target JSON envelope `{ error: { code, message, details } }` — [adr-error-envelope.md](./adr-error-envelope.md) |

Ключевые Target-коды (`error.code`): `VALIDATION`, `FORBIDDEN_APPROVAL`, `TASK_DONE`, `REQUEST_ACTION_NOT_ALLOWED`, `INVALID_STATE`, `ROUTE_CONFIG`, `NOT_FOUND`, `UNAUTHORIZED`.

**Legacy / Pre-E2 (HISTORICAL):** плоский envelope с `ERR_*` — не Target.

---

## 5. Аудит и технические логи

### 5.1. Требования

| Тема | Источник |
| :--- | :--- |
| Прикладная история заявки (actor, time, action, from/to, comment) | BR-24, FR-AUDIT-*, NFR-LOG-02 |
| API tech log: method, path, status, latency, request_id, user_id; без паролей/токенов | NFR-LOG-01 |
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
| Только in-app | BR-11 | Target |
| Минимальный набор событий | BR-23 | Target |
| Создание в **одной транзакции** с бизнес-событием; failure → rollback | BR-29 | Target |
| List / mark as read | FR-NOTIF-02/03 | Target API + UI |

### 6.2. Архитектура

- **Notification Module** — Target: создаётся в TX Action Engine / submit; UI список уведомлений.
- Нет message broker / email gateway в MVP (out of scope).
- **ADR-NOTIF-01:** MVP использует pull (список при открытии / refresh UI) без WebSocket и без нового NFR.

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
- Stateless JWT (без refresh / без server session) снимает sticky-session ограничения (NFR-SCL-01).
- Индексы/кэш — решения реализации/ERD; в Architecture фиксируется готовность модели конфига к NFR-SCL-02.

---

## 8. Надёжность live config и идемпотентность

| Тема | Источник | Архитектура |
| :--- | :--- | :--- |
| Live route + tasks согласованы (`current_stage_id` / `ApprovalTask.stage_id`) | NFR-REL-03, BR-08/09/22 | Action / Approval Engine; Admin Config с ограничением BR-09 |
| Повтор action по завершённой задаче | NFR-REL-02 | Action Engine: без повторной мутации; ошибка |

Snapshot isolation **не** Target ([ADR-LIVE-CFG-01](./adr-live-config.md); ADR-SNAP-01 Superseded).

---

## 9. Поставка и секреты

| Тема | Источник |
| :--- | :--- |
| Локальный запуск и облачный деплой | NFR-DEP-01, NFR-AVL-01 — Python + Neon/local PG; Render + Neon; runtime: FastAPI + статика + PostgreSQL ([ADR-UI-01](./adr-static-web-client.md)) |
| Seed пользователи/типы | NFR-DEP-02 |
| Secrets через env (`DATABASE_URL`, `JWT_SECRET`, опционально `DEMO_PASSWORD`) | NFR-DEP-03 |
| HTTPS на внешнем демо | NFR-SEC-06 |

Cloud/K8s не проектируются.

---

## 10. Трассировка

| Область | FR / BR / NFR / ADR |
| :--- | :--- |
| AuthN Target | ADR-AUTH-JWT-01, FR-AUTH-01/02, NFR-SEC-01/03/04 |
| AuthN Historical | ADR-AUTH-DEMO-01 Superseded |
| AuthZ | BR-01/14–16/21, NFR-SEC-02/05, ACL-*, AC-ACC-* |
| Errors | error-matrix, NFR-USB-02; ADR-ERR-* |
| Audit/logs | BR-24, FR-AUDIT-*, NFR-LOG-01…03, NFR-REL-01 |
| Notifications | FR-NOTIF-*, BR-11/23/29 — Target |
| Perf/scale | NFR-PERF-*, NFR-SCL-* |
| Deploy | NFR-DEP-*, NFR-AVL-*, NFR-SEC-06 |
| UI | ADR-UI-01 |

---

## 11. Границы

- Не вводятся 2FA, SSO, refresh token, email/push.
- Не создаются новые коды ошибок.
- ADR помечены явно и не маскируются под FR/BR/NFR.
- NFR-DEP-01 задан в NFR; здесь только архитектурное отражение.

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.1 | 2026-09-20 | Baseline: demo-header AuthN |
| 1.2 | 2026-09-24 | JWT CURRENT; demo Historical; Notification Target; §8 live config |
