#!/usr/bin/env node
// PreToolUse guard for Fluid Lab. Turns PROJECT.md's hard rules into tooling (SPEC §8 P0, §6.3).
// Reads the hook payload on stdin. Exit 0 = allow; exit 2 = block, and stderr is shown to Claude.
//
// Rules:
//   always         GOAL.md, SPEC.md and the loop's own machinery can't be edited by agents.
//   generated      hashes and thresholds can only come from their npm scripts, never hand edits.
//   after freeze   once the `baseline-v1` tag exists, harness/, metrics/, scenes/ and baselines/ are locked.
//   exp branches   on `exp/*` branches, only sim/, render/ and optlog/ can be edited.
//   tags           agents may not create `baseline-*` tags. Freezing is Mike's call.

import { execFileSync } from 'node:child_process';
import { readFileSync, realpathSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export const LOCKED_ALWAYS = [
  'GOAL.md',
  'SPEC.md',
  '.claude/goal.txt',
  '.claude/settings.json',
  '.claude/hooks/',
  'scripts/goal-status.mjs',
  'scripts/run-goal.sh',
];
export const GENERATED = {
  'scenes/hashes.json': 'npm run scenes:hash',
  'metrics/thresholds.json': 'npm run calibrate',
};
export const LOCKED_AFTER_FREEZE = ['harness/', 'metrics/', 'scenes/', 'baselines/'];
export const EXP_ALLOWED = ['sim/', 'render/', 'optlog/'];
export const FREEZE_TAG = 'baseline-v1';

const matches = (rel, prefixes) => prefixes.some((p) => (p.endsWith('/') ? rel.startsWith(p) : rel === p));

function git(root, args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return '';
  }
}

export function repoState(root) {
  return {
    frozen: git(root, ['tag', '-l', FREEZE_TAG]) === FREEZE_TAG,
    branch: git(root, ['rev-parse', '--abbrev-ref', 'HEAD']),
  };
}

/** Returns a reason string if editing `rel` (repo-relative, posix) is not allowed, else null. */
export function checkPath(rel, { frozen, branch }) {
  if (matches(rel, LOCKED_ALWAYS)) {
    return `${rel} is locked for agents. Put proposed changes under "Proposals" in STATUS.md.`;
  }
  if (GENERATED[rel]) {
    return `${rel} is generated. Run \`${GENERATED[rel]}\` instead of editing it by hand.`;
  }
  if (frozen && matches(rel, LOCKED_AFTER_FREEZE)) {
    return `${rel} is locked: ${FREEZE_TAG} exists (PROJECT.md hard rule 1). Log concerns in optlog/backlog.md under "Harness concerns".`;
  }
  if (branch.startsWith('exp/') && !matches(rel, EXP_ALLOWED)) {
    return `On experiment branch ${branch} you may only edit sim/, render/ and optlog/ (SPEC §6.1).`;
  }
  return null;
}

const WRITE_TOOL = /\b(sed|perl)\b[^\n]*\s-i|\b(tee|mv|rm|cp|truncate|dd|install|ln|chmod)\b|\bgit\s+(checkout|restore|rm|mv)\b/;
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

/** Returns a reason string if the shell command breaks a rule, else null. Heuristic, errs toward blocking. */
export function checkCommand(cmd, state) {
  if (/\bgit\s+tag\b/.test(cmd) && /\bbaseline-/.test(cmd) && !/\bgit\s+tag\s+(-l|--list|-d|--delete)\b/.test(cmd)) {
    return `Creating ${FREEZE_TAG} (or any baseline-* tag) is Mike's call. Write a freeze request under "Blocked on Mike" in STATUS.md.`;
  }
  const protectedPaths = [...LOCKED_ALWAYS, ...Object.keys(GENERATED)];
  if (state.frozen) protectedPaths.push(...LOCKED_AFTER_FREEZE);
  for (const seg of cmd.split(/&&|\|\||;|\||\n/)) {
    for (const p of protectedPaths) {
      const ref = new RegExp(`(^|[\\s'"=/.])${esc(p)}`);
      if (!ref.test(seg)) continue;
      const redirect = new RegExp(`>\\s*['"]?(\\./)?${esc(p)}`);
      if (redirect.test(seg) || WRITE_TOOL.test(seg)) {
        return `This command looks like it writes to ${p}, which is protected (see .claude/hooks/guard.mjs). Leave it to Mike or the npm script that owns it.`;
      }
    }
  }
  return null;
}

// Resolves symlinks (macOS /var -> /private/var), including for files that don't exist yet.
export function realish(p) {
  const abs = path.resolve(p);
  try {
    return realpathSync(abs);
  } catch {
    const parent = path.dirname(abs);
    return parent === abs ? abs : path.join(realish(parent), path.basename(abs));
  }
}

function main() {
  let payload;
  try {
    payload = JSON.parse(readFileSync(0, 'utf8'));
  } catch {
    process.exit(0);
  }
  const root = realish(process.env.CLAUDE_PROJECT_DIR || payload.cwd || process.cwd());
  const state = repoState(root);
  const input = payload.tool_input ?? {};
  let reason = null;

  if (payload.tool_name === 'Bash') {
    reason = checkCommand(String(input.command ?? ''), state);
  } else {
    const target = input.file_path ?? input.notebook_path;
    if (target) {
      const rel = path.relative(root, realish(path.resolve(root, target))).split(path.sep).join('/');
      if (!rel.startsWith('..')) reason = checkPath(rel, state);
    }
  }

  if (reason) {
    process.stderr.write(`Blocked by Fluid Lab guard: ${reason}\n`);
    process.exit(2);
  }
  process.exit(0);
}

// Compare resolved paths: Node reports import.meta.url with symlinks resolved, argv[1] as typed.
if (process.argv[1] && realish(process.argv[1]) === realish(fileURLToPath(import.meta.url))) main();
