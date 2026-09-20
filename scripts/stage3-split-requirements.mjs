/**
 * Stage 3: split MVP Baseline requirements from backlog.
 * Asserts inventory: UC=15, FR=38, BR=29, AC=32, NFR=29 (total 143).
 */
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1")), "..");
const DOCS = path.join(ROOT, "docs");
const REQ = path.join(DOCS, "02-requirements");
const REASONS = JSON.parse(fs.readFileSync(path.join(DOCS, "_stage3-reasons.json"), "utf8"));

const BASELINE = {
  UC: new Set(["UC-03", "UC-04", "UC-05", "UC-06", "UC-07", "UC-08", "UC-09", "UC-10", "UC-14"]),
  FR: new Set([
    "FR-CAB-02",
    "FR-CAT-01", "FR-CAT-02", "FR-CAT-03",
    "FR-REQ-01", "FR-REQ-02", "FR-REQ-03", "FR-REQ-04", "FR-REQ-05", "FR-REQ-06", "FR-REQ-07", "FR-REQ-08", "FR-REQ-09",
    "FR-APP-01", "FR-APP-02", "FR-APP-03", "FR-APP-04", "FR-APP-05", "FR-APP-06", "FR-APP-07",
    "FR-AUDIT-01", "FR-AUDIT-02",
  ]),
  BR: new Set([
    "BR-01", "BR-02", "BR-03", "BR-04", "BR-05", "BR-06", "BR-07", "BR-08", "BR-09", "BR-10",
    "BR-12", "BR-14", "BR-15", "BR-16", "BR-17", "BR-18", "BR-19", "BR-20", "BR-21", "BR-22",
    "BR-24", "BR-25", "BR-26", "BR-28",
  ]),
  AC: new Set([
    "AC-APP-01", "AC-APP-02", "AC-APP-02b", "AC-APP-03", "AC-APP-04", "AC-APP-04b",
    "AC-APP-05", "AC-APP-05b", "AC-APP-06", "AC-APP-06b", "AC-APP-07", "AC-APP-07b",
    "AC-APP-08", "AC-APP-09", "AC-APP-10", "AC-APP-10b",
    "AC-ACC-01", "AC-ACC-02", "AC-ACC-03", "AC-ACC-06",
    "AC-CAT-01", "AC-CAT-01b", "AC-CAT-02",
    "AC-REQ-06", "AC-REQ-07",
    "AC-DRAFT-01", "AC-DRAFT-02",
  ]),
  NFR: new Set([
    "NFR-PERF-01", "NFR-PERF-02", "NFR-PERF-03", "NFR-PERF-04",
    "NFR-AVL-01", "NFR-AVL-02",
    "NFR-SEC-02", "NFR-SEC-05", "NFR-SEC-06",
    "NFR-REL-01", "NFR-REL-02", "NFR-REL-03",
    "NFR-MNT-01", "NFR-MNT-02", "NFR-MNT-03",
    "NFR-SCL-02",
    "NFR-LOG-01", "NFR-LOG-02", "NFR-LOG-03",
    "NFR-USB-01", "NFR-USB-02", "NFR-USB-03",
    "NFR-DEP-01", "NFR-DEP-02", "NFR-DEP-03",
  ]),
};

const ALL_EXPECTED = { UC: 15, FR: 38, BR: 29, AC: 32, NFR: 29 };

function read(p) {
  return fs.readFileSync(p, "utf8").replace(/\r\n/g, "\n");
}

function write(p, content) {
  fs.writeFileSync(p, content.replace(/\n/g, "\r\n"), "utf8");
}

/** Extract UC blocks: ## UC-XX — Title ... until next ## UC- or ## Сводка / ##  */
function extractUcBlocks(md) {
  const blocks = {};
  const re = /^## (UC-\d+) — (.+)$/gm;
  const matches = [...md.matchAll(re)];
  for (let i = 0; i < matches.length; i++) {
    const id = matches[i][1];
    const start = matches[i].index;
    const end = i + 1 < matches.length ? matches[i + 1].index : md.search(/\n## Сводка\n/);
    blocks[id] = md.slice(start, end === -1 ? undefined : end).trim() + "\n";
  }
  return blocks;
}

/** Extract FR blocks: ### FR-XXX-NN — Title */
function extractFrBlocks(md) {
  const blocks = {};
  const re = /^### (FR-[A-Z]+-\d+) — (.+)$/gm;
  const matches = [...md.matchAll(re)];
  for (let i = 0; i < matches.length; i++) {
    const id = matches[i][1];
    const start = matches[i].index;
    let end;
    if (i + 1 < matches.length) end = matches[i + 1].index;
    else {
      const nextSec = md.indexOf("\n## 9. Сводка", start);
      end = nextSec === -1 ? md.length : nextSec;
    }
    // include trailing --- if present
    let text = md.slice(start, end).trimEnd();
    if (!text.endsWith("---")) {
      // keep as-is; sections may not have ---
    }
    blocks[id] = text.trim() + "\n";
  }
  return blocks;
}

/** Extract BR blocks: ### BR-XX — Title */
function extractBrBlocks(md) {
  const blocks = {};
  const re = /^### (BR-\d+) — (.+)$/gm;
  const matches = [...md.matchAll(re)];
  for (let i = 0; i < matches.length; i++) {
    const id = matches[i][1];
    const start = matches[i].index;
    const end = i + 1 < matches.length ? matches[i + 1].index : md.search(/\n## 7\. Сводка ID\n/);
    blocks[id] = md.slice(start, end === -1 ? undefined : end).trim() + "\n";
  }
  return blocks;
}

/** Extract AC blocks: ### AC-XXX — Title */
function extractAcBlocks(md) {
  const blocks = {};
  const re = /^### (AC-[A-Z]+-\d+[a-z]?) — (.+)$/gm;
  const matches = [...md.matchAll(re)];
  for (let i = 0; i < matches.length; i++) {
    const id = matches[i][1];
    const start = matches[i].index;
    let end;
    if (i + 1 < matches.length) end = matches[i + 1].index;
    else {
      const nextSec = md.indexOf("\n## 15. Сводка AC", start);
      end = nextSec === -1 ? md.length : nextSec;
    }
    blocks[id] = md.slice(start, end).trim() + "\n";
  }
  return blocks;
}

/** Extract NFR blocks: ### NFR-XXX-NN — Title */
function extractNfrBlocks(md) {
  const blocks = {};
  const re = /^### (NFR-[A-Z]+-\d+) — (.+)$/gm;
  const matches = [...md.matchAll(re)];
  for (let i = 0; i < matches.length; i++) {
    const id = matches[i][1];
    const start = matches[i].index;
    let end;
    if (i + 1 < matches.length) end = matches[i + 1].index;
    else {
      const nextSec = md.indexOf("\n## 11. Open Questions", start);
      end = nextSec === -1 ? md.length : nextSec;
    }
    blocks[id] = md.slice(start, end).trim() + "\n";
  }
  return blocks;
}

function classify(type, id) {
  return BASELINE[type].has(id) ? "Baseline" : "backlog";
}

function reason(type, id) {
  return REASONS[type]?.[id] || "(no reason in _stage3-reasons.json)";
}

/** Expand compact ID refs like FR-ADMIN-03–05, AC-ACC-*, BR-13–16 */
function expandToken(token) {
  // Already a full ID
  if (/^(UC|FR|BR|AC|NFR)-[A-Z0-9]+-\d+[a-z]?$/.test(token) || /^(UC|BR)-\d+$/.test(token)) {
    return [token];
  }
  // FR-ADMIN-03–05 or FR-APP-03–05 (en-dash or hyphen)
  let m = token.match(/^(FR|AC|NFR)-([A-Z]+)-(\d+)[–-](\d+)$/);
  if (m) {
    const [, kind, area, a, b] = m;
    const out = [];
    for (let i = +a; i <= +b; i++) out.push(`${kind}-${area}-${String(i).padStart(2, "0")}`);
    return out;
  }
  m = token.match(/^(BR)-(\d+)[–-](\d+)$/);
  if (m) {
    const out = [];
    for (let i = +m[2]; i <= +m[3]; i++) out.push(`BR-${String(i).padStart(2, "0")}`);
    return out;
  }
  // Wildcard FR-ADMIN-*, AC-ACC-*, AC-APP-*
  m = token.match(/^(FR|AC|NFR)-([A-Z]+)-\*$/);
  if (m) {
    const prefix = `${m[1]}-${m[2]}-`;
    const pool = Object.keys(REASONS[m[1]] || {}).filter((id) => id.startsWith(prefix));
    return pool.length ? pool : [token];
  }
  return [token];
}

const ID_TOKEN_RE =
  /\b((?:UC|BR)-\d+|(?:FR|AC|NFR)-[A-Z]+-\d+[a-z]?|(?:FR|AC|NFR)-[A-Z]+-\d+[–-]\d+|(?:BR)-\d+[–-]\d+|(?:FR|AC|NFR)-[A-Z]+-\*)\b/g;

function isBacklogId(id) {
  if (id.startsWith("UC-")) return !BASELINE.UC.has(id);
  if (id.startsWith("FR-")) return !BASELINE.FR.has(id);
  if (id.startsWith("BR-")) return !BASELINE.BR.has(id);
  if (id.startsWith("AC-")) return !BASELINE.AC.has(id);
  if (id.startsWith("NFR-")) return !BASELINE.NFR.has(id);
  return false;
}

function cleanRelatedLine(line) {
  // Only process Related / Связи cells
  if (!/\*\*(Related|Связи)/.test(line) && !line.includes("| **Related") && !line.includes("| **Связи")) {
    // Also handle table rows that are pure related content in BR "Связи:"
    if (!line.includes("**Связи:**") && !line.startsWith("**Related:**") && !line.startsWith("**Связи:**") === false) {
      if (!line.includes("Связи:")) return line;
    }
  }

  const backlogLink = "[docs/backlog.md](../backlog.md)";
  let touched = false;
  const cleaned = line.replace(ID_TOKEN_RE, (tok) => {
    const expanded = expandToken(tok);
    const allBacklog = expanded.every((id) => isBacklogId(id) || id.includes("*"));
    const anyBacklog = expanded.some((id) => isBacklogId(id));
    if (tok.includes("*")) {
      // FR-ADMIN-*, AC-ACC-* — if prefix is mixed, keep baseline-only mention + backlog link
      const expandedIds = expandToken(tok);
      const base = expandedIds.filter((id) => !isBacklogId(id));
      const back = expandedIds.filter((id) => isBacklogId(id));
      if (back.length && base.length === 0) {
        touched = true;
        return `см. ${backlogLink}`;
      }
      if (back.length) {
        touched = true;
        return `${base.join(", ")} (+ backlog: ${backlogLink})`;
      }
      return tok;
    }
    if (allBacklog && expanded.length >= 1 && expanded.every((id) => /^[A-Z]/.test(id))) {
      touched = true;
      return `см. ${backlogLink}`;
    }
    if (anyBacklog && expanded.length > 1) {
      const keep = expanded.filter((id) => !isBacklogId(id));
      touched = true;
      return keep.length ? `${keep.join(", ")} (+ backlog: ${backlogLink})` : `см. ${backlogLink}`;
    }
    if (anyBacklog) {
      touched = true;
      return `см. ${backlogLink}`;
    }
    return tok;
  });

  // Collapse duplicate backlog links / messy commas
  let out = cleaned
    .replace(/,\s*,+/g, ", ")
    .replace(/;\s*;+/g, "; ")
    .replace(/см\. \[docs\/backlog\.md\]\(\.\.\/backlog\.md\)(,\s*см\. \[docs\/backlog\.md\]\(\.\.\/backlog\.md\))+/g, "см. [docs/backlog.md](../backlog.md)")
    .replace(/\(\+ backlog: \[docs\/backlog\.md\]\(\.\.\/backlog\.md\)\)(,\s*\(\+ backlog: \[docs\/backlog\.md\]\(\.\.\/backlog\.md\)\))*/g, "(+ backlog: [docs/backlog.md](../backlog.md))")
    .replace(/,\s*\|\s*$/, " |")
    .replace(/:\s*,\s*/g, ": ")
    .replace(/,\s*$/, "");

  return out;
}

function cleanBlockReferences(block, opts = {}) {
  const { isBr01 = false } = opts;
  let text = block;

  if (isBr01) {
    // Remove admin/BR-13 exception sentence
    text = text.replace(
      /\n\*\*Исключение:\*\* пользователь с ролью `admin` видит все заявки в реестре \(см\. BR-13\)\.\s*\n/,
      "\n"
    );
  }

  // Clean related lines line-by-line
  text = text
    .split("\n")
    .map((line) => {
      if (
        line.includes("**Related FR**") ||
        line.includes("**Related BR**") ||
        line.includes("**Related:**") ||
        line.includes("**Связи**") ||
        line.includes("**Связи:**") ||
        /^\*\*Связи:\*\*/.test(line.trim())
      ) {
        return cleanRelatedLine(line);
      }
      // Also strip backlog IDs from body of baseline UC/FR where they appear as Related only —
      // leave body references that are narrative; task says Related/Связи/trace tables.
      return line;
    })
    .join("\n");

  return text;
}

function cleanTraceTable(md) {
  const lines = md.split("\n");
  const out = [];
  for (const line of lines) {
    if (!line.trim().startsWith("|")) {
      out.push(line);
      continue;
    }
    // Skip header/separator
    if (/^\|\s*:?-{3}/.test(line) || line.includes("| :---")) {
      out.push(line);
      continue;
    }
    // Detect if first cell is an ID that is backlog → drop row
    const firstCell = line.split("|")[1]?.trim() || "";
    const idMatch = firstCell.match(/^(UC|FR|BR|AC|NFR)-[A-Z0-9]+-?\d*[a-z]?/);
    if (idMatch) {
      const raw = firstCell.split(/\s|\.|…|,/)[0];
      // Handle FR-ADMIN-01…05 style
      if (raw.includes("ADMIN") || raw.startsWith("FR-AUTH") || raw.startsWith("FR-NOTIF") ||
          raw.startsWith("FR-CAB-01") || raw === "FR-CAB-01" ||
          (raw.startsWith("UC-") && isBacklogId(raw)) ||
          (raw.startsWith("BR-") && isBacklogId(raw)) ||
          (raw.startsWith("AC-") && isBacklogId(raw)) ||
          (raw.startsWith("NFR-") && isBacklogId(raw)) ||
          (raw.startsWith("FR-") && isBacklogId(raw.split("…")[0].replace(/–.*/, "")))) {
        // More precise: check known backlog prefixes in first cell
        const checkId = raw.replace(/…\d+$/, "").replace(/–\d+$/, "").replace(/\.\.\.\d+$/, "");
        if (
          checkId.startsWith("FR-ADMIN") ||
          checkId.startsWith("FR-AUTH") ||
          checkId.startsWith("FR-NOTIF") ||
          checkId === "FR-CAB-01" ||
          checkId === "FR-CAB-03" ||
          isBacklogId(checkId)
        ) {
          continue; // drop backlog row
        }
      }
    }
    // Clean backlog tokens inside the row
    let cleaned = line.replace(ID_TOKEN_RE, (tok) => {
      const expanded = expandToken(tok);
      if (expanded.every((id) => isBacklogId(id))) return "см. backlog.md";
      if (expanded.some((id) => isBacklogId(id))) {
        return expanded.filter((id) => !isBacklogId(id)).join(", ") || "см. backlog.md";
      }
      return tok;
    });
    // Drop rows whose first ID cell became empty-ish
    out.push(cleaned);
  }
  return out.join("\n");
}

function scanBacklogTokens(text, label) {
  const found = new Set();
  for (const m of text.matchAll(ID_TOKEN_RE)) {
    const expanded = expandToken(m[1]);
    for (const id of expanded) {
      if (isBacklogId(id)) found.add(id);
    }
  }
  return [...found].sort();
}

// --- Load sources ---
const ucMd = read(path.join(REQ, "use-cases.md"));
const frMd = read(path.join(REQ, "functional-requirements.md"));
const brMd = read(path.join(REQ, "business-rules.md"));
const acMd = read(path.join(REQ, "acceptance-criteria.md"));
const nfrMd = read(path.join(REQ, "non-functional-requirements.md"));

const ucBlocks = extractUcBlocks(ucMd);
const frBlocks = extractFrBlocks(frMd);
const brBlocks = extractBrBlocks(brMd);
const acBlocks = extractAcBlocks(acMd);
const nfrBlocks = extractNfrBlocks(nfrMd);

const counts = {
  UC: Object.keys(ucBlocks).length,
  FR: Object.keys(frBlocks).length,
  BR: Object.keys(brBlocks).length,
  AC: Object.keys(acBlocks).length,
  NFR: Object.keys(nfrBlocks).length,
};

for (const [k, v] of Object.entries(ALL_EXPECTED)) {
  if (counts[k] !== v) {
    console.error(`COUNT MISMATCH ${k}: got ${counts[k]}, expected ${v}`);
    console.error(`IDs: ${Object.keys({ UC: ucBlocks, FR: frBlocks, BR: brBlocks, AC: acBlocks, NFR: nfrBlocks }[k === "UC" ? "UC" : k === "FR" ? "FR" : k === "BR" ? "BR" : k === "AC" ? "AC" : "NFR"]).sort().join(", ")}`);
    process.exit(1);
  }
}

const total = Object.values(counts).reduce((a, b) => a + b, 0);
if (total !== 143) {
  console.error(`TOTAL MISMATCH: ${total} !== 143`);
  process.exit(1);
}

// Verify all IDs classified
const idMap = { UC: {}, FR: {}, BR: {}, AC: {}, NFR: {}, counts: {}, inventory: { ...counts, total: 143 } };
for (const [type, blocks] of [
  ["UC", ucBlocks],
  ["FR", frBlocks],
  ["BR", brBlocks],
  ["AC", acBlocks],
  ["NFR", nfrBlocks],
]) {
  let base = 0,
    back = 0;
  for (const id of Object.keys(blocks).sort(naturalIdSort)) {
    const bucket = classify(type, id);
    if (bucket === "Baseline") base++;
    else back++;
    idMap[type][id] = { bucket: bucket === "Baseline" ? "Baseline" : "backlog", reason: reason(type, id) };
  }
  idMap.counts[type] = { Baseline: base, backlog: back, total: base + back };
}

function naturalIdSort(a, b) {
  const pa = a.match(/^(UC|BR|FR|AC|NFR)-(?:([A-Z]+)-)?(\d+)([a-z])?$/);
  const pb = b.match(/^(UC|BR|FR|AC|NFR)-(?:([A-Z]+)-)?(\d+)([a-z])?$/);
  if (!pa || !pb) return a.localeCompare(b);
  if (pa[1] !== pb[1]) return pa[1].localeCompare(pb[1]);
  const areaA = pa[2] || "";
  const areaB = pb[2] || "";
  if (areaA !== areaB) return areaA.localeCompare(areaB);
  const n = +pa[3] - +pb[3];
  if (n !== 0) return n;
  return (pa[4] || "").localeCompare(pb[4] || "");
}

// Expected baseline/backlog counts from user
const EXPECT_BASE = { UC: 9, FR: 22, BR: 24, AC: 27, NFR: 25 };
const EXPECT_BACK = { UC: 6, FR: 16, BR: 5, AC: 5, NFR: 4 };
for (const t of ["UC", "FR", "BR", "AC", "NFR"]) {
  if (idMap.counts[t].Baseline !== EXPECT_BASE[t] || idMap.counts[t].backlog !== EXPECT_BACK[t]) {
    console.error(`Bucket count mismatch ${t}:`, idMap.counts[t], "expected", EXPECT_BASE[t], EXPECT_BACK[t]);
    process.exit(1);
  }
}

console.log("Inventory OK:", counts, "buckets:", idMap.counts);

// ========== Build backlog.md ==========
function sectionTitle(type) {
  return { UC: "Use Cases", FR: "Functional Requirements", BR: "Business Rules", AC: "Acceptance Criteria", NFR: "Non-Functional Requirements" }[type];
}

let backlog = `# Backlog требований (вне MVP Baseline)

**Продукт:** Employee Service  
**ID документа:** DOC-BACKLOG  
**Статус:** Backlog  
**Версия:** 1.0  
**Связанный Baseline:** [docs/02-requirements/](./02-requirements/)

Документ хранит полный исходный текст требований, вынесенных из MVP Baseline (этап 3).  
ID не удаляются и не перенумеровываются — они сохранены для трассировки и будущего scope.

> Замечание: в теле backlog-требований могут встречаться ссылки на Baseline ID (это нормально). Baseline-файлы не должны содержать backlog ID в Related/Связи/трассировке без отсылки сюда.

---

## Сводка перенесённых ID

| Тип | ID | Причина |
| :--- | :--- | :--- |
`;

for (const type of ["UC", "FR", "BR", "AC", "NFR"]) {
  for (const id of Object.keys(idMap[type]).sort(naturalIdSort)) {
    if (idMap[type][id].bucket === "backlog") {
      backlog += `| ${type} | ${id} | ${idMap[type][id].reason} |\n`;
    }
  }
}

backlog += `
**Итого backlog:** UC ${EXPECT_BACK.UC} + FR ${EXPECT_BACK.FR} + BR ${EXPECT_BACK.BR} + AC ${EXPECT_BACK.AC} + NFR ${EXPECT_BACK.NFR} = **${Object.values(EXPECT_BACK).reduce((a, b) => a + b, 0)}**

**Итого Baseline:** UC ${EXPECT_BASE.UC} + FR ${EXPECT_BASE.FR} + BR ${EXPECT_BASE.BR} + AC ${EXPECT_BASE.AC} + NFR ${EXPECT_BASE.NFR} = **${Object.values(EXPECT_BASE).reduce((a, b) => a + b, 0)}**

**Инвентарь всего:** 15 + 38 + 29 + 32 + 29 = **143**

---

`;

const sourceBlocks = { UC: ucBlocks, FR: frBlocks, BR: brBlocks, AC: acBlocks, NFR: nfrBlocks };
for (const type of ["UC", "FR", "BR", "AC", "NFR"]) {
  backlog += `## ${sectionTitle(type)} (backlog)\n\n`;
  for (const id of Object.keys(sourceBlocks[type]).sort(naturalIdSort)) {
    if (idMap[type][id].bucket !== "backlog") continue;
    backlog += `### ${id}\n\n`;
    backlog += `**Причина выноса:** ${idMap[type][id].reason}\n\n`;
    // Full original text (heading already in block for most)
    let body = sourceBlocks[type][id];
    // Avoid duplicate ### if we already added ### id — keep original heading as-is inside a blockquote? User asked FULL original text.
    // Put original block verbatim.
    backlog += body.trim() + "\n\n---\n\n";
  }
}

write(path.join(DOCS, "backlog.md"), backlog);

// ========== Rebuild Baseline use-cases.md ==========
const ucHeader = `# Пользовательские сценарии (Use Cases)

**Проект:** Employee Service  
**Документ:** Use Cases  
**ID:** DOC-UC  
**Версия:** 1.0  
**Статус:** Baseline v1.0

MVP Baseline (этап 3). Сценарии вне Baseline — [docs/backlog.md](../backlog.md).

Нумерация UC детализирует список Vision (разделение Create/Submit и др.).

---

`;

let ucOut = ucHeader;
const ucTitles = {
  "UC-03": "Browse Service Catalog",
  "UC-04": "Create Request",
  "UC-05": "Submit Request",
  "UC-06": "View My Request",
  "UC-07": "Approve Request",
  "UC-08": "Reject Request",
  "UC-09": "Return Request",
  "UC-10": "Cancel Request",
  "UC-14": "View Request History",
};

for (const id of [...BASELINE.UC].sort(naturalIdSort)) {
  let block = cleanBlockReferences(ucBlocks[id]);
  // Extra cleanup for known Related cells with mixed IDs
  block = scrubBaselineBody(block);
  ucOut += block.trim() + "\n\n---\n\n";
}

ucOut += `## Сводка

| ID | Название |
| :--- | :--- |
`;
for (const id of [...BASELINE.UC].sort(naturalIdSort)) {
  ucOut += `| ${id} | ${ucTitles[id]} |\n`;
}
ucOut += `
**Количество UC (Baseline): ${EXPECT_BASE.UC}**  
Backlog UC: см. [docs/backlog.md](../backlog.md).

---

## Open Questions / TBD

**Обязательных открытых вопросов для Этапа 3 нет.**  
Закрытые решения — [business-rules.md](./business-rules.md) §9.

---

## Трассировка

См. таблицы Related FR / Related BR в каждом UC. Обратная трассировка FR→UC — в [functional-requirements.md](./functional-requirements.md).  
Backlog-требования — [docs/backlog.md](../backlog.md).
`;

write(path.join(REQ, "use-cases.md"), ucOut);

function scrubBaselineBody(text) {
  // Replace standalone backlog ID tokens in Related table cells more carefully
  // Also handle narrative mentions that are purely related-list style
  return text
    .split("\n")
    .map((line) => {
      if (
        line.includes("**Related FR**") ||
        line.includes("**Related BR**") ||
        line.includes("**Related:**") ||
        line.includes("**Связи**") ||
        line.includes("**Связи:**")
      ) {
        return cleanRelatedLine(line);
      }
      return line;
    })
    .join("\n");
}

// ========== FR Baseline ==========
const frAreas = {
  CAT: ["FR-CAT-01", "FR-CAT-02", "FR-CAT-03"],
  CAB: ["FR-CAB-02"],
  REQ: ["FR-REQ-01", "FR-REQ-02", "FR-REQ-03", "FR-REQ-04", "FR-REQ-05", "FR-REQ-06", "FR-REQ-07", "FR-REQ-08", "FR-REQ-09"],
  APP: ["FR-APP-01", "FR-APP-02", "FR-APP-03", "FR-APP-04", "FR-APP-05", "FR-APP-06", "FR-APP-07"],
  AUDIT: ["FR-AUDIT-01", "FR-AUDIT-02"],
};

const frAreaTitles = {
  CAB: "2. CAB — Личный кабинет (ядро)",
  CAT: "3. CAT — Каталог заявок",
  REQ: "4. REQ — Жизненный цикл заявки",
  APP: "5. APP — Согласование",
  AUDIT: "7. AUDIT — История",
};

let frOut = `# Функциональные требования

**Проект:** Employee Service  
**Документ:** Functional Requirements  
**ID:** DOC-FR  
**Версия:** 1.0  
**Статус:** Baseline v1.0

MVP Baseline (этап 3). Формат ID: \`FR-<AREA>-NN\`.  
Области Baseline: CAB (частично), CAT, REQ, APP, AUDIT.  
AUTH, NOTIF, ADMIN и часть CAB — [docs/backlog.md](../backlog.md).

---

`;

// Order: CAB, CAT, REQ, APP, AUDIT matching original numbering spirit
const frOrder = ["CAB", "CAT", "REQ", "APP", "AUDIT"];
let secNum = 1;
for (const area of frOrder) {
  const ids = frAreas[area];
  frOut += `## ${secNum}. ${frAreaTitles[area].replace(/^\d+\.\s*/, "")}\n\n`;
  secNum++;
  for (const id of ids) {
    let block = scrubBaselineBody(frBlocks[id]);
    // FR-specific: strip admin actor mentions in FR-REQ-04 related — cleaned via Связи
    // Soften FR-REQ-04 actor line admin — keep text but it's describing visibility; BR-13 is backlog.
    // User said strip from Related/Связи/trace — body can keep narrative. Clean Связи only.
    frOut += block.trim() + "\n\n";
  }
}

frOut += `## ${secNum}. Сводка количества FR (Baseline)

| Область | ID | Кол-во |
| :--- | :--- | ---: |
| CAB | FR-CAB-02 | 1 |
| CAT | FR-CAT-01…03 | 3 |
| REQ | FR-REQ-01…09 | 9 |
| APP | FR-APP-01…07 | 7 |
| AUDIT | FR-AUDIT-01…02 | 2 |
| **Итого Baseline** | | **${EXPECT_BASE.FR}** |

Backlog FR (AUTH, CAB-01/03, NOTIF, ADMIN): см. [docs/backlog.md](../backlog.md).

---

## ${secNum + 1}. Open Questions / TBD

**Обязательных открытых вопросов для Этапа 3 нет.**  
См. сводку закрытых решений в [business-rules.md](./business-rules.md) §9–10.

---

## ${secNum + 2}. Трассировка (сводка Baseline)

| FR | BR | UC | AC |
| :--- | :--- | :--- | :--- |
| FR-CAB-02 | BR-01 | UC-06 | — |
| FR-CAT-01 | BR-10 | UC-03 | AC-CAT-01, AC-CAT-02 |
| FR-REQ-01 | BR-19 | UC-04 | AC-APP-01 |
| FR-REQ-02 | BR-26 | UC-04 | AC-DRAFT-01 |
| FR-REQ-03 | BR-08, BR-18, BR-20, BR-22, BR-26 | UC-05 | AC-APP-02, AC-APP-03, AC-APP-10, AC-DRAFT-01, AC-DRAFT-02 |
| FR-REQ-06 | BR-25, BR-28 | UC-06 | AC-REQ-06 |
| FR-REQ-07 | BR-07 | UC-10 | AC-REQ-07 |
| FR-REQ-09 | BR-06, BR-22, BR-26 | UC-05 | AC-APP-08, AC-DRAFT-02 |
| FR-APP-02 | BR-14 | UC-07 | AC-ACC-06 |
| FR-APP-03 | BR-03, BR-17, BR-21, BR-25 | UC-07 | AC-APP-04, AC-APP-09 |
| FR-APP-04 | BR-04, BR-21, BR-25 | UC-08 | AC-APP-06 |
| FR-APP-05 | BR-05, BR-21, BR-25 | UC-09 | AC-APP-07 |
| FR-APP-06 | BR-02, BR-03 | UC-07 | AC-APP-05 |
| FR-AUDIT-01 | BR-24 | UC-14 | — |

Backlog-трассировка — [docs/backlog.md](../backlog.md).
`;

write(path.join(REQ, "functional-requirements.md"), frOut);

// ========== BR Baseline ==========
// Rebuild by sections keeping baseline BRs in original section order
const brSectionMap = [
  {
    title: "2. Правила доступа и видимости",
    ids: ["BR-01", "BR-14", "BR-15", "BR-16"],
  },
  {
    title: "3. Правила маршрута и согласования",
    ids: ["BR-02", "BR-03", "BR-04", "BR-05", "BR-17", "BR-18", "BR-12"],
  },
  {
    title: "4. Правила жизненного цикла заявки",
    ids: ["BR-06", "BR-07", "BR-19", "BR-20", "BR-21", "BR-25", "BR-26", "BR-28"],
  },
  {
    title: "5. Правила snapshot и каталога",
    ids: ["BR-08", "BR-09", "BR-22", "BR-10"],
  },
  {
    title: "6. Правила аудита",
    ids: ["BR-24"],
  },
];

let brOut = `# Бизнес-правила

**Проект:** Employee Service  
**Документ:** Business Rules  
**ID:** DOC-BR  
**Версия:** 1.0  
**Статус:** Baseline v1.0  
**Связанные артефакты:** [Vision & Scope](../01-vision-and-scope/vision-scope.md), [Глоссарий](../01-vision-and-scope/glossary.md), [Backlog](../backlog.md)

---

## 1. Назначение

Документ фиксирует бизнес-правила **MVP Baseline**, обязательные для реализации и проверки. Правила имеют устойчивые ID \`BR-XX\` и используются в FR, UC и AC.  
Правила вне Baseline сохранены в [docs/backlog.md](../backlog.md).

---

`;

for (const sec of brSectionMap) {
  brOut += `## ${sec.title}\n\n`;
  for (const id of sec.ids) {
    let block = scrubBaselineBody(brBlocks[id]);
    if (id === "BR-01") {
      block = cleanBlockReferences(block, { isBr01: true });
      // Also remove BR-13, FR-ADMIN-07, UC-15, AC from Связи if still present
      block = block.replace(/\*\*Связи:\*\*.*/, (line) => cleanRelatedLine(line));
    }
    // BR-09 references FR-ADMIN — clean Связи
    // BR-16 references FR-AUTH — clean Связи
    // BR-18 references FR-ADMIN — clean Связи
    // BR-26 references FR-ADMIN-02 — clean Связи
    brOut += block.trim() + "\n\n";
  }
}

const brSummaryTitles = {
  "BR-01": "Сотрудник видит только свои заявки",
  "BR-02": "Маршрут последовательный",
  "BR-03": "First-approve wins",
  "BR-04": "Reject завершает заявку",
  "BR-05": "Return → returned",
  "BR-06": "После return — правка и повторный submit с того же этапа",
  "BR-07": "Отмена только draft/returned",
  "BR-08": "Snapshot при первом submit",
  "BR-09": "Конфиг не влияет на запущенные заявки",
  "BR-10": "Неактивный тип скрыт в каталоге",
  "BR-12": "Нет оргструктурного auto-routing",
  "BR-14": "Approver видит заявки со своими задачами",
  "BR-15": "Действие только по своей открытой задаче",
  "BR-16": "Множественные роли (union)",
  "BR-17": "Approve последнего этапа → approved",
  "BR-18": "Валидация маршрута при активации и при submit",
  "BR-19": "Создание → draft",
  "BR-20": "Submit → in_approval + задачи",
  "BR-21": "Запрет самосогласования",
  "BR-22": "Resubmit: маршрут snapshot неизменен; схема/значения обновляются",
  "BR-24": "Минимальный набор audit-событий",
  "BR-25": "Комментарий обязателен при reject/return; для approve нет",
  "BR-26": "Edit draft/returned — актуальная схема; после submit — snapshot схемы и значений",
  "BR-28": "Свободные комментарии инициатора в in_approval",
};

brOut += `## 7. Сводка ID (Baseline)

| ID | Кратко |
| :--- | :--- |
`;
for (const id of [...BASELINE.BR].sort(naturalIdSort)) {
  brOut += `| ${id} | ${brSummaryTitles[id]} |\n`;
}
brOut += `
**Количество BR (Baseline): ${EXPECT_BASE.BR}**  
Backlog BR: см. [docs/backlog.md](../backlog.md).

---

## 8. Согласованность с Vision & Scope

Проверка BR Baseline против Vision & Scope: **противоречий по ядру MVP не выявлено**. Scope не расширялся.

Замечание по нумерации UC: в Vision — UC-01…UC-12; детальные UC Baseline — см. [use-cases.md](./use-cases.md). Уточнение детализации, не конфликт scope.

---

## 9. Закрытые решения (бывшие Open Questions)

| Бывший OQ | Решение | Где зафиксировано |
| :--- | :--- | :--- |
| OQ-BR-01 | Самосогласование запрещено | BR-21 |
| OQ-BR-02 | Свободные комментарии инициатора в in_approval | BR-28 |
| OQ-BR-03 | Остальные задачи этапа → \`cancelled\` | BR-03 |
| OQ-FR-01 / OQ-UC-02 / OQ-AC-02 | Комментарий обязателен при reject/return; для approve нет | BR-25 |
| OQ-FR-02 | Схема: актуальная при edit draft/returned; snapshot после submit | BR-26 |
| OQ-FR-03 | Уведомление в одной транзакции с событием | см. [docs/backlog.md](../backlog.md) (BR-29) |
| OQ-FR-04 | Валидация маршрута при активации и при submit | BR-18 |
| OQ-HOME-01 | После login — ЛК + навигация по union roles | BR-16 (login UI — backlog) |
| OQ-NFR-01 | JWT TTL = 8 часов | см. backlog (NFR-SEC-04) |
| OQ-NFR-02 / OQ-ERR-01 / OQ-AC-01 | Чужой скрываемый ресурс → 404 | NFR-SEC-05 |
| OQ-NFR-03 | Perf baseline ≥ 1000 заявок / 5000 history | NFR-PERF-04 |
| OQ-NFR-04 | Password hash: bcrypt или эквивалент | см. backlog (NFR-SEC-03) |
| OQ-NFR-LOG | Retention техлогов = 14 дней | NFR-LOG-03 |
| OQ-RBAC-01 | Admin не создаёт заявки от сотрудника | см. backlog (BR-27) |
| OQ-RBAC-02 | Approver видит полную карточку по своей задаче | BR-14 |
| OQ-ERR-02 | Optimistic locking в админке не реализуется | error-matrix |
| OQ-ERR-03 | Пустой каталог → HTTP 200 + [] | FR-CAT-01 / error-matrix |
| HTTPS внешний стенд | Обязателен | NFR-SEC-06 |
| Multi-instance | Вне MVP | см. backlog (NFR-SCL-01) |
| Retention истории заявок | 60 дней в MVP | NFR-LOG-03 |
| Выбор активной роли | Не требуется; union permissions | BR-16 |

---

## 10. Оставшиеся Open Questions / TBD

**Обязательных для проектирования открытых вопросов нет.**

---

## 11. Трассировка (Baseline)

| BR | FR (основные) | UC | AC |
| :--- | :--- | :--- | :--- |
| BR-01 | FR-REQ-04 | UC-06 | AC-ACC-01 |
| BR-02 | FR-APP-06 | UC-07 | AC-APP-05 |
| BR-03 | FR-APP-03, FR-APP-06, FR-APP-07 | UC-07 | AC-APP-09 |
| BR-04 | FR-APP-04 | UC-08 | AC-APP-06 |
| BR-05 | FR-APP-05, FR-REQ-08 | UC-09 | AC-APP-07 |
| BR-06 | FR-REQ-09 | UC-05 | AC-APP-08 |
| BR-07 | FR-REQ-07 | UC-10 | AC-REQ-07 |
| BR-08 | FR-REQ-03 | UC-05 | AC-APP-10 |
| BR-09 | см. backlog (admin FR) | — | AC-APP-10 |
| BR-10 | FR-CAT-01 | UC-03 | AC-CAT-01 |
| BR-12 | см. backlog (admin FR) | — | — |
| BR-14 | FR-APP-02, FR-REQ-04 | UC-07 | AC-ACC-06 |
| BR-16 | см. backlog (AUTH FR) | — | — |
| BR-18 | FR-REQ-03 | UC-05 | AC-APP-02b |
| BR-21 | FR-APP-03–05 | UC-07–09 | AC-ACC-03 |
| BR-22 | FR-REQ-09 | UC-05 | AC-APP-08, AC-DRAFT-02 |
| BR-25 | FR-APP-03–05 | UC-07–09 | AC-APP-04, AC-APP-06, AC-APP-07 |
| BR-26 | FR-REQ-02, FR-REQ-03 | UC-04, UC-05 | AC-DRAFT-01, AC-DRAFT-02 |
| BR-28 | FR-REQ-06 | UC-06 | AC-REQ-06 |

Backlog BR/FR/UC/AC — [docs/backlog.md](../backlog.md).
`;

write(path.join(REQ, "business-rules.md"), brOut);

// ========== AC Baseline ==========
const acSections = [
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

const acTitles = {};
for (const [id, block] of Object.entries(acBlocks)) {
  const m = block.match(/^### (AC-\S+) — (.+)$/m);
  if (m) acTitles[id] = m[2].trim();
}

let acOut = `# Acceptance Criteria

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

for (const sec of acSections) {
  acOut += `## ${sec.title}\n\n`;
  for (const id of sec.ids) {
    let block = scrubBaselineBody(acBlocks[id]);
    acOut += block.trim() + "\n\n---\n\n";
  }
}

acOut += `## 15. Сводка AC (Baseline)

| ID | Тема |
| :--- | :--- |
`;
for (const id of [...BASELINE.AC].sort(naturalIdSort)) {
  acOut += `| ${id} | ${acTitles[id] || ""} |\n`;
}
acOut += `
**Количество AC (Baseline): ${EXPECT_BASE.AC}**  
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

write(path.join(REQ, "acceptance-criteria.md"), acOut);

// ========== NFR Baseline ==========
const nfrSections = [
  { title: "2. Performance", ids: ["NFR-PERF-01", "NFR-PERF-02", "NFR-PERF-03", "NFR-PERF-04"] },
  { title: "3. Availability", ids: ["NFR-AVL-01", "NFR-AVL-02"] },
  { title: "4. Security", ids: ["NFR-SEC-02", "NFR-SEC-05", "NFR-SEC-06"] },
  { title: "5. Reliability", ids: ["NFR-REL-01", "NFR-REL-02", "NFR-REL-03"] },
  { title: "6. Maintainability", ids: ["NFR-MNT-01", "NFR-MNT-02", "NFR-MNT-03"] },
  { title: "7. Scalability", ids: ["NFR-SCL-02"] },
  { title: "8. Logging / Audit", ids: ["NFR-LOG-01", "NFR-LOG-02", "NFR-LOG-03"] },
  { title: "9. Usability", ids: ["NFR-USB-01", "NFR-USB-02", "NFR-USB-03"] },
  { title: "10. Deployment", ids: ["NFR-DEP-01", "NFR-DEP-02", "NFR-DEP-03"] },
];

let nfrOut = `# Нефункциональные требования

**Проект:** Employee Service  
**Документ:** Non-Functional Requirements  
**ID:** DOC-NFR  
**Версия:** 1.0  
**Статус:** Baseline v1.0

MVP Baseline (этап 3). NFR вне Baseline — [docs/backlog.md](../backlog.md).

> **Замечание по поставке (Vision §11 vs NFR-DEP-01):** Vision §11 предполагает локальный стенд + Render + Neon; **NFR-DEP-01** фиксирует поставку через **Docker Compose** для локального/демо-стенда. Новый NFR не создаётся — расхождение зафиксировано здесь и в причине NFR-DEP-01 в backlog-карте этапа 3.

---

## 1. Назначение

NFR задают проверяемые ограничения качества MVP Baseline.

---

`;

for (const sec of nfrSections) {
  nfrOut += `## ${sec.title}\n\n`;
  for (const id of sec.ids) {
    let block = scrubBaselineBody(nfrBlocks[id]);
    // Clean body mentions of backlog IDs in NFR-SEC-02 (BR-13), NFR-PERF (admin), etc. lightly in related lines only
    // Also scrub **Проверка:** lines that cite backlog AC
    block = block
      .split("\n")
      .map((line) => {
        if (line.includes("**Проверка:**") || line.startsWith("Доступ разграничивается")) {
          return line.replace(ID_TOKEN_RE, (tok) => {
            const expanded = expandToken(tok);
            if (expanded.every((id) => isBacklogId(id))) return "см. [docs/backlog.md](../backlog.md)";
            if (expanded.some((id) => isBacklogId(id))) {
              const keep = expanded.filter((id) => !isBacklogId(id));
              return keep.length ? keep.join(", ") : "см. [docs/backlog.md](../backlog.md)";
            }
            return tok;
          });
        }
        return line;
      })
      .join("\n");
    nfrOut += block.trim() + "\n\n";
  }
}

nfrOut += `## 11. Open Questions / TBD

**Обязательных открытых NFR-вопросов для Этапа 3 нет.**

Ранее закрытые OQ по JWT/password/multi-instance — в [docs/backlog.md](../backlog.md) (NFR-SEC-01/03/04, NFR-SCL-01) и [business-rules.md](./business-rules.md) §9.

---

## 12. Трассировка (фрагмент Baseline)

| NFR | Связанные FR / BR / AC |
| :--- | :--- |
| NFR-SEC-02 | BR-01, BR-14–16, BR-21, AC-ACC-01, AC-ACC-02, AC-ACC-03, AC-ACC-06 |
| NFR-REL-01 | BR-03–05, BR-20, AC-APP-* |
| NFR-LOG-02 | FR-AUDIT-01, BR-24, UC-14 |
| NFR-DEP-01 | Docker Compose (локальная поставка); Vision §11 также описывает Render+Neon — без нового NFR |

Backlog NFR — [docs/backlog.md](../backlog.md).

## 13. Сводка NFR (Baseline)

| ID | Область |
| :--- | :--- |
`;
for (const id of [...BASELINE.NFR].sort(naturalIdSort)) {
  nfrOut += `| ${id} | ${id.split("-")[1]} |\n`;
}
nfrOut += `
**Количество NFR (Baseline): ${EXPECT_BASE.NFR}**  
Полный инвентарь NFR (29): NFR-PERF-01..04, NFR-AVL-01..02, NFR-SEC-01..06, NFR-REL-01..03, NFR-MNT-01..03, NFR-SCL-01..02, NFR-LOG-01..03, NFR-USB-01..03, NFR-DEP-01..03.
`;

write(path.join(REQ, "non-functional-requirements.md"), nfrOut);

// ========== RBAC light update ==========
let rbac = read(path.join(REQ, "rbac-matrix.md"));
rbac = rbac.replace(/\*\*Статус:\*\* Draft \(Этап 2\)/, "**Статус:** Baseline v1.0");
rbac = rbac.replace(
  /\*\*Версия:\*\* 1\.0\n\*\*Статус:\*\* Baseline v1\.0/,
  "**Версия:** 1.0  \n**Статус:** Baseline v1.0"
);

// Rewrite RBAC more carefully
const rbacOut = `# Матрица прав доступа (RBAC)

**Проект:** Employee Service  
**Документ:** RBAC Matrix  
**ID:** DOC-RBAC  
**Версия:** 1.0  
**Статус:** Baseline v1.0

**Обозначения:**  
\`C\` — create · \`R\` — read · \`U\` — update · \`D\` — delete · \`A\` — action · \`—\` — нет доступа

Права пользователя с несколькими ролями объединяются (**union**, BR-16).

Ядро Baseline: роли \`employee\` / \`approver\`. Admin-only операции и ACL-04/ACL-09 — см. раздел Backlog ниже и [docs/backlog.md](../backlog.md).

---

## 1. Матрица функций (ядро Baseline)

| Function | employee | approver | admin (см. backlog) |
| :--- | :---: | :---: | :---: |
| Просмотр каталога активных типов | R | — | R (удобство проверки; создание заявок — нет) |
| Просмотр схемы формы типа | R | — | R |
| Создание заявки (draft) | C | — | — |
| Редактирование своей заявки (\`draft\` / \`returned\`) | U | — | — |
| Submit / повторный submit своей заявки | A | — | — |
| Отмена своей заявки (\`draft\` / \`returned\`) | A | — | — |
| Просмотр своих заявок (список/карточка) | R | — | — |
| Свободный комментарий к своей заявке (в т.ч. \`in_approval\`) | C / R | — | — |
| Очередь своих задач согласования | — | R | — |
| Просмотр заявки по своей задаче (полная карточка) | — | R | — |
| Approve / Reject / Return по своей задаче | — | A | — |
| Комментарий при решении по задаче | — | C | — |
| История своей заявки | R | — | — |
| История заявки по своей задаче | — | R | — |
| Выполнение approve/reject/return без задачи | — | — | — |

Примечания к ячейкам (Baseline):
- \`approver\` без роли \`employee\` не создаёт заявки.
- Для reject/return комментарий обязателен (BR-25); для approve — нет.
- Инициатор может оставлять свободные комментарии в \`in_approval\` (BR-28).
- Login / профиль / in-app уведомления / CRUD админки — [docs/backlog.md](../backlog.md).

---

## 2. Ограничения доступа (Baseline)

### ACL-01 — Чужие заявки сотрудника
\`employee\` не может читать/изменять/отменять заявку другого инициатора (BR-01).  
Ожидаемый результат: **HTTP 404** + \`ERR_NOT_FOUND\` (NFR-SEC-05).

### ACL-02 — Чужие задачи согласующего
\`approver\` не может approve/reject/return по задаче, где он не assignee (BR-15). → **403** / \`ERR_FORBIDDEN_APPROVAL\`.

### ACL-03 — Самосогласование
Инициатор не выполняет решения по своей заявке (BR-21). → **403** / \`ERR_FORBIDDEN_APPROVAL\`.

### ACL-05 — Неактивный тип
Создание заявки по неактивному типу запрещено (BR-10). → \`ERR_INACTIVE_TYPE\`.

### ACL-06 — Недопустимый статус для действия
Submit/cancel/edit/approve и т.д. вне допустимых статусов → \`ERR_INVALID_STATE\`.

### ACL-07 — Завершённая / cancelled задача
Повторное действие по завершённой или \`cancelled\` задаче запрещено (NFR-REL-02, BR-03). → \`ERR_TASK_DONE\` / \`ERR_DUP_ACTION\`.

### ACL-08 — Множественные роли
Пользователь с несколькими ролями получает объединение permissions (BR-16). Отдельный выбор активной роли не требуется.  
(Полный сценарий login/JWT — backlog.)

---

## 3. Backlog (admin / auth UI)

Следующие строки и ACL отложены вместе с admin/AUTH/NOTIF:

| Function / ACL | Примечание |
| :--- | :--- |
| Login / получить текущую сессию | backlog (UC-01, FR-AUTH-*) |
| Просмотр своего профиля | backlog (UC-02, FR-CAB-01) |
| Просмотр своих in-app уведомлений / mark read | backlog (UC-13, FR-NOTIF-*) |
| CRUD типов / полей / маршрутов / справочников | backlog (UC-11, UC-12, FR-ADMIN-01…06) |
| Реестр всех заявок / история любой заявки | backlog (UC-15, FR-ADMIN-07/08, BR-13) |
| **ACL-04** — Недоступность админки | backlog (AC-ACC-04) |
| **ACL-09** — Admin не создаёт заявки от сотрудника | backlog (BR-27, AC-ACC-04) |

Полные тексты — [docs/backlog.md](../backlog.md).

---

## 4. Связь с ролями Vision

| Роль Vision | Код | Матрица |
| :--- | :--- | :--- |
| Сотрудник | \`employee\` | колонка employee |
| Согласующий | \`approver\` | колонка approver |
| Администратор | \`admin\` | backlog (колонка admin) |

Отдельные колонки «Руководитель» / «HR» **не вводятся** (соответствует Vision).

---

## 5. Open Questions / TBD

**Обязательных открытых вопросов RBAC для Этапа 3 нет.**

---

## 6. Трассировка (Baseline)

| Ограничение | BR | FR | AC |
| :--- | :--- | :--- | :--- |
| ACL-01 | BR-01 | FR-REQ-04 | AC-ACC-01 |
| ACL-02 | BR-15 | FR-APP-03–05 | AC-ACC-02 |
| ACL-03 | BR-21 | FR-APP-03–05 | AC-ACC-03 |
| ACL-05 | BR-10 | FR-REQ-01 | AC-CAT-01 |
| ACL-08 | BR-16 | см. backlog (AUTH) | см. backlog (AC-AUTH-01) |
| Полная карточка approver | BR-14 | FR-APP-02 | AC-ACC-06 |

ACL-04 / ACL-09 — [docs/backlog.md](../backlog.md).
`;

write(path.join(REQ, "rbac-matrix.md"), rbacOut);

// ========== Error matrix light update ==========
const errOut = `# Матрица ошибок

**Проект:** Employee Service  
**Документ:** Error Matrix  
**ID:** DOC-ERR  
**Версия:** 1.0  
**Статус:** Baseline v1.0

Документ задаёт коды ошибок для будущего REST API. **Конкретные endpoint на этом этапе не проектируются.**

Рекомендуемый формат тела ошибки (ориентир для Этапа 4):

\`\`\`json
{
  "error_code": "ERR_FORBIDDEN",
  "message": "Недостаточно прав для выполнения операции",
  "details": {}
}
\`\`\`

---

## 1. Матрица (ядро Baseline)

| Error code | HTTP status | Condition | User message | System behavior |
| :--- | :---: | :--- | :--- | :--- |
| ERR_FORBIDDEN | 403 | Роль не позволяет операцию | Недостаточно прав для выполнения операции | Состояние данных не меняется |
| ERR_FORBIDDEN_APPROVAL | 403 | Пользователь не assignee задачи, либо самосогласование (BR-15, BR-21) | Вы не можете выполнить действие по этой задаче | Заявка и задача не меняются |
| ERR_NOT_FOUND | 404 | Ресурс не существует **или** скрыт правилами видимости (чужая заявка) | Объект не найден | Состояние не меняется |
| ERR_VALIDATION | 422 | Нарушение схемы/обязательных полей/форматов/page_size | Проверьте корректность заполнения полей | Детали по полям в \`details\`; запись не создаётся/не обновляется |
| ERR_INACTIVE_TYPE | 409 | Попытка создать/отправить заявку по неактивному типу (BR-10) | Этот тип заявки недоступен | Заявка не создаётся / submit не выполняется |
| ERR_INVALID_STATE | 409 | Действие недопустимо в текущем статусе заявки/задачи (cancel не из draft/returned, edit не из draft/returned, submit не из draft/returned и т.п.) | Действие недоступно для текущего статуса | Статус не меняется; пишется технический лог |
| ERR_TASK_DONE | 409 | Задача уже завершена (approve/reject/return уже выполнены или закрыта системой) | Задача уже обработана | Повторное решение не применяется |
| ERR_DUP_ACTION | 409 | Повтор того же бизнес-действия в условиях гонки/повтора запроса | Действие уже было выполнено | Идемпотентный отказ; итоговое состояние сохраняется |
| ERR_ROUTE_CONFIG | 409 | Маршрут типа невалиден при submit (и при активации типа — admin backlog): нет этапов и/или нет назначений (BR-18) | Маршрут согласования настроен некорректно | Submit отклоняется; draft/returned сохраняется |
| ERR_CONFLICT_VERSION | — | **Не используется в MVP.** Optimistic locking не реализуется | — | — |
| ERR_INTERNAL | 500 | Непредвиденная ошибка сервера | Произошла внутренняя ошибка. Попробуйте позже | Rollback транзакции; ошибка в технический лог с request_id; клиенту без stack trace |

---

## 1b. Backlog auth errors (отложено вместе с login/JWT)

Коды остаются в словаре API, но сценарии login/JWT — backlog ([docs/backlog.md](../backlog.md), UC-01, FR-AUTH-*, NFR-SEC-01/04):

| Error code | HTTP status | Condition | User message | System behavior | Статус |
| :--- | :---: | :--- | :--- | :--- | :--- |
| ERR_INVALID_CREDENTIALS | 401 | Неверный логин и/или пароль | Неверный логин или пароль | Токен не выдаётся; факт существования логина не уточняется | **Deferred** (с login) |
| ERR_UNAUTHORIZED | 401 | Нет токена, токен просрочен или повреждён | Требуется аутентификация | Запрос отклоняется до бизнес-логики | **Deferred** (с JWT/login) |

---

## 2. Минимальное покрытие (чеклист)

| Требование заказчика | Error code | Baseline / backlog |
| :--- | :--- | :--- |
| invalid credentials | ERR_INVALID_CREDENTIALS | backlog (auth) |
| unauthorized | ERR_UNAUTHORIZED | backlog (auth) |
| forbidden | ERR_FORBIDDEN / ERR_FORBIDDEN_APPROVAL | Baseline |
| resource not found | ERR_NOT_FOUND | Baseline |
| validation error | ERR_VALIDATION | Baseline |
| inactive request type | ERR_INACTIVE_TYPE | Baseline |
| invalid request state | ERR_INVALID_STATE | Baseline |
| user cannot perform approval | ERR_FORBIDDEN_APPROVAL | Baseline |
| task already completed | ERR_TASK_DONE | Baseline |
| route configuration error | ERR_ROUTE_CONFIG | Baseline (submit); активация типа — backlog admin |
| duplicate action | ERR_DUP_ACTION | Baseline |
| internal error | ERR_INTERNAL | Baseline |

---

## 3. Связь с BR / FR (Baseline)

| Error code | BR / FR |
| :--- | :--- |
| ERR_INACTIVE_TYPE | BR-10, FR-CAT-01, FR-REQ-01 |
| ERR_INVALID_STATE | BR-07, BR-19, BR-20, FR-REQ-07 |
| ERR_FORBIDDEN_APPROVAL | BR-15, BR-21, FR-APP-03–05 |
| ERR_TASK_DONE | BR-03, NFR-REL-02 |
| ERR_ROUTE_CONFIG | BR-18, FR-REQ-03 |
| ERR_NOT_FOUND | BR-01, BR-14, NFR-SEC-05 |
| ERR_VALIDATION | BR-25, BR-26, FR-REQ-02, FR-APP-04, FR-APP-05 |

---

## 4. Open Questions / TBD

**Обязательных открытых вопросов по error-matrix для Этапа 3 нет.**

Примечание: пустой каталог **не является ошибкой** и в матрицу ошибок не входит.

---

## 5. Трассировка

Ошибки ядра используются в AC негативных сценариев Baseline: AC-ACC-01…03, AC-ACC-06, AC-CAT-01, AC-APP-*, AC-REQ-07.  
Детальная привязка к path/method — на Этапе 4 (OpenAPI).
`;

write(path.join(REQ, "error-matrix.md"), errOut);

// ========== id-map JSON ==========
write(path.join(DOCS, "_stage3-id-map.json"), JSON.stringify(idMap, null, 2) + "\n");

// ========== Scan baseline files for backlog tokens ==========
const baselineFiles = [
  "use-cases.md",
  "functional-requirements.md",
  "business-rules.md",
  "acceptance-criteria.md",
  "non-functional-requirements.md",
  "rbac-matrix.md",
  "error-matrix.md",
];

const scanReport = {};
for (const f of baselineFiles) {
  const text = read(path.join(REQ, f));
  // Exclude lines that intentionally point to backlog.md
  const lines = text.split("\n").filter((l) => !/backlog\.md/i.test(l) && !/Backlog/i.test(l) && !/Deferred/i.test(l));
  const hits = scanBacklogTokens(lines.join("\n"), f);
  scanReport[f] = hits;
}

write(path.join(DOCS, "_stage3-scan-remaining.json"), JSON.stringify(scanReport, null, 2) + "\n");

console.log("Wrote backlog.md, baseline files, _stage3-id-map.json");
console.log("Remaining backlog ID tokens in Baseline (excl. backlog-link lines):");
console.log(JSON.stringify(scanReport, null, 2));
