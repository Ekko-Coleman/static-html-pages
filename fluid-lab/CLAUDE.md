# CLAUDE.md: Fluid Lab

@PROJECT.md

---

## How the `/goal` loop works in this repo

`./setup.sh` (or `npm run goal`) starts Claude Code with `/goal` and the condition in `.claude/goal.txt`.
After every turn a separate evaluator checks that condition. Until it is met, you keep working.

Work in **iterations**. Each iteration:

1. **Orient.** Run `npm run goal:status`. It reads the milestone table in `PROJECT.md`, the checklist for the current milestone in `docs/MILESTONES.md`, and the open items in `STATUS.md`.
2. **Pick** the first unchecked, non-👤 item of the current milestone that isn't blocked. If an item is too big for one iteration, split it into sub-items in `docs/MILESTONES.md` first.
3. **State what you expect** in `STATUS.md` under "Now" before you write code (rule 7 applies to build work too).
4. **Build** the smallest thing that satisfies the item. Follow the code conventions in `PROJECT.md`.
5. **Verify** with `npm run check` (typecheck + unit tests + build), plus any item-specific command the checklist names. Never tick an item you have not verified by running something.
6. **Record.** Tick the item in `docs/MILESTONES.md`, move the "Now" note to "Done" in `STATUS.md` with the command you ran and its result, and commit (`git commit`, conventional message, one item per commit).
7. **Advance.** When every non-👤 item of a milestone is ticked, set that row to ✅ in the `PROJECT.md` table and the next row to ⏳. Then go to step 1.

When the condition is met, finish with `npm run goal:status` as your last command so the evaluator can see the result.

### Build phase vs optimization phase

- **Build phase (M0–M3, before `baseline-v1` exists).** You are the builder. You write `harness/`, `metrics/` and `scenes/` as normal feature work. These are Mike's areas, so list every file you add or change there under "For Mike to review" in `STATUS.md`.
- **Optimization phase (after Mike tags `baseline-v1`).** Hard rules 1, 2 and 6 in `PROJECT.md` apply in full. The guard hook (`.claude/hooks/guard.mjs`) enforces them and refuses edits to locked paths.

### Things only Mike does (👤): stop and ask, don't work around

- Choosing or confirming the reference Mac (Q1). `setup.sh` records it in `harness/reference-machine.json` when Mike says yes.
- Answering the open questions in SPEC §11.
- Tagging `baseline-v1` (or any `baseline-*` tag). The guard hook blocks it.
- Reviewing verdicts on the first ~20 experiments in M4.
- Editing `GOAL.md` or `SPEC.md`. The guard hook blocks it. Put proposed changes in `STATUS.md` under "Proposals".

When you reach one of these, add a `- [ ]` item under **Blocked on Mike** in `STATUS.md` with the exact question and the options you see. Then carry on with any other unblocked item. The goal also counts as met when nothing unblocked remains.

### Environment notes

- The benchmarks only mean something on the reference Mac (Apple Silicon, Chrome via Playwright, AC power). On any other machine, build and unit-test, but don't record performance numbers as results.
- Playwright and its Chromium build are pinned in `package.json`. Don't upgrade them without a `STATUS.md` proposal, because doing so changes the timing environment.
- Don't install global tools. Add dev dependencies with `npm i -D --save-exact`.
