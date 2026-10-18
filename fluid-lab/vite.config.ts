import { defineConfig } from 'vitest/config';

export default defineConfig({
  // WGSL sources are imported with `?raw`, so no shader plugin is needed.
  build: { target: 'es2022', outDir: 'dist' },
  test: {
    include: ['**/*.test.{ts,mjs}'],
    exclude: ['node_modules/**', 'dist/**', 'baselines/**'],
  },
});
