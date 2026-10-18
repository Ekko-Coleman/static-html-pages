#!/usr/bin/env node
// Prints where the build-phase /goal loop stands. Read-only.
// Sources: the PROJECT.md milestone table, docs/MILESTONES.md checklists, and STATUS.md "Blocked on Mike".
// Item markers: [x] done · ~~struck~~ dropped (counts as done) · 👤 Mike only · ⛔ blocked (reason in STATUS.md).

import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const BUILD_PHASE = ['M0', 'M1', 'M2', 'M3'];

/** Milestone table rows in PROJECT.md → { M0: 'done' | 'active' | 'todo' }. */
export function parseMilestoneTable(md) {
  const out = {};
  for (const line of md.split('\n')) {
    const m = line.match(/^\|\s*(M\d)\b[^|]*\|\s*([^|]*)\|/);
    if (!m) continue;
    const cell = m[2];
    out[m[1]] = cell.includes('✅') ? 'done' : cell.includes('⏳') ? 'active' : 'todo';
  }
  return out;
}

/** docs/MILESTONES.md → { M0: [{ text, done, mike, blocked }] }. Nested sub-items count on their own. */
export function parseChecklists(md) {
  const out = {};
  let current = null;
  for (const line of md.split('\n')) {
    const h = line.match(/^##\s+(M\d)\b/);
    if (h) {
      current = h[1];
      out[current] = [];
      continue;
    }
    if (/^##\s/.test(line)) current = null;
    const item = current && line.match(/^\s*-\s+\[( |x|X)\]\s+(.*)$/);
    if (!item) continue;
    const text = item[2].trim();
    out[current].push({
      text,
      done: item[1] !== ' ' || /^~~.*~~/.test(text),
      mike: text.includes('👤'),
      blocked: text.includes('⛔'),
    });
  }
  return out;
}

/** Open `- [ ]` lines under "## Blocked on Mike" in STATUS.md. */
export function parseBlocked(md) {
  const section = md.split(/^##\s+/m).find((s) => s.startsWith('Blocked on Mike'));
  if (!section) return [];
  return section
    .split('\n')
    .map((l) => l.match(/^\s*-\s+\[ \]\s+(.*)$/))
    .filter(Boolean)
    .map((m) => m[1].trim());
}

/** Combines the parsed sources into a verdict: COMPLETE, BLOCKED or IN PROGRESS. */
export function evaluate({ table, lists, blocked, frozen }) {
  const rows = BUILD_PHASE.map((id) => {
    const items = lists[id] ?? [];
    const open = items.filter((i) => !i.done);
    return {
      id,
      status: table[id] ?? 'todo',
      total: items.length,
      done: items.length - open.length,
      workable: open.filter((i) => !i.mike && !i.blocked),
      waiting: open.filter((i) => i.mike || i.blocked),
    };
  });
  const workable = rows.flatMap((r) => r.workable.map((i) => `${r.id}: ${i.text}`));
  const tableDone = rows.slice(0, 3).every((r) => r.status === 'done');
  const freezeRequested = frozen || blocked.some((b) => /baseline-v1/.test(b));

  let result;
  if (workable.length === 0 && tableDone && freezeRequested) result = 'COMPLETE';
  else if (workable.length === 0 && blocked.length > 0) result = 'BLOCKED';
  else result = 'IN PROGRESS';
  return { rows, workable, blocked, tableDone, freezeRequested, result };
}

function git(root, args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return null;
  }
}

function main() {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
  const read = (f) => (existsSync(path.join(root, f)) ? readFileSync(path.join(root, f), 'utf8') : '');
  const frozen = git(root, ['tag', '-l', 'baseline-v1']) === 'baseline-v1';
  const r = evaluate({
    table: parseMilestoneTable(read('PROJECT.md')),
    lists: parseChecklists(read('docs/MILESTONES.md')),
    blocked: parseBlocked(read('STATUS.md')),
    frozen,
  });

  const icon = { done: '✅', active: '⏳', todo: '☐' };
  console.log('Fluid Lab goal status (build phase M0–M3)\n');
  for (const row of r.rows) {
    const waiting = row.waiting.length ? ` · ${row.waiting.length} waiting on Mike` : '';
    console.log(`  ${icon[row.status]} ${row.id}  ${row.done}/${row.total} items${waiting}`);
  }
  if (r.blocked.length) {
    console.log(`\nBlocked on Mike (${r.blocked.length} open):`);
    for (const b of r.blocked) console.log(`  - ${b}`);
  }
  if (r.workable.length) {
    console.log('\nNext workable items:');
    for (const w of r.workable.slice(0, 3)) console.log(`  - ${w}`);
  }
  const dirty = git(root, ['status', '--porcelain']);
  console.log(`\ngit: ${dirty === null ? 'not a repo' : dirty ? 'uncommitted changes' : 'clean'} · baseline-v1 tag: ${frozen ? 'yes' : 'no'}`);
  console.log(`RESULT: ${r.result}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();
