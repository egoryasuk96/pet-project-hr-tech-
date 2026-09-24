# ADR — Configurable actions (ProcessTransition)

**Продукт:** Employee Service  
**ID:** ADR-ACTION-01  
**Версия:** 1.0  
**Статус:** Accepted (Target-active; Frozen Target API)  
**Связанные документы:** [ADR-LIVE-CFG-01](./adr-live-config.md), [ERD Domain Model](../erd/erd-domain-model.md), [Business Rules](../../02-requirements/business-rules.md)

---

## Контекст

Сейчас переходы статусов и кнопки (submit / cancel / approve / return / reject) зашиты в Python и частично в узких REST-путях. Нужна конфигурируемая модель для Admin UI и единый execute без отдельного BPM-движка.

---

## Решение

### Справочники

- **Process**, **Status**, **Action** — `id`, `code`, `name`, `description`, `active`. UI показывает `name`.
- **ProcessTransition** (live): `process_id`, `from_status_id`, `action_id`, `to_status_id`, `role_id`, `effect`, `is_active`, `sort_order`.

### Effects

| effect | Поведение |
| :--- | :--- |
| `status_only` | Смена `request.status_id` на `to_status_id` (submit, cancel, reject, return и т.п.). Submit дополнительно создаёт `ApprovalTask` по первому live stage. |
| `approve_advance` | См. ниже |

### approve_advance (live stage)

1. Проверить, что transition разрешён (process, from_status, role, active).
2. Проверить open `ApprovalTask` текущего пользователя: `task.stage_id == request.current_stage_id`, не self-approve.
3. Завершить задачу (first-approve → sibling open tasks этапа → cancelled).
4. Если есть следующий live `ApprovalStage` по `sequence_no` — установить `current_stage_id`, создать tasks по live `StageAssignment`; статус обычно остаётся «На согласовании».
5. Если этап последний — `status_id = to_status_id` (например «Согласовано»), `current_stage_id = null`.

Маршрут (`ApprovalRoute` / stages / assignments) остаётся отдельной live-конфигурацией **кто** согласует; transitions задают **какие** действия и **куда** ведёт статус.

### API (целевой контракт)

- Discovery: `GET /requests/{request_id}/available-actions`.
- Execute: `POST /requests/{request_id}/actions/{action_id}` с повторной серверной проверкой (Action Engine).
- Frontend не решает набор кнопок сам по статусу.
- Legacy aliases `POST .../submit` и `POST .../cancel` — deprecated thin wrappers; primary mutation — Action Engine.

Не вводится: workflow engine, условные ветвления, event bus.

---

## Последствия

| + | − |
| :--- | :--- |
| Admin может настраивать матрицу действий | Нужен seed/матрица по умолчанию |
| Один endpoint execute | Breaking change относительно `/submit`, `/approve` и т.д. |
| Согласовано с live config | Правки transitions влияют на in-flight (ADR-LIVE-CFG-01) |

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-23 | Принята модель ProcessTransition + effects |
| 1.1 | 2026-09-24 | available-actions GET; Target-active; legacy aliases note |
