# UML-SEQ-03 — Sequence: админ-конфигурация типа и маршрута

**Продукт:** Employee Service  
**ID:** UML-SEQ-03  
**Версия:** 1.1  
**Статус:** Future  
**Связанные документы:** [uml-description.md](./uml-description.md), [Backlog](../../backlog.md), [ADR-LIVE-CFG-01](../architecture/adr-live-config.md)

---

## 1. Назначение

> **Статус Future:** admin-конфигурация вне MVP Baseline. Полные требования — [docs/backlog.md](../../backlog.md). Файл сохранён для будущего развития, не удалять.

Взаимодействия администратора и системы при настройке типа заявки, полей, последовательного маршрута, этапов, назначений и ProcessTransition; активация / деактивация.

**Осознанное ограничение:** изменение live-конфигурации **может затронуть** ещё не завершённые заявки ([ADR-LIVE-CFG-01](../architecture/adr-live-config.md)). Рекомендуемое правило: не удалять этап, на который есть open tasks или заявки в `in_approval` с этим `current_stage_id` (BR-09). Admin **не** создаёт заявки от имени сотрудника (BR-27).

---

## 2. Участники (lifelines)

| Lifeline | Смысл |
| :--- | :--- |
| **Администратор** | Роль `admin` |
| **Система** | Граница Employee Service |
| **In-flight заявка** | Справочный объект: заявка в `in_approval` (не участник UI) |

### 2.1. Логические области ответственности (не архитектура)

Имена **Validation**, **ConfigStore**, **InFlightGuard** (проверка BR-09), **Audit** — логические роли анализа.

---

## 3. Основные сценарии

### 3.1. Настройка конфигурации

1. Проверка роли `admin` (ACL-04 — backlog).
2. CRUD типа, полей, маршрута, этапов (BR-02), назначений (BR-12), ProcessTransition.
3. Сохранение **live** — без snapshot-фиксации.

### 3.2. Активация типа

1. Validation маршрута: ≥1 этап; у каждого ≥1 назначение (BR-18).
2. Успех → тип активен; иначе ERR_ROUTE_CONFIG.

### 3.3. Деактивация

1. `is_active = false` → тип скрыт в каталоге (BR-10).
2. In-flight заявки продолжают согласование по **текущему** live-маршруту (маршрут мог измениться с момента submit).

### 3.4. Связь с runtime

| Ситуация | Поведение |
| :--- | :--- |
| Admin меняет маршрут после submit заявки R | R при следующем approve/resubmit читает **актуальный** live-маршрут; caveat ADR-LIVE-CFG-01 |
| Новая заявка после смены маршрута | Submit берёт актуальный live-маршрут |
| Admin меняет схему полей | Edit draft/returned видит актуальную схему (BR-26) |
| Admin удаляет этап с open tasks | Должно блокироваться (BR-09) |

---

## 4. Sequence: конфиг, активация, in-flight caveat (Mermaid)

```mermaid
sequenceDiagram
  actor Admin as Администратор
  participant Sys as Система
  participant Req as In-flight заявка
  Note over Sys: Логические области: Validation,<br/>ConfigStore, InFlightGuard, Audit
  Note over Req: in_approval; current_stage_id → live stage

  Admin->>Sys: Открыть конфигурацию типов / маршрутов
  Sys->>Sys: Validation: роль admin
  alt Не admin
    Sys-->>Admin: ERR_FORBIDDEN
  else OK
    Admin->>Sys: Сохранить тип / поля / этапы / назначения / transitions
    Sys->>Sys: ConfigStore: персистенция live config
    Sys->>Sys: InFlightGuard: предупреждение/блок опасных правок (BR-09)
    Note over Req: может быть затронута при следующем runtime-шаге (ADR-LIVE-CFG-01)
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
    Note over Req: in-flight продолжают (BR-10)
    Sys-->>Admin: тип скрыт из каталога
  end
```

---

## 5. Трассировка

| Тип | ID |
| :--- | :--- |
| **UC** | UC-11, UC-12 |
| **FR** | FR-ADMIN-01…06 |
| **BR** | BR-02, BR-09, BR-10, BR-12, BR-18, BR-26, BR-27 |
| **AC** | AC-ADMIN-01, AC-APP-10, AC-APP-10b, AC-CAT-01, AC-CAT-01b, AC-DRAFT-01, AC-ACC-04 |
| **RBAC/ACL** | ACL-04, ACL-09 — backlog |
| **BPMN** | BPMN-03 |

---

## 6. Границы

- Runtime submit/approval — UML-SEQ-01 / UML-SEQ-02.
- Snapshot isolation **не** применяется; см. ADR-LIVE-CFG-01.

---

## История изменений

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-19 | Первая версия |
| 1.1 | 2026-09-23 | Live config caveat; без SnapshotIsolation |
