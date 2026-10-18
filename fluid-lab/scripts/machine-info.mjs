#!/usr/bin/env node
// Prints this machine's benchmark-relevant facts as JSON (SPEC §5.2 environment control).
// Usage: node scripts/machine-info.mjs [--out <file>]

import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const sh = (cmd, args) => {
  try {
    return execFileSync(cmd, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return null;
  }
};

const info = {
  recorded_at: new Date().toISOString(),
  hostname: os.hostname(),
  platform: process.platform,
  arch: process.arch,
  cpu: os.cpus()[0]?.model ?? null,
  memory_gb: Math.round(os.totalmem() / 2 ** 30),
  node: process.version,
};

if (process.platform === 'darwin') {
  info.chip = sh('sysctl', ['-n', 'machdep.cpu.brand_string']);
  info.macos = sh('sw_vers', ['-productVersion']);
  info.model = sh('sysctl', ['-n', 'hw.model']);
  const displays = sh('system_profiler', ['SPDisplaysDataType']) ?? '';
  info.gpu_cores = Number(displays.match(/Total Number of Cores:\s*(\d+)/)?.[1]) || null;
  const power = sh('pmset', ['-g', 'batt']) ?? '';
  info.on_ac_power = power ? power.includes("'AC Power'") : null;
}

const json = JSON.stringify(info, null, 2);
const outIdx = process.argv.indexOf('--out');
if (outIdx > -1 && process.argv[outIdx + 1]) {
  const out = process.argv[outIdx + 1];
  mkdirSync(path.dirname(out), { recursive: true });
  writeFileSync(out, json + '\n');
}
console.log(json);
