# sim/

WGSL compute kernels and their TypeScript dispatch code (SPEC §3).

- Particle buffers are structure of arrays. Document each buffer's layout where it's declared.
- Fixed-point scale factors live only in `fixedpoint.ts`, with their overflow bounds.
- No magic numbers in kernels: constants come from the scene config uniform.
- After `baseline-v1` is tagged, change this folder only on an `exp/NNNN-slug` branch, as a logged experiment.
