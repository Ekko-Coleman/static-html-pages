# Fluid Lab

A real-time 3D fluid sandbox in WebGPU, built to show that an autonomous AI agent loop can make it measurably faster at the same accuracy.

| Read | For |
|---|---|
| [`GOAL.md`](GOAL.md) | Why: the claim and the success criteria |
| [`SPEC.md`](SPEC.md) | What: architecture, gates, loop protocol, milestones |
| [`PROJECT.md`](PROJECT.md) | How: the operating manual for humans and agents (loaded through `CLAUDE.md`) |
| [`docs/MILESTONES.md`](docs/MILESTONES.md) | SPEC §9 broken into checklists that the loop ticks off |
| [`STATUS.md`](STATUS.md) | The loop's working memory: now, done, and what's blocked on Mike |

## Quick start (on the reference Mac)

```bash
# Unzip or copy the fluid-lab folder somewhere outside other git repos, then:
cd fluid-lab
./setup.sh
```

`setup.sh` runs these steps in order:

1. Checks the machine. Benchmarks only count on Apple Silicon; other machines can still build and test.
2. Makes sure the project is its own git repo. If it's sitting inside another repo, it offers to copy itself to `~/fluid-lab`.
3. Checks for Node.js 22.12 or newer, and offers `brew install node` if it's missing.
4. Checks for Claude Code, and offers the official installer if it's missing.
5. Runs `npm ci` and installs the pinned Playwright Chromium.
6. Records this machine in `.fluidlab/machine.json` and asks whether this Mac is **the** reference machine (SPEC Q1). If you say yes, it saves the record as `harness/reference-machine.json`.
7. Initializes git and makes the first commit.
8. Runs `npm run check` as a smoke test, then starts Claude Code with **`/goal`**.

Options: `--no-launch` (set up only), `--headless` (run the loop with `claude -p`), `--mode <permission-mode>` (default `acceptEdits`), `--yes` (accept install prompts).

## The `/goal` loop

`/goal <condition>` is built into Claude Code. After every turn, a separate evaluator checks the condition, and Claude keeps working until it's met. The condition for this repo is in [`.claude/goal.txt`](.claude/goal.txt). In short: finish the **build phase** (M0–M3) up to the point where `baseline-v1` is ready for Mike to freeze, or stop when everything left needs a decision only Mike can make.

Each iteration follows the procedure in [`CLAUDE.md`](CLAUDE.md): orient with `npm run goal:status`, pick the next checklist item, build it, verify it with `npm run check`, tick it, log it in `STATUS.md`, and commit.

```bash
npm run goal:status    # where the loop stands: COMPLETE / BLOCKED / IN PROGRESS
npm run goal           # start or resume the loop (each run is a fresh session; STATUS.md carries memory)
npm run goal -- --headless --mode auto   # unattended
```

**When it stops:** read "Blocked on Mike" in `STATUS.md`, answer by ticking the item and writing the answer next to it (or by editing `SPEC.md` yourself), then run `npm run goal` again.

## Guardrails (enforced by tooling, SPEC §6.3)

`.claude/settings.json` registers a PreToolUse hook, [`.claude/hooks/guard.mjs`](.claude/hooks/guard.mjs). It enforces these rules:

- Agents can't edit `GOAL.md`, `SPEC.md`, the goal condition or the guard itself.
- `scenes/hashes.json` and `metrics/thresholds.json` can only be produced by their npm scripts.
- Agents can't create a `baseline-*` tag. Freezing is Mike's call.
- After `baseline-v1` exists, `harness/`, `metrics/`, `scenes/` and `baselines/` are locked.
- On `exp/*` branches, agents can only edit `sim/`, `render/` and `optlog/`.

`npm run test:guard` checks all of this in a throwaway repo. The hook binds agents only; Mike edits these files directly.

## Commands

```bash
npm run dev            # sandbox in the browser (needs WebGPU: Chrome or Safari 26)
npm run check          # typecheck + unit tests + guard tests + build
npm run machine        # print this machine's benchmark environment as JSON
```

The benchmark and gate commands listed in `PROJECT.md` (`bench`, `gates`, `calibrate`, `exp:new`, `exp:verify`) are built by the loop during M0–M3.
