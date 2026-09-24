# ADR — Организационная модель

**Продукт:** Employee Service  
**ID:** ADR-ORG-01  
**Версия:** 1.0  
**Статус:** Accepted (целевая модель; реализация — последующие этапы)  
**Связанные документы:** [Vision](../../01-vision-and-scope/vision-scope.md), [ERD Domain Model](../erd/erd-domain-model.md), [ADR-ID-01](./adr-id-strategy.md)

---

## Контекст

В Baseline у `User` были строковые `department` / `position` без сущностей Employee/Department. Для production-like портфолио нужна явная оргструктура без авто-routing по руководителю (по-прежнему out of scope).

---

## Решение

```text
Company
  └── Department
        └── Employee
              └── User (учётная запись)
```

- **Employee:** `employee_number`, ФИО, `department_id`, `manager_employee_id`, `position`, `active`.
- **User:** связь с Employee; **одна** системная роль (`role_id` → Role). M:N `UserRole` в целевой модели не используется.
- Назначения на этапы маршрута — явные (role и/или user), **не** через `manager_employee_id`.
- Одна Company в демо (не мультитенантность).

---

## Последствия

- Профиль и UI берут ФИО/отдел с Employee.
- Admin может менять роль пользователя.
- Автоопределение руководителя по оргструктуре остаётся **out of scope**.

---

## История

| Версия | Дата | Описание |
| :--- | :--- | :--- |
| 1.0 | 2026-09-23 | Company → Department → Employee → User; одна роль |
