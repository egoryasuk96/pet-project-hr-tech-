# ARCH-CTX — Context Diagram (граница системы)

**Продукт:** Employee Service  
**ID:** ARCH-CTX  
**Версия:** 1.2  
**Статус:** Target architecture (Frozen Target)  
**Связанные документы:** [architecture-description.md](./architecture-description.md), [Vision](../../01-vision-and-scope/vision-scope.md), [ADR-AUTH-JWT-01](./adr-jwt-core-api.md), [ADR-UI-01](./adr-static-web-client.md)

---

## 1. Назначение

Показать границу MVP Employee Service, актёров и отсутствие внешних runtime-зависимостей, уже исключённых Vision / требованиями.

---

## 2. Система и актёры

| Участник | Тип | Смысл | Scope |
| :--- | :--- | :--- | :--- |
| **Employee Service** | Система | Каталог, заявки, согласование (Action Engine), история, in-app уведомления; UI — static HTML/JS | Target |
| **Сотрудник** (`employee`) | Актёр | Инициатор заявок, мои заявки, карточка | Target |
| **Согласующий** (`approver`) | Актёр | Действия по заявке через available-actions / execute | Target |
| **Администратор** (`admin`) | Актёр | Конфигурация процессов/маршрутов, роли пользователей, реестр | Target (docs); Admin UI — Future |

У каждого пользователя **одна** системная роль (`role_id`, BR-16 / [ADR-ORG-01](./adr-org-model.md)). Auth Target: JWT ([ADR-AUTH-JWT-01](./adr-jwt-core-api.md)).

**Legacy:** union нескольких ролей; demo-header без login (ADR-AUTH-DEMO-01 — Superseded).

---

## 3. Внешние системы

**В MVP runtime-интеграций нет** (требование / out of scope Vision):

| Не используется | Основание |
| :--- | :--- |
| SSO / AD / LDAP | Out of scope |
| Email / push | BR-11 — только in-app |
| Внешний BPM (Camunda и аналоги) | Out of scope; встроенный Approval / Action Engine |
| Оргструктура / auto-routing руководителя | BR-12, out of scope |
| HRIS / payroll | Out of scope |

OpenAPI — артефакт документации (контракт API), не внешняя runtime-система.

---

## 4. Диаграмма (Mermaid)

```mermaid
flowchart TB
  Emp[Сотрудник employee]
  Apr[Согласующий approver]
  Adm[Администратор admin]

  subgraph ES["Employee Service (граница Target)"]
    Core[Каталог / Заявки / Action Engine / История / Notifications]
  end

  Emp -->|использует| Core
  Apr -->|использует| Core
  Adm -.->|Admin UI Future| Core

  NoteOut[Внешние runtime-системы отсутствуют в MVP]
  Core -.->|нет интеграций| NoteOut
```

---

## 5. Что внутри границы (обзор)

**CURRENT / TARGET:**

1. Auth: login/password → JWT access token; Bearer на защищённых запросах ([ADR-AUTH-JWT-01](./adr-jwt-core-api.md)). Refresh token нет. Demo-header — Legacy.
2. Лёгкий веб-клиент: static HTML+JS от FastAPI ([ADR-UI-01](./adr-static-web-client.md)).
3. Каталог активных типов и схемы (FR-CAT-*).
4. Жизненный цикл заявки по live-маршруту и ProcessTransition (FR-REQ-*, BR-08/22/26; [ADR-LIVE-CFG-01](./adr-live-config.md)).
5. Согласование через Action Engine: `GET .../available-actions` + `POST .../actions/{action_id}` ([ADR-ACTION-01](./adr-configurable-actions.md)).
6. История решений и статусов на карточке (FR-AUDIT-*, BR-24).
7. In-app уведомления (API + UI список).

**Future / backlog** (Vision §7.1): Admin UI, профиль (Cabinet), Create UI / полноценная Approver Queue как отдельные экраны.

Детализация контейнеров — [container-diagram.md](./container-diagram.md).

---

## 6. Трассировка

| Тип | ID |
| :--- | :--- |
| **UC** | UC ядра + login; UC-02/11–12/15 — backlog UI |
| **FR** | CAT / REQ / APP / AUDIT / AUTH / NOTIF (Target); CAB / ADMIN — backlog |
| **BR** | BR ядра; BR-12/13/27 — по scope / backlog admin |
| **Vision** | Scope §6, Out of scope §7, §12 |
| **UML** | UML-UC-01 |

---

## 7. Границы

- Не показываются HTTP-эндпоинты и таблицы БД.
- Не добавляются внешние системы «на будущее».
- Новые актёры и роли не вводятся.

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.1 | 2026-09-20 | Baseline context |
| 1.2 | 2026-09-24 | JWT Target; demo-header Legacy; Action Engine в границе |
