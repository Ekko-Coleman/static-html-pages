import { describe, expect, it } from 'vitest';
import { evaluate, parseBlocked, parseChecklists, parseMilestoneTable } from './goal-status.mjs';

const table = (m0, m1, m2, m3) =>
  parseMilestoneTable(`| Milestone | Status |
|---|---|
| M0 Harness skeleton | ${m0} |
| M1 Sim baseline | ${m1} |
| M2 Render baseline | ${m2} |
| M3 Sandbox + freeze \`baseline-v1\` | ${m3} |
| M4 Optimization run | ☐ |`);

const lists = (m3Items) =>
  parseChecklists(`## M0 Harness skeleton
- [x] a
- [x] 👤 reference Mac
## M1 Sim
- [x] b
  - [x] b.1
## M2 Render
- [x] ~~c~~ dropped
## M3 Sandbox
${m3Items}
## M4 Optimization
- [ ] 👤 later`);

describe('goal-status', () => {
  it('parses the milestone table', () => {
    expect(table('✅', '⏳ in progress', '☐', '☐')).toEqual({ M0: 'done', M1: 'active', M2: 'todo', M3: 'todo', M4: 'todo' });
  });

  it('parses markers and sub-items', () => {
    const l = parseChecklists('## M0 X\n- [ ] 👤 ask\n- [ ] ⛔ wait\n  - [X] sub\n- [ ] ~~gone~~\n## Notes\n- [ ] ignored');
    expect(l.M0.map((i) => [i.done, i.mike, i.blocked])).toEqual([
      [false, true, false],
      [false, false, true],
      [true, false, false],
      [true, false, false],
    ]);
    expect(l.Notes).toBeUndefined();
  });

  it('reads only open items under Blocked on Mike', () => {
    const md = '## Now\n- [ ] not this\n## Blocked on Mike\n- [ ] Q1 which Mac?\n- [x] answered\n## Done\n';
    expect(parseBlocked(md)).toEqual(['Q1 which Mac?']);
  });

  it('is IN PROGRESS while workable items remain', () => {
    const r = evaluate({ table: table('✅', '✅', '✅', '⏳'), lists: lists('- [ ] sandbox\n- [ ] 👤 tag'), blocked: [], frozen: false });
    expect(r.result).toBe('IN PROGRESS');
    expect(r.workable).toEqual(['M3: sandbox']);
  });

  it('is BLOCKED when only Mike items remain and a question is open', () => {
    const r = evaluate({ table: table('⏳', '☐', '☐', '☐'), lists: lists('- [ ] ⛔ needs Q1'), blocked: ['Q1 which Mac?'], frozen: false });
    expect(r.result).toBe('BLOCKED');
  });

  it('is COMPLETE once M0–M2 are done, M3 has only Mike items left and a freeze is requested', () => {
    const r = evaluate({
      table: table('✅', '✅', '✅', '⏳'),
      lists: lists('- [x] sandbox\n- [ ] 👤 tag'),
      blocked: ['Please review and tag baseline-v1'],
      frozen: false,
    });
    expect(r.result).toBe('COMPLETE');
  });
});
