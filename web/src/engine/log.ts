// Diagnostic logging — ported from the vanilla player. Always-on, prefixed +
// timestamped so glitches correlate with the rest of the console. dremote also
// POSTs to the server's /log endpoint, which appends a JSON line to
// /tmp/strudel-debug.log so you can `tail -f` the loop without screen-scraping
// the DevTools console.

const T0 = performance.now();
const ts = () => `${((performance.now() - T0) / 1000).toFixed(2)}s`;

export function dlog(category: string, ...args: unknown[]): void {
  console.log(`[${ts()}][${category}]`, ...args);
}

export function dwarn(category: string, ...args: unknown[]): void {
  console.warn(`[${ts()}][${category}]`, ...args);
}

// Console + server. Fire-and-forget; a missing server never blocks.
export function dremote(category: string, payload: unknown): void {
  console.log(`[${ts()}][${category}]`, payload);
  try {
    fetch('/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, payload }),
    }).catch(() => {});
  } catch {
    /* ignore */
  }
}
