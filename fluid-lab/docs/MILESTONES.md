# MILESTONES.md: checklists

> SPEC §9 broken into checkable items. The `/goal` loop works top to bottom and ticks items only after verifying them.
> 👤 = only Mike can do or decide this. The loop raises it under "Blocked on Mike" in `STATUS.md` and works on other items.
> Split big items into indented sub-items when you need to. Don't delete items. If one turns out to be wrong, strike it through (`~~…~~`) and explain why in `STATUS.md`.

## M0 Harness skeleton

- [x] Repo scaffold: Vite + TypeScript + raw WebGPU, `npm run check` (typecheck, unit tests, build) passes
- [ ] 👤 Reference Mac confirmed (Q1): `harness/reference-machine.json` exists (written by `setup.sh`)
- [ ] WebGPU bootstrap in `app/`: adapter/device request with `timestamp-query` (and `shader-f16` / `subgroups` when available); clear error UI when WebGPU is missing
- [ ] GPU pass timing utility: labeled timestamp-query pairs per pass, resolved into a per-pass ms map (PROJECT code conventions: label = HUD name = JSON key)
- [ ] Toy compute kernel in `sim/` (e.g. a deterministic particle integrator using fixed-point i32 atomics) that exists only so the harness has something to time and judge
- [ ] `scenes/` format: JSON schema for scene configs (seed, particle tier, grid res, Δt, substeps, render res, camera) and a `toy` scene
- [ ] `npm run scenes:hash` writes `scenes/hashes.json`; the harness refuses to run a scene whose hash doesn't match
- [ ] Headless runner in `harness/`: Playwright launches the pinned Chromium with WebGPU enabled, loads a scene, runs N frames and returns timing JSON
- [ ] Timestamp precision verified (SPEC §5.2): document in `docs/TIMING.md` which Chrome flags give unquantized timestamps, with a test that fails if timings come back quantized
- [ ] Snapshot readback: the harness reads particle SoA buffers back at checkpoint frames and writes them as binary plus a JSON manifest
- [ ] Gate evaluator skeleton in `metrics/` (Node, CPU-only): loads two snapshot sets and implements G0 (params) and G1 (integrity), with unit tests on synthetic snapshots
- [ ] `npm run bench -- --scene toy` and `npm run gates -- --against <dir>` work end to end on the toy kernel
- [ ] Environment record: every perf JSON includes chip, GPU core count, macOS version and browser build
- [x] Guard hook verified: `npm run test:guard` shows that locked paths are refused once a `baseline-v1` tag exists (run it in a temporary repo, never tag this one)

## M1 Sim baseline (MLS-MPM)

- [ ] `sim/fixedpoint.ts`: one home for the fixed-point scale factors, with overflow bounds documented and unit-tested
- [ ] SoA particle buffers (position, velocity, C, J, volume), with the layout commented at each declaration
- [ ] Kernels: clear grid → P2G (quadratic B-spline, 3×3×3, fixed-point `atomicAdd`, stress term) → grid update (gravity, SDF boundary, brush forces) → G2P (APIC C, advect, J) → volume recompute
- [ ] Tait-style equation of state; all constants come from the scene config uniform (no magic numbers in WGSL)
- [ ] Run-to-run determinism test: two runs of the same build give bit-identical snapshots
- [ ] Canonical scenes: `dam-break`, `drop-splash`, `rotating-box`, `brush-replay` (with a recorded interaction script), all hashed
- [ ] Particle tiers 50k / 100k / 200k / 400k on a 64³ grid, 2 substeps, fixed Δt
- [ ] Gates G2 (compressibility), G3 (energy) and G4 (macro behavior: front position, settled height, center-of-mass trajectory) in `metrics/`, with unit tests
- [ ] `npm run calibrate`: chaos-floor run (positions jittered by ~1e-6 cells) writes `metrics/thresholds.json` using `max(fixed tolerance, 1.5 × chaos floor)`
- [ ] Baseline passes G0–G4 against itself on every scene

## M2 Render baseline (SSFR + narrow-range filter)

- [ ] Sphere impostors into a half-resolution linear-depth target plus an additive thickness target
- [ ] Narrow-range filter depth smoothing (Truong & Yuksel 2018)
- [ ] Shading: normals from depth, Beer–Lambert thickness absorption, Schlick Fresnel, screen-space refraction, environment-map reflection
- [ ] Density-scaled splat size and velocity stretch; ACES tonemap
- [ ] Every render pass has a timestamp label that shows up in the perf JSON
- [ ] Harness captures frames 10 and 30; gate G5 (mean ꟻLIP error) in `metrics/`, calibrated into `thresholds.json`
- [ ] Full suite (`npm run bench:all`, `npm run gates`) runs G0–G5 on all four scenes

## M3 Sandbox + freeze `baseline-v1`

- [ ] Sandbox: orbit camera; brushes (push, add fluid, remove fluid); SDF obstacle primitives
- [ ] HUD: per-pass GPU ms, fps, particle count, current build
- [ ] Baseline/Optimized toggle wiring (both point at the same build until M4)
- [ ] S1 check on the reference Mac: 100k particles at ≥60 fps, recorded in `STATUS.md` with the perf JSON path
- [ ] Competence check (SPEC §3): benchmark WebGPU-Ocean at matched particle counts on the reference Mac (check its license first; benchmark it, don't copy it); the baseline is within ~25%
- [ ] Verified in Safari 26 and Chrome on Apple Silicon
- [ ] `npm run exp:new <slug>` and `npm run exp:verify <id>` implemented; `harness/`, `metrics/` and `scenes/` checksums recorded for the anti-gaming guard (SPEC §6.3)
- [ ] `optlog/` scaffolding: entry template matching SPEC §6.4, empty `optlog.json`, `backlog.md` seeded from SPEC §6.5
- [ ] Freeze request written under "Blocked on Mike" in `STATUS.md`, listing everything Mike should review
- [ ] 👤 Mike reviews and tags `baseline-v1`, and copies the build to `baselines/baseline-v1/`

## M4 Optimization run (not part of the build-phase goal)

- [ ] 👤 Q3 answered: which agent runtime runs the loop
- [ ] 👤 Q5 confirmed: v1 "optimize" means the code-tuning track
- [ ] Orchestrator, experimenter and verifier roles wired up (SPEC §6.1), with the verifier read-only and given no shared context
- [ ] 👤 First 20 experiments supervised

## M5 Showcase site (later)

- [ ] Optimization timeline viewer, public URL, write-up

## M6 Metal tier (later)

- [ ] Swift + MSL port evaluated by the same gates
