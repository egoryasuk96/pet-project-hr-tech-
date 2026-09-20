import fs from "node:fs";

const original = fs.readFileSync("docs/_stage3-ac-original.md", "utf8").replace(/\r\n/g, "\n");
const map = JSON.parse(fs.readFileSync("docs/_stage3-id-map.json", "utf8"));
const baseline = new Set(
  Object.entries(map.AC)
    .filter(([, v]) => v.bucket === "Baseline")
    .map(([k]) => k)
);

const re = /^### (AC-[A-Z]+-\d+[a-z]?) — (.+)$/gm;
const matches = [...original.matchAll(re)];
const blocks = {};
for (let i = 0; i < matches.length; i++) {
  const id = matches[i][1];
  const start = matches[i].index;
  let end;
  if (i + 1 < matches.length) end = matches[i + 1].index;
  else {
    const n = original.indexOf("\n## 15. Сводка AC", start);
    end = n === -1 ? original.length : n;
  }
  let text = original.slice(start, end).trim();
  text = text.replace(/\n## [^\n]+\n*$/, "");
  blocks[id] = text + "\n";
}

function cleanRelated(line) {
  return line
    .replace(/FR-ADMIN-03[–-]05/g, "конфиг admin — [docs/backlog.md](../backlog.md)")
    .replace(/FR-ADMIN-03–04/g, "[docs/backlog.md](../backlog.md)")
    .replace(/FR-ADMIN-02/g, "схема admin — [docs/backlog.md](../backlog.md)")
    .replace(/FR-ADMIN-01/g, "[docs/backlog.md](../backlog.md)")
    .replace(/,\s*,/g, ", ")
    .replace(/:\s*,/g, ": ");
}

const sections = [
  { title: "1. Создание заявки", ids: ["AC-APP-01"] },
  { title: "2. Submit", ids: ["AC-APP-02", "AC-APP-02b"] },
  { title: "3. Создание задачи первого этапа", ids: ["AC-APP-03"] },
  { title: "4. Approve", ids: ["AC-APP-04", "AC-APP-04b"] },
  { title: "5. Переход на следующий этап и завершение маршрута", ids: ["AC-APP-05", "AC-APP-05b"] },
  { title: "6. Reject", ids: ["AC-APP-06", "AC-APP-06b"] },
  { title: "7. Return", ids: ["AC-APP-07", "AC-APP-07b"] },
  { title: "8. Повторный submit", ids: ["AC-APP-08"] },
  { title: "9. First-approve wins", ids: ["AC-APP-09"] },
  { title: "10. Snapshot маршрута", ids: ["AC-APP-10", "AC-APP-10b"] },
  { title: "11. Права доступа", ids: ["AC-ACC-01", "AC-ACC-02", "AC-ACC-03", "AC-ACC-06"] },
  { title: "12. Неактивный тип заявки и пустой каталог", ids: ["AC-CAT-01", "AC-CAT-01b", "AC-CAT-02"] },
  { title: "13. Отмена и комментарии", ids: ["AC-REQ-07", "AC-REQ-06"] },
  { title: "14. Схема полей", ids: ["AC-DRAFT-01", "AC-DRAFT-02"] },
];

const notifReplacements = [
  [
    "And согласующие первого этапа получают in-app уведомления",
    "And (опционально, backlog) согласующие первого этапа получают in-app уведомления",
  ],
  [
    "And согласующие этапа 2 получают уведомления",
    "And (опционально, backlog) согласующие этапа 2 получают уведомления",
  ],
  [
    "And инициатор получает уведомление о завершении",
    "And (опционально, backlog) инициатор получает уведомление о завершении",
  ],
  [
    "And инициатор получает уведомление\nAnd в истории есть reject",
    "And (опционально, backlog) инициатор получает уведомление\nAnd в истории есть reject",
  ],
  [
    "And открытые задачи этапа N закрыты\nAnd инициатор получает уведомление\nAnd инициатор может",
    "And открытые задачи этапа N закрыты\nAnd (опционально, backlog) инициатор получает уведомление\nAnd инициатор может",
  ],
];

let out = `# Acceptance Criteria

**Проект:** Employee Service  
**Документ:** Acceptance Criteria  
**ID:** DOC-AC  
**Версия:** 1.0  
**Статус:** Baseline v1.0

Формат преимущественно Given / When / Then. Каждый AC имеет ID и ссылки на FR/BR.  
MVP Baseline (этап 3). AC вне Baseline — [docs/backlog.md](../backlog.md).

> **AC-ACC** = Access (проверки контроля доступа / access control), не «account».

---

`;

for (const sec of sections) {
  out += `## ${sec.title}\n\n`;
  for (const id of sec.ids) {
    if (!blocks[id]) throw new Error("missing " + id);
    let block = blocks[id];
    block = block
      .split("\n")
      .map((l) => (l.includes("**Related:**") ? cleanRelated(l) : l))
      .join("\n");
    for (const [a, b] of notifReplacements) block = block.split(a).join(b);
    out += block.trim() + "\n\n---\n\n";
  }
}

const titles = {};
for (const [id, block] of Object.entries(blocks)) {
  const m = block.match(/^### (AC-\S+) — (.+)$/m);
  if (m) titles[id] = m[2].trim();
}

const sorted = [...baseline].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
out += `## 15. Сводка AC (Baseline)

| ID | Тема |
| :--- | :--- |
`;
for (const id of sorted) {
  out += `| ${id} | ${titles[id] || ""} |\n`;
}
out += `
**Количество AC (Baseline): 27**  
Backlog AC: см. [docs/backlog.md](../backlog.md).

---

## 16. Open Questions / TBD

**Обязательных открытых вопросов для Этапа 3 нет.**

---

## 17. Трассировка (Baseline)

| AC | FR | BR |
| :--- | :--- | :--- |
| AC-APP-01 | FR-REQ-01 | BR-19 |
| AC-APP-02 | FR-REQ-03 | BR-08, BR-20, BR-26 |
| AC-APP-03 | FR-REQ-03, FR-APP-01 | BR-20 |
| AC-APP-04 | FR-APP-03 | BR-15, BR-25 |
| AC-APP-05 | FR-APP-06 | BR-02 |
| AC-APP-05b | FR-APP-07 | BR-17 |
| AC-APP-06 | FR-APP-04 | BR-04, BR-25 |
| AC-APP-07 | FR-APP-05 | BR-05, BR-25 |
| AC-APP-08 | FR-REQ-09 | BR-06, BR-22, BR-26 |
| AC-APP-09 | FR-APP-03 | BR-03 |
| AC-APP-10 | FR-REQ-03 | BR-08, BR-09 |
| AC-ACC-01 | FR-REQ-04 | BR-01 |
| AC-ACC-02 | FR-APP-03–05 | BR-15 |
| AC-ACC-03 | FR-APP-03–05 | BR-21 |
| AC-ACC-06 | FR-APP-02 | BR-14 |
| AC-CAT-01 | FR-CAT-01, FR-REQ-01 | BR-10 |
| AC-CAT-02 | FR-CAT-01 | — |
| AC-REQ-06 | FR-REQ-06 | BR-28 |
| AC-REQ-07 | FR-REQ-07 | BR-07 |
| AC-DRAFT-01 | FR-REQ-02, FR-REQ-03 | BR-26 |
| AC-DRAFT-02 | FR-REQ-03, FR-REQ-09 | BR-26, BR-22 |

Backlog AC — [docs/backlog.md](../backlog.md).
`;

fs.writeFileSync("docs/02-requirements/acceptance-criteria.md", out.replace(/\n/g, "\r\n"));
const headers = [...out.matchAll(/^## .+$/gm)].map((m) => m[0]);
console.log("headers", headers.length);
console.log(headers.join("\n"));
console.log("baseline", baseline.size, "extracted", Object.keys(blocks).length);
