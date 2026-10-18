# SPEC: Fluid Lab

Status: Draft v0.1 · Owner: Mike · See `GOAL.md` for why, `PROJECT.md` for how agents operate.

---

## 1. Overview

There are three deliverables, and they are built in this order:

1. **Benchmark harness.** It runs canonical scenes headlessly and produces performance numbers and correctness verdicts. It is built first because everything depends on it.
2. **Baseline simulator.** 3D MLS-MPM liquid with SSFR rendering and an interactive sandbox, in TypeScript and WebGPU. It is frozen as `baseline-v1`.
3. **Optimization loop and showcase.** Agents optimize against the harness. The public site shows baseline vs optimized and the full experiment log.

A Metal port follows later as the performance-ceiling tier. It uses the same scenes and the same gates.

---

## 2. Architecture

```
fluid-lab/
├── sim/            WGSL compute kernels + TS dispatch code      (optimizer-editable)
├── render/         WGSL render passes + TS pipeline              (optimizer-editable)
├── app/            Sandbox UI, brushes, HUD, toggle, log viewer  (human / feature work)
├── harness/        Headless runner, timing, snapshot readback    (LOCKED during opt runs)
├── metrics/        CPU-side gate evaluators, chaos-floor calib   (LOCKED during opt runs)
├── scenes/         Canonical scene configs (JSON) + hashes       (LOCKED during opt runs)
├── optlog/         One file per experiment + optlog.json index
├── baselines/      Frozen builds: baseline-v1/, ...
└── metal/          (Phase 6) Swift + MSL port, same scenes/gates
```

**Stack.** TypeScript, Vite and raw WebGPU with WGSL. No three.js, so every pass stays visible, labeled and timeable. Playwright drives a pinned Chrome version for headless benchmarking. Metrics are written in TypeScript and run in Node.

**Key design choice: gates are computed from CPU snapshots, not on the GPU.** The harness reads back particle state at checkpoint frames, and the metrics run on the CPU. That keeps the gates independent of the code being optimized, and lets the same evaluator judge the WebGPU and Metal builds.

---

## 3. Simulation baseline

**Method: MLS-MPM fluid (Hu et al. 2018) with APIC transfers.** It is weakly compressible, using a Tait-style equation of state.

Per substep:

1. **Clear grid.**
2. **P2G.** Quadratic B-spline weights over 3×3×3 nodes. Scatter mass and momentum, including the stress term, with **fixed-point i32 `atomicAdd`**. WGSL has no float atomics.
3. **Grid update.** Normalize momentum, add gravity, apply the SDF boundary (slip or friction), apply brush forces.
4. **G2P.** Gather velocity and the APIC matrix C, advect particles, update the deformation determinant J.
5. **Volume recompute.** Recompute particle volume (the nialltl stabilization trick).

**Baseline parameters (v1, finalized in M1):**

| Parameter | Value |
|---|---|
| Grid | 64³ dense |
| Particles | 100k default; benchmark tiers at 50k / 100k / 200k / 400k |
| Substeps | 2 per frame, fixed Δt |
| Particle layout | Structure of arrays (SoA) |

**Side effect worth exploiting: fixed-point P2G makes the scatter order-independent.** Integer addition is associative, so a single build is bit-for-bit deterministic run to run. Determinism across *different* builds is not expected (see §5.3).

**The baseline must be competent, not a strawman.** Before freezing, benchmark it on the reference Mac against a public implementation of the same method (WebGPU-Ocean) at matched particle counts. It must be within ~25% of that implementation, or the 2× claim is meaningless. Check reference-code licenses before borrowing anything. The default is a clean-room implementation.

---

## 4. Rendering baseline

| Element | Choice |
|---|---|
| Particles | Sphere impostors written to a linear depth target and an additive thickness target, at half resolution |
| Depth smoothing | **Narrow-range filter** (Truong & Yuksel 2018) |
| Shading | Normals from depth derivatives; Beer–Lambert absorption from thickness; Schlick Fresnel; screen-space refraction of the background; environment map reflection |
| Splats | Density-scaled particle size, velocity stretch |
| Post | ACES tonemap |

Every pass gets a timestamp-query label so the harness reports per-pass GPU time.

---

## 5. Benchmark harness & metrics

### 5.1 Canonical scenes (locked, hashed)

| Scene | What it stresses |
|---|---|
| `dam-break` | Bulk flow, impact, settling. Main macro-behavior check. |
| `drop-splash` | Thin sheets, high velocity, near-surface rendering cost |
| `rotating-box` | Sustained vorticity, wall boundaries, long-run stability |
| `brush-replay` | A recorded user-interaction script, so interactive paths are covered |

Each scene config fixes the seed, particle count tier, grid resolution, Δt, substeps, render resolution and camera. The harness refuses to run if a config hash doesn't match `scenes/hashes.json`.

### 5.2 Performance metrics

**Protocol.** 120-frame warm-up, then 600 measured frames, repeated 5 runs per scene and tier.

**Measured per run:**
- GPU time per pass (timestamp-query)
- Total GPU frame time: median and p95
- Wall-clock frame time
- Max particle tier sustained at ≤16.6 ms

**Headline number:** geometric mean across scenes of the median frame-time speedup vs `baseline-v1`. Sim and render speedups are reported separately as well as combined.

**Environment control:**
- Pinned Chrome build via Playwright
- AC power
- Fixed window size
- Cool-down between runs
- Every log entry records chip, GPU core count, macOS version and browser build

**Timestamp precision.** Chrome may quantize timestamp-query results. M0 must verify how to get full precision in the harness browser, using developer flags if needed.

### 5.3 Correctness gates (all must pass to accept a change)

The fluid is chaotic, so per-particle comparison between builds is meaningless after a few dozen frames. The gates use aggregate and early-time metrics instead. Thresholds are calibrated against a **chaos floor**: run the baseline against itself with initial positions jittered by ~1e-6 cells, and measure how far it diverges. A gate's threshold is `max(fixed tolerance, 1.5 × chaos floor)`.

| Gate | Check | Initial tolerance (calibrate in M1) |
|---|---|---|
| G0 Params | Scene hash, particle count, substeps, Δt, grid and render resolution unchanged | Exact |
| G1 Integrity | Particle count and total mass conserved; zero NaN/Inf | Exact |
| G2 Compressibility | Time-averaged mean of \|J − 1\| (frames 60–600) | ≤ baseline × 1.10 |
| G3 Energy | Total energy (kinetic + potential) curve, RMS difference over frames 0–120, plus settled energy | ±5% |
| G4 Macro behavior | Dam-break front position at t = 0.5 s; settled free-surface height; center-of-mass trajectory | ±3% / ±2% / ≤ chaos-floor bound |
| G5 Visual | Mean ꟻLIP image error vs the baseline render at frames 10 and 30 | ≤ calibrated floor × 1.5 |

### 5.4 Acceptance rule

A change is accepted only if **all gates pass** AND the speedup is **≥ 2%** AND the bootstrap 95% confidence interval of the speedup lies **entirely above 1.0**.

---

## 6. Optimization loop

### 6.1 Roles

| Role | Can edit | Responsibility |
|---|---|---|
| **Orchestrator** | `optlog/backlog.md` | Keeps the hypothesis backlog, picks the next experiment, enforces budgets |
| **Experimenter** (one per experiment, own git worktree) | `sim/`, `render/` only | Implements one hypothesis |
| **Verifier** (independent agent; has no access to the experimenter's reasoning) | Nothing (read-only) | Runs gates and benchmarks, issues the verdict |
| **Mike** | Harness, gates, thresholds, baselines | Freezes baselines, reviews accepted diffs weekly. **Never edits `sim/` or `render/` in the optimized track.** |

### 6.2 Experiment protocol

1. The orchestrator picks a hypothesis from the backlog, or the experimenter proposes one with a written rationale.
2. The experimenter implements it on branch `exp/NNNN-slug`, staying within a time and token budget.
3. The verifier runs G0–G5 and the performance protocol.
4. **Accepted:** merge into `optimized`, write the log entry, and run the full suite again on the new head.
5. **Rejected:** write the log entry anyway, with the reason and the numbers. The branch is archived, not deleted.

The first ~20 experiments are supervised: Mike reviews each verdict. After that the loop runs autonomously, and Mike audits weekly.

### 6.3 Guardrails against gaming

- `harness/`, `metrics/` and `scenes/` are checksummed. Any experiment that touches them, or changes their checksums, is auto-rejected.
- Scene parameters are runtime-asserted by G0. "Faster because it simulates less" is impossible by construction.
- The verifier is a separate agent with read-only access and no shared context.
- Mike audits every accepted diff in plain language: "what did this actually change?"

### 6.4 Log format (`optlog/NNNN-slug.md` and an entry in `optlog.json`)

```yaml
id: 0007
slug: tiled-p2g-workgroup-accum
date: 2026-11-02
hypothesis: Accumulate P2G in workgroup memory per tile, flush once per node
files: [sim/p2g.wgsl, sim/dispatch.ts]
commit: abc1234
agent: { model: ..., role: experimenter, tokens: ..., wall_min: ... }
gates: { G0: pass, G1: pass, G2: pass, G3: pass, G4: pass, G5: pass }
perf:
  dam-break:   { base_ms: 9.8, new_ms: 7.1, speedup: 1.38, ci95: [1.34, 1.41] }
  ...
verdict: accepted
notes: ...
```

### 6.5 Seed backlog (initial hypotheses)

- Tiled P2G: accumulate in workgroup memory, flush once per node
- Sort particles by cell every N frames for memory locality
- Fuse grid clear into the grid update; fuse G2P with volume recompute
- Tune workgroup sizes per kernel
- f16 storage (`shader-f16`) for velocity and C
- Subgroup operations for reductions
- Indirect dispatch and a sparse active-block grid
- Reduce render passes: merge depth and thickness; separable narrow-range filter tuning
- Reduce CPU-side encoder and bind-group churn

---

## 7. Showcase app

**P0:**
- Sandbox with brushes (push, add fluid, remove fluid), SDF obstacle primitives and an orbit camera
- **Baseline / Optimized toggle.** Both builds ship. Toggling re-initializes the same scene and state.
- HUD: per-pass GPU ms, fps, particle count, current build
- **Optimization timeline.** A frame-time chart across accepted experiments. Each point opens that experiment's log entry and diff.

**P1:**
- Scrub mode: load any intermediate commit's build
- Split-screen race mode
- Short write-up page

---

## 8. Requirements

### P0 (v1 cannot ship without these)
- [ ] Harness runs all four scenes headlessly with locked configs, and emits performance JSON plus a gate verdict
- [ ] Chaos-floor calibration script, with thresholds stored in `metrics/thresholds.json`
- [ ] Baseline MLS-MPM and SSFR meet S1, and pass the competence check (§3)
- [ ] Loop protocol, roles and guardrails (§6) enforced by tooling, not just convention
- [ ] Showcase P0 features (§7) live at a public URL

### P1 (fast follow)
- [ ] Ihmsen diffuse particles (spray, foam, bubbles) as `baseline-v2`, with a fresh optimization run
- [ ] Metal port. The same harness gates evaluate its snapshots.
- [ ] Rigid-body two-way coupling via node momentum exchange

### P2 (keep the architecture open for these)
- [ ] Smoke/fire MAC-grid module (MacCormack, advection-reflection, MGPCG)
- [ ] Neural track: learned pressure preconditioner on Metal (MPSGraph / Core ML), with its own gates
- [ ] Leapfrog Flow Maps "research mode"

---

## 9. Milestones (estimates are guesses)

| Milestone | Scope | Est. |
|---|---|---|
| **M0 Harness skeleton** | Repo, WebGPU bootstrap, Playwright runner, timestamp precision verified, snapshot readback, gate evaluator on a toy kernel | 1 wk |
| **M1 Sim baseline** | MLS-MPM, four scenes, G0–G4, chaos-floor calibration | 2 wk |
| **M2 Render baseline** | SSFR, narrow-range filter, shading, G5 | 1–2 wk |
| **M3 Sandbox + freeze** | Brushes, obstacles, HUD, competence check, tag `baseline-v1` | 1 wk |
| **M4 Optimization run** | 20 supervised experiments, then autonomous | 2–4 wk |
| **M5 Showcase** | Public site, timeline viewer, write-up | 1–2 wk |
| **M6 Metal tier** | Port plus cross-backend comparison | 2–3 wk |

---

## 10. Risks

| Risk | Mitigation |
|---|---|
| Metric gaming / Goodhart | Locked params, checksummed harness, independent verifier, human diff audit |
| Weak baseline inflates the claim | Competence check against a public implementation before the freeze |
| Measurement noise (thermals, browser updates) | Pinned browser, 5 runs, bootstrap confidence intervals, environment recorded per entry |
| Chaotic divergence makes gates flaky | Chaos-floor calibration; early-time and aggregate metrics only |
| Safari behaves differently from Chrome | Benchmark in Chrome; verify the showcase in Safari each milestone |
| Timestamp quantization hides small wins | Verify precision in M0; the 2% minimum effect size |

---

## 11. Open questions

| # | Question | Owner | Blocking? |
|---|---|---|---|
| Q1 | Which Mac is the reference machine (chip, GPU cores)? | Mike | Yes, for M0 numbers |
| Q2 | Who is the showcase audience: public, or internal leadership? This affects polish and the write-up. | Mike | No |
| Q3 | Which agent runtime runs the loop: Claude Code headless, or a custom orchestrator? | Mike | Yes, for M4 |
| Q4 | Does the headline report sim and render speedups combined or separately? (Recommendation: both, sim-only as the headline.) | Mike | No |
| Q5 | Confirm "optimize" = the code-tuning track for v1 (assumed in GOAL.md). | Mike | Yes |
