# UML-SEQ-03 — Sequence: админ-конфигурация типа и маршрута

**Продукт:** Employee Service  
**ID:** UML-SEQ-03  
**Версия:** 1.0  
**Статус:** Future  
**Связанные документы:** [uml-description.md](./uml-description.md), [Backlog](../../backlog.md)

---

## 1. Назначение

> **Статус Future:** admin-конфигурация вне MVP Baseline. Полные требования — [docs/backlog.md](../../backlog.md). Файл сохранён для будущего развития, не удалять.

Взаимодействия администратора и системы при настройке типа заявки, полей, последовательного маршрута, этапов и назначений; активация / деактивация.

Зафиксированы изоляция **RouteInstance** уже отправленных заявок (BR-09) и валидация маршрута при активации (BR-18). Admin **не** создаёт заявки от имени сотрудника (BR-27).

---

## 2. Участники (lifelines)

| Lifeline | Смысл |
| :--- | :--- |
| **Администратор** | Роль `admin` |
| **Система** | Граница Employee Service |
| **Запущенная заявка** | Справочный объект анализа: уже отправленная заявка со своим route snapshot (не участник UI) |

### 2.1. Логические области ответственности (не архитектура)

Имена **Validation**, **ConfigStore** (сохранение конфигурации), **SnapshotIsolation** (следствие BR-09), **Audit** — **логические роли / области ответственности на уровне анализа**.

Они **не** микросервисы, **не** компоненты архитектуры и **не** API.

---

## 3. Основные сценарии

### 3.1. Настройка конфигурации

1. Проверка роли `admin` (ACL-04).
2. CRUD типа, полей формы, маршрута, этапов (последовательный порядок — BR-02), явных назначений роль/пользователь (BR-12).
3. Опционально: справочники (FR-ADMIN-06).
4. Сохранение не ретроактивно для route snapshot уже отправленных заявок (BR-09).

### 3.2. Активация типа

1. Запрос `is_active = true`.
2. Validation маршрута: ≥1 этап; у каждого этапа ≥1 назначение (BR-18).
3. Успех → тип активен; иначе ERR_ROUTE_CONFIG / ERR_VALIDATION, тип остаётся неактивным (AC-ADMIN-01).

### 3.3. Деактивация

1. `is_active = false` → тип скрыт в каталоге (BR-10).
2. Уже созданные / отправленные заявки продолжают согласование по своим snapshot.

### 3.4. Связь с runtime (без новых правил)

| Ситуация | Поведение |
| :--- | :--- |
| Admin меняет маршрут после submit заявки R | R продолжает по своему route snapshot (AC-APP-10) |
| Новая заявка после смены маршрута | Первый submit берёт **актуальный** маршрут (AC-APP-10b) |
| Admin меняет схему полей | Edit draft/returned видит актуальную схему (BR-26); in-flight после submit — зафиксированные данные (AC-DRAFT-02) |

---

## 4. Sequence: конфиг, активация, изоляция (Mermaid)

```mermaid
sequenceDiagram
  actor Admin as Администратор
  participant Sys as Система
  participant Req as Запущенная заявка
  Note over Sys: Логические области анализа<br/>(не сервисы/API): Validation,<br/>ConfigStore, SnapshotIsolation, Audit
  Note over Req: Уже есть route snapshot<br/>(создан при первом submit)

  Admin->>Sys: Открыть конфигурацию типов / маршрутов
  Sys->>Sys: Validation: роль admin
  alt Не admin
    Sys-->>Admin: ERR_FORBIDDEN
  else OK
    Admin->>Sys: Сохранить тип / поля / этапы / назначения
    Sys->>Sys: ConfigStore: персистенция конфигурации
    Sys->>Sys: SnapshotIsolation: не менять route snapshot Req (BR-09)
    Note over Req: согласование без изменений маршрута
    Sys-->>Admin: конфигурация сохранена

    Admin->>Sys: Активировать тип (is_active = true)
    Sys->>Sys: Validation: маршрут валиден (BR-18)
    alt Маршрут невалиден
      Sys-->>Admin: ERR_ROUTE_CONFIG; тип неактивен
    else OK
      Sys->>Sys: is_active = true
      Sys-->>Admin: тип активен в каталоге
    end

    Admin->>Sys: Деактивировать тип
    Sys->>Sys: is_active = false
    Sys->>Sys: SnapshotIsolation: in-flight заявки продолжают (BR-10)
    Sys-->>Admin: тип скрыт из каталога
  end
```

---

## 5. Трассировка

| Тип | ID |
| :--- | :--- |
| **UC** | UC-11, UC-12 |
| **FR** | FR-ADMIN-01, FR-ADMIN-02, FR-ADMIN-03, FR-ADMIN-04, FR-ADMIN-05; FR-ADMIN-06 (кратко) |
| **BR** | BR-02, BR-08, BR-09, BR-10, BR-12, BR-18, BR-26, BR-27 |
| **AC** | AC-ADMIN-01, AC-APP-10, AC-APP-10b, AC-CAT-01, AC-CAT-01b, AC-DRAFT-01, AC-ACC-04 |
| **RBAC/ACL** | ACL-04, ACL-09 |
| **BPMN** | BPMN-03 |

---

## 6. Границы

- Реестр заявок и история admin (UC-15) — на Use Case; отдельный sequence не требуется.
- Runtime submit/approval — UML-SEQ-01 / UML-SEQ-02.
- ERD и API **не** моделируются.
- Новые правила не вводятся.
