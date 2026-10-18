# GOAL: Fluid Lab (working name)

## North star

Show, with evidence anyone can check, that an autonomous AI agent loop can make a real-time 3D fluid simulation on a Mac substantially faster without making it less physically accurate.

## The claim we want to be able to make

> "Starting from a frozen, competent baseline, agents ran **N** experiments unattended and kept **K** of them. The simulation got **X× faster at the same measured accuracy**. Here is every change, every number, and a live toggle so you can see both versions."

Every decision in this project should make that sentence more true or more believable.

## What "optimize" means here

**Primary track: agents optimize the code.** Same physics, same scenes, same parameters. Faster kernels, better memory layouts, fewer dispatches. This is provable, so it is the headline.

**Stretch track: AI inside the physics.** For example, a learned pressure preconditioner or a neural surrogate. It is out of scope for v1 because it is much harder to prove "same accuracy."

## Success criteria (v1)

| # | Criterion | Target | Stretch |
|---|---|---|---|
| S1 | **Baseline exists and is competent.** 3D MLS-MPM liquid with screen-space rendering in the browser via WebGPU, frozen and tagged `baseline-v1`. | 100k particles at ≥60 fps on the reference Mac | — |
| S2 | **Speedup.** Median frame time (sim + render) across the benchmark suite, optimized vs baseline. | ≥ 2.0× | ≥ 3.0× |
| S3 | **No accuracy regression.** Every accepted change passes every correctness gate (SPEC §5.3). | 100% | — |
| S4 | **Attribution integrity.** Every gain traces to a logged loop experiment. No human edits to sim or render code after the freeze. | 100% | — |
| S5 | **Viewable.** Public URL with a live baseline/optimized toggle, a frame-time HUD and an optimization-log viewer. Works in Safari 26 and Chrome on Apple Silicon. | Ships | Split-screen race mode |
| S6 | **Reproducible.** Anyone can re-run the benchmark on the same hardware class and land within ±10% of the published numbers. | Yes | — |

The 2× target is a hypothesis, not a known result. The known headroom suggests it is plausible: tiled P2G, kernel fusion, f16 storage, cell-sorted particles and fewer dispatches. Record the actual outcome honestly, including if it is lower.

## Non-goals

- **New physics.** Use proven methods only: MLS-MPM and SSFR with a narrow-range filter.
- **Neural or learned solvers in v1.** They go in the stretch track.
- **Film-quality or offline realism.** The bar is "convincing in real time."
- **Unreal / Niagara integration.** The showcase needs a fast headless loop and a shareable link.
- **WebGL fallback.** It has no compute shaders or atomics.
- **Mobile performance targets.** It is fine if it happens to run on iPad.

## Guiding principles

1. **Measured or it didn't happen.** No claim without a logged number.
2. **The harness is the product.** If the metrics can be gamed, the showcase is worthless.
3. **Freeze, then optimize.** New features go into a new baseline version (`baseline-v2`), never into the optimized track mid-run.
4. **Browser first for reach, Metal for the ceiling.**
5. **Negative results are part of the story.** Rejected experiments are logged too.
