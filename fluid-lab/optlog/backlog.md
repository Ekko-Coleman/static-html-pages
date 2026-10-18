# Optimization backlog

> Owned by the orchestrator (SPEC §6.1). One hypothesis per line. The experimenter states the expected gain and why before writing code.

## Seed hypotheses (SPEC §6.5)

- [ ] Tiled P2G: accumulate in workgroup memory, flush once per node
- [ ] Sort particles by cell every N frames for memory locality
- [ ] Fuse grid clear into the grid update; fuse G2P with volume recompute
- [ ] Tune workgroup sizes per kernel
- [ ] f16 storage (`shader-f16`) for velocity and C
- [ ] Subgroup operations for reductions
- [ ] Indirect dispatch and a sparse active-block grid
- [ ] Reduce render passes: merge depth and thickness; separable narrow-range filter tuning
- [ ] Reduce CPU-side encoder and bind-group churn

## Harness concerns

<!-- PROJECT.md hard rule 1: if harness/, metrics/ or scenes/ look wrong, write it here and stop. -->
