#!/usr/bin/env node
// Checks the PreToolUse guard end to end in a throwaway git repo, so this repo is never tagged.
// Run: npm run test:guard

import { execFileSync, spawnSync } from 'node:child_process';
import { cpSync, mkdtempSync, realpathSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const tmp = realpathSync(mkdtempSync(path.join(tmpdir(), 'fluid-lab-guard-')));
// The hook runs through a symlinked project path, as on macOS (/var -> /private/var).
// File paths below use the real path, so every case also covers mixed symlinked/real paths.
const link = `${tmp}-link`;
symlinkSync(tmp, link);
const git = (...args) => execFileSync('git', ['-c', 'user.name=guard', '-c', 'user.email=guard@test', ...args], { cwd: tmp, stdio: 'ignore' });
const hook = path.join(link, '.claude/hooks/guard.mjs');

function run(tool_name, tool_input) {
  const r = spawnSync('node', [hook], {
    input: JSON.stringify({ tool_name, tool_input, cwd: link }),
    env: { ...process.env, CLAUDE_PROJECT_DIR: link },
    encoding: 'utf8',
  });
  return r.status === 2 ? 'block' : r.status === 0 ? 'allow' : `error(${r.status}): ${r.stderr}`;
}

const edit = (rel) => ['Edit', { file_path: path.join(tmp, rel) }];
const bash = (command) => ['Bash', { command }];

const phases = [
  {
    name: 'build phase (no tag, main branch)',
    setup: () => {},
    cases: [
      [edit('harness/runner.ts'), 'allow'],
      [edit('sim/p2g.wgsl'), 'allow'],
      [edit('GOAL.md'), 'block'],
      [edit('SPEC.md'), 'block'],
      [edit('.claude/hooks/guard.mjs'), 'block'],
      [edit('scenes/hashes.json'), 'block'],
      [edit('metrics/thresholds.json'), 'block'],
      [bash('cat SPEC.md'), 'allow'],
      [bash('npm run scenes:hash'), 'allow'],
      [bash("sed -i 's/2.0/1.1/' GOAL.md"), 'block'],
      [bash('echo x > SPEC.md'), 'block'],
      [bash('git tag baseline-v1'), 'block'],
      [bash('git tag -a baseline-v1 -m freeze'), 'block'],
      [bash('git tag -l baseline-v1'), 'allow'],
    ],
  },
  {
    name: 'after freeze (baseline-v1 tagged)',
    setup: () => git('tag', 'baseline-v1'),
    cases: [
      [edit('harness/runner.ts'), 'block'],
      [edit('metrics/gates.ts'), 'block'],
      [edit('scenes/dam-break.json'), 'block'],
      [edit('baselines/baseline-v1/index.html'), 'block'],
      [edit('sim/p2g.wgsl'), 'allow'],
      [bash('rm -rf harness/'), 'block'],
      [bash('npm run bench -- --scene dam-break'), 'allow'],
    ],
  },
  {
    name: 'experiment branch exp/0001-tiled-p2g',
    setup: () => git('checkout', '-q', '-b', 'exp/0001-tiled-p2g'),
    cases: [
      [edit('sim/p2g.wgsl'), 'allow'],
      [edit('render/ssfr.wgsl'), 'allow'],
      [edit('optlog/0001-tiled-p2g.md'), 'allow'],
      [edit('app/hud.ts'), 'block'],
      [edit('package.json'), 'block'],
    ],
  },
];

let failed = 0;
try {
  cpSync(path.join(root, '.claude'), path.join(tmp, '.claude'), { recursive: true });
  git('init', '-q', '-b', 'main');
  git('add', '-A');
  git('commit', '-q', '-m', 'init');
  for (const phase of phases) {
    phase.setup();
    console.log(phase.name);
    for (const [[tool, input], want] of phase.cases) {
      const got = run(tool, input);
      const label = tool === 'Bash' ? input.command : path.relative(tmp, input.file_path);
      const ok = got === want;
      if (!ok) failed++;
      console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${tool.padEnd(4)} ${label} → ${got}${ok ? '' : ` (want ${want})`}`);
    }
  }
} finally {
  rmSync(link, { force: true });
  rmSync(tmp, { recursive: true, force: true });
}

console.log(failed ? `\n${failed} guard case(s) failed` : '\nall guard cases passed');
process.exit(failed ? 1 : 0);
