# PROJECT.md: Fluid Lab

> Operating manual for humans and agents working in this repo. Read this first, every session.
> Why: `GOAL.md` · What: `SPEC.md` · Experiment history: `optlog/`
> (Rename to `CLAUDE.md` / `AGENTS.md` if your tooling expects that.)

## One-line purpose

A real-time 3D fluid sandbox in WebGPU (Metal later), built to prove that an AI agent loop can make it measurably faster at the same accuracy.

## Current phase

**M0: Harness skeleton.** Nothing in `sim/` or `render/` matters until the harness can time it and judge it.

| Milestone | Status |
|---|---|
| M0 Harness skeleton | ⏳ in progress |
| M1 Sim baseline (MLS-MPM) | ☐ |
| M2 Render baseline (SSFR + narrow-range filter) | ☐ |
| M3 Sandbox + freeze `baseline-v1` | ☐ |
| M4 Optimization run | ☐ |
| M5 Showcase site | ☐ |
| M6 Metal tier | ☐ |

Update this table when a milestone's definition of done in SPEC §9 is met.

## Repo map

| Path | What | Who may edit |
|---|---|---|
| `sim/` | WGSL compute kernels, dispatch | Feature work before freeze; **experimenters only** after freeze |
| `render/` | WGSL render passes | Same as `sim/` |
| `app/` | Sandbox UI, HUD, toggle, log viewer | Feature work |
| `harness/` | Headless runner, timing, readback | **Mike only.** Locked during optimization runs. |
| `metrics/` | Gate evaluators, thresholds, calibration | **Mike only.** Locked. |
| `scenes/` | Canonical scene JSON + `hashes.json` | **Mike only.** Locked. |
| `optlog/` | Experiment entries, `backlog.md`, `optlog.json` | Orchestrator, verifier |
| `baselines/` | Frozen builds | Mike, at freeze time only |

## Commands (planned; implement in M0)

```bash
npm run dev                         # sandbox in browser
npm run bench -- --scene dam-break  # perf protocol for one scene (all tiers)
npm run bench:all                   # full suite, writes results/*.json
npm run gates -- --against baseline-v1   # G0–G5 verdict
npm run calibrate                   # chaos-floor calibration → metrics/thresholds.json
npm run exp:new <slug>              # creates worktree exp/NNNN-slug + log stub
npm run exp:verify <id>             # verifier entry point: gates + bench + verdict
```

## Hard rules for agents

1. **Never edit `harness/`, `metrics/` or `scenes/`.** If you think they're wrong, write it in `optlog/backlog.md` under "Harness concerns" and stop.
2. **Never change scene parameters** (particle count, substeps, Δt, grid resolution, render resolution) to gain speed. G0 rejects it anyway.
3. **One hypothesis per experiment.** Don't bundle unrelated changes. Attribution matters more than speed.
4. **Log everything, including failures.** A rejected experiment with good notes is a useful result.
5. **Experimenters don't judge their own work.** Only the verifier issues verdicts.
6. **No unlogged changes to `sim/` or `render/` after `baseline-v1` is tagged.** This includes "trivial" cleanups.
7. **State the hypothesis before writing code.** What you expect to get faster, and why.
8. **Stay in budget.** If an experiment exceeds its time or token budget, log it as `abandoned` with what you learned.

## Definition of done: one experiment

- [ ] Hypothesis written in the log entry before implementation
- [ ] Changes confined to `sim/` and/or `render/` on `exp/NNNN-slug`
- [ ] Verifier ran G0–G5 and the 5-run performance protocol on the reference Mac
- [ ] Verdict recorded (`accepted` / `rejected` / `abandoned`) with numbers
- [ ] If accepted: merged to `optimized`, full suite re-run, `optlog.json` updated

## Code conventions

- **Particle buffers are structure of arrays.** Document every buffer's layout in a comment at its declaration.
- **Every GPU pass has a timestamp label** that matches its name in the HUD and the performance JSON.
- **No magic numbers in kernels.** Physical and scene constants come from the scene config uniform.
- **Fixed-point atomic scale factors live in one place** (`sim/fixedpoint.ts`), with their overflow bounds noted.
- **Keep WGSL portable to MSL.** Avoid browser-only tricks that have no Metal equivalent unless they are logged as such.

## Decision record

| # | Decision | Why |
|---|---|---|
| D1 | WebGPU first, Metal second; no WebGL, no Niagara | Shareable demo plus a fast headless agent loop; WGSL ports almost directly to MSL |
| D2 | MLS-MPM for the liquid baseline | No neighbor search; proven 100k–300k particle counts in browser demos |
| D3 | SSFR with a narrow-range filter for rendering | Best realism-to-cost ratio for particle liquids; keeps silhouettes |
| D4 | Fixed-point i32 atomics for P2G | WGSL has no float atomics; side benefit is run-to-run determinism |
| D5 | Gates computed from CPU snapshots | Independent of the code being optimized; reusable for the Metal build |
| D6 | v1 "optimize" means agents tuning code, not neural physics | Provable "same accuracy" claim; the neural track is P2 |
| D7 | Thresholds = max(fixed tolerance, 1.5 × chaos floor) | The fluid is chaotic; gates must not flake on legitimate changes |

Add new decisions here with a number, a date and a one-line reason. Don't rewrite old ones; supersede them.

## Reference material

- Research report: methods survey, rendering, WebGPU/Metal constraints (earlier research doc)
- Reference implementations to benchmark against, not copy: WebGPU-Ocean / Splash (matsuoka-601), Ten Minute Physics FLIP, nialltl MPM guide
- Key papers: Hu et al. 2018 (MLS-MPM), Truong & Yuksel 2018 (narrow-range filter), Ihmsen et al. 2012 (diffuse particles)
