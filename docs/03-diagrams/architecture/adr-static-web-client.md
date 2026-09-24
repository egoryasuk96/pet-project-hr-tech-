# ADR — Лёгкий веб-клиент: статические HTML + JavaScript

**Продукт:** Employee Service  
**ID:** ADR-UI-01  
**Версия:** 1.1  
**Статус:** Accepted (UI Stage 6.2)  
**Связанные документы:** [architecture-description.md](./architecture-description.md), [ADR-AUTH-JWT-01](./adr-jwt-core-api.md), [ADR-AUTH-DEMO-01](./adr-demo-role-header.md), [Vision & Scope](../../01-vision-and-scope/vision-scope.md) §12 п.7–8, [Backlog](../../backlog.md)

---

## Контекст

Ранее в ранних версиях архитектуры предполагался отдельный **React + TypeScript SPA** как deployable Web-контейнер с login UI и хранением JWT на клиенте (ADR-CNT-03, ADR-SEC-02, ADR-CMP-02 в части SPA). Vision §12 зафиксировал иной контур: портфолио без React/SPA; ранняя формулировка «без настоящей аутентификации» — **HISTORICAL** (заменена JWT, ADR-AUTH-JWT-01).

Нужно явно заменить UI-стек, сохранив историю прежних ADR как **Superseded**.

---

## Решение

1. Решение «React + TypeScript SPA как отдельный Web-контейнер» **superseded**.
2. UI = **статические HTML-страницы + JavaScript**, которые **отдаёт тот же FastAPI**-приложение (один deployable-процесс: REST API + раздача статики / static mount). Отдельный React-контейнер **не** используется.
3. Страницы отдаются как `GET /login`, `GET /my-requests`, `GET /requests/{id}`, `GET /notifications` (+ последующие экраны по мере срезов); статика — `/static/...`.
4. **Auth UI:** login/JWT по [ADR-AUTH-JWT-01](./adr-jwt-core-api.md) (`POST /auth/login`, Bearer, `sessionStorage`). Demo-header ([ADR-AUTH-DEMO-01](./adr-demo-role-header.md)) **не** используется клиентом.
5. **Реализованный FE-срез:** Login, My Requests, Request Detail (available-actions / execute), Notifications. **Не** реализованы: Create UI, Admin UI, полноценная Approver Queue, профиль (Cabinet).

Источники: Vision §12 п.6–8; ADR-AUTH-JWT-01.

---

## Последствия

| + | − |
| :--- | :--- |
| Согласованность с Vision и минимальный стек портфолио | Нет богатого SPA-роутинга / component tree React |
| Один процесс FastAPI упрощает Compose/демо | Многостраничный HTML без SPA-роутера |
| Экраны ядра проверяемы без отдельного FE build | ADR-CNT-03 / ADR-SEC-02 / SPA-часть ADR-CMP-02 помечены Superseded |

---

## Что остаётся в backlog / следующих срезах

- Create Request UI;
- полноценная Approver Queue UI (отдельный список задач);
- Admin UI, профиль (Cabinet);
- при необходимости — более развитый клиент (не обязательно React; решение отдельно).

Уже в Target FE-срезе: Login, My Requests, Request Detail (+ available-actions / execute), Notifications.

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-20 | Baseline UI: static HTML+JS от FastAPI; React SPA superseded |
| 1.1 | 2026-09-23 | JWT login UI вместо demo-header; маршруты /login, /my-requests |
| 1.2 | 2026-09-24 | FE-срез: Detail + Notifications; Create/Admin/Queue — Future |
