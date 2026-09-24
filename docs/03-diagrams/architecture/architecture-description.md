# Архитектура Employee Service (логико-техническая модель)

**Продукт:** Employee Service  
**ID:** ARCH-00  
**Версия:** 1.4  
**Статус:** Target architecture (Frozen Target)  
**Связанные документы:** [BPMN](../bpmn/bpmn-description.md), [UML](../uml/uml-description.md), [ADR-LIVE-CFG-01](./adr-live-config.md), [ADR-ACTION-01](./adr-configurable-actions.md), [ADR-AUTH-JWT-01](./adr-jwt-core-api.md), [ADR-UI-01](./adr-static-web-client.md), [Vision](../../01-vision-and-scope/vision-scope.md)

---

## 1. Назначение

Документ фиксирует **логическую и техническую архитектуру** MVP Employee Service на уровне системного аналитика: границы системы, контейнеры (веб-клиент / backend / database), логические компоненты, потоки данных, зоны ответственности, место ключевых бизнес-правил, безопасность, ошибки, аудит, ограничения масштабируемости и производительности.

Новые бизнес-правила **не вводятся** этим индексом. Архитектура **реализует** процессы (BPMN) и аналитические взаимодействия (UML), не заменяя их.

---

## 2. Соглашения

| Тема | Правило |
| :--- | :--- |
| **Формат** | Markdown = source of truth; визуал — Mermaid |
| **Язык** | Русский |
| **Трассировка** | Ссылки на UC / FR / BR / AC / NFR / RBAC |
| **Требование vs ADR** | Зафиксированное в Vision / требованиях — требование; иное — **ADR / предположение MVP** |
| **Логические модули** | Разбиение монолита, не микросервисы |
| **Live config** | [ADR-LIVE-CFG-01](./adr-live-config.md); snapshot deprecated |
| **Auth** | JWT Bearer ([ADR-AUTH-JWT-01](./adr-jwt-core-api.md)); demo-header Superseded |

### 2.1. ADR

| Метка | Смысл |
| :--- | :--- |
| **Требование** | Vision / FR / BR / NFR / AC / RBAC / BPMN / UML |
| **ADR (MVP)** | Архитектурное решение; **не** новый FR/BR/NFR |
| **Superseded** | Решение сохранено в тексте, не действует для Target; ссылка на замену |

Отдельные ADR Target:

- [ADR-LIVE-CFG-01](./adr-live-config.md) — live config; supersedes ADR-SNAP-01;
- [ADR-ACTION-01](./adr-configurable-actions.md) — ProcessTransition, Action Engine;
- [ADR-ORG-01](./adr-org-model.md) — Company/Department/Employee; one `role_id`;
- [ADR-ID-01](./adr-id-strategy.md) — User UUID; business entities integer PK;
- [ADR-ERR-03](./adr-error-envelope.md) — Target error envelope (`error.{code,message,details}`);
- [ADR-ERR-01](./security-and-crosscutting.md) / [ADR-ERR-02](./security-and-crosscutting.md) — HTTP mapping и validation-before-TX (не envelope);
- [ADR-AUTH-JWT-01](./adr-jwt-core-api.md) — JWT Core API (Accepted);
- [ADR-UI-01](./adr-static-web-client.md) — static HTML+JS от FastAPI.

**Superseded / HISTORICAL:**

- [ADR-AUTH-DEMO-01](./adr-demo-role-header.md) — demo-header stub → JWT;
- [ADR-SNAP-01](./adr-snapshot-submit-versions.md) — snapshot → live config;
- ADR-CNT-03, ADR-SEC-02 (React SPA JWT storage).

---

## 3. Архитектурный стиль (ADR)

**Выбор:** модульный монолит — один backend + лёгкий веб-клиент (HTML/JS) + одна БД.

**Обоснование:** один bounded context; атомарность status + tasks + history + notifications; объём MVP; стек PostgreSQL + FastAPI + статика (Vision §12).

---

## 4. Список артефактов

| ID | Файл | Кратко |
| :--- | :--- | :--- |
| ARCH-00 | [architecture-description.md](./architecture-description.md) | Индекс, соглашения, DoD |
| ARCH-CTX | [context-diagram.md](./context-diagram.md) | Граница системы и актёры |
| ARCH-CNT | [container-diagram.md](./container-diagram.md) | Web static / API / DB |
| ARCH-CMP | [component-diagram.md](./component-diagram.md) | Логические модули и UI-зоны |
| ARCH-FLOW | [data-flows.md](./data-flows.md) | Потоки submit / actions / admin |
| ARCH-SEC | [security-and-crosscutting.md](./security-and-crosscutting.md) | JWT, AuthZ, ошибки, логи, NFR |
| ARCH-MAP | [architecture-traceability.md](./architecture-traceability.md) | Трассировка |
| ADR-LIVE-CFG-01 | [adr-live-config.md](./adr-live-config.md) | Live config |
| ADR-ACTION-01 | [adr-configurable-actions.md](./adr-configurable-actions.md) | Action Engine |
| ADR-AUTH-JWT-01 | [adr-jwt-core-api.md](./adr-jwt-core-api.md) | JWT Bearer |
| ADR-SNAP-01 | [adr-snapshot-submit-versions.md](./adr-snapshot-submit-versions.md) | **Superseded** |
| ADR-AUTH-DEMO-01 | [adr-demo-role-header.md](./adr-demo-role-header.md) | **Superseded** |
| ADR-UI-01 | [adr-static-web-client.md](./adr-static-web-client.md) | Static HTML+JS клиент |

---

## 5. Сводка: критичные правила → владелец

| Правило | Источник | Владелец |
| :--- | :--- | :--- |
| Submit читает live route | BR-08; [ADR-LIVE-CFG-01](./adr-live-config.md) | Action Engine + Submit Orchestrator |
| approve_advance по live stages | BR-02, BR-17; ADR-ACTION-01 | Action Engine + Approval Engine |
| First-approve wins | BR-03 | Approval Engine |
| Запрет самосогласования | BR-21 | Authorization + Action Engine |
| Комментарий обязателен reject/return | BR-25 | Action Engine |
| RBAC / ownership | BR-01, BR-14–16 | Authorization Module |
| История | BR-24 | Audit Module |
| available-actions / execute | ADR-ACTION-01 | Action Engine |

---

## 6. Границы

Микросервисы / cloud сверх NFR — вне этого индекса. Новые FR/BR/NFR этим файлом не вводятся. Поставка — NFR-DEP-01 (Python + Neon/local PG; Render + Neon). OpenAPI Frozen Target — `docs/04-api`.

---

## 7. DoD

1. Каталог содержит ARCH-00…ARCH-MAP и ADR Target (включая ADR-UI-01, ADR-AUTH-JWT-01, ADR-LIVE-CFG-01, ADR-ACTION-01).
2. Context / container / component описаны под static HTML+JS + **JWT Bearer**.
3. Монолит обоснован; решения вне требований помечены ADR; demo-header и snapshot ADR — **Superseded**.
4. Live config — ADR-LIVE-CFG-01; Snapshot Module удалён из target; primary mutation — Action Engine.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия Architecture |
| 1.1 | 2026-09-20 | ADR-SNAP-01 / ADR-AUTH-DEMO-01; вариант B |
| 1.2 | 2026-09-20 | ADR-UI-01; выравнивание под Vision §12 (static UI, demo header) |
| 1.3 | 2026-09-23 | Live config; Action Engine; ADR-LIVE-CFG-01 supersedes SNAP |
| 1.4 | 2026-09-24 | Frozen Target sync: JWT CURRENT; demo/snapshot Historical; DoD |
