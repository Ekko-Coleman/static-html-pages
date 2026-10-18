// Placeholder entry. M0 replaces this with the real WebGPU bootstrap (see docs/MILESTONES.md).
const status = document.querySelector<HTMLDivElement>('#status')!;

async function main(): Promise<void> {
  if (!navigator.gpu) {
    status.textContent = 'WebGPU is not available in this browser.';
    return;
  }
  const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
  if (!adapter) {
    status.textContent = 'No WebGPU adapter found.';
    return;
  }
  const features = ['timestamp-query', 'shader-f16', 'subgroups'].filter((f) => adapter.features.has(f));
  status.textContent = `WebGPU ready · ${adapter.info.vendor || 'unknown vendor'} ${adapter.info.architecture} · ${features.join(', ') || 'no optional features'}`;
}

main().catch((err: unknown) => {
  status.textContent = `WebGPU init failed: ${String(err)}`;
});
