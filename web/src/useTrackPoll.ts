import { useEffect, useRef } from 'react';

// Mirrors the vanilla player's pollForChanges: poll tracks/<id>.strudel and
// fire onChange when the file content changes on disk (e.g. after the chat
// edits it). The first read just seeds the baseline so we don't fire on load.
export function useTrackPoll(
  trackId: string,
  onChange: (code: string) => void,
  intervalMs = 700
) {
  const lastRef = useRef<string | null>(null);
  const cbRef = useRef(onChange);
  cbRef.current = onChange;

  useEffect(() => {
    if (!trackId) return;
    lastRef.current = null; // reset baseline on track switch
    let alive = true;
    const tick = async () => {
      try {
        const res = await fetch(`/tracks/${encodeURIComponent(trackId)}.strudel`, {
          cache: 'no-cache',
        });
        if (!res.ok || !alive) return;
        const text = await res.text();
        if (!alive) return;
        if (lastRef.current !== null && text !== lastRef.current) cbRef.current(text);
        lastRef.current = text;
      } catch {
        /* transient — try again next tick */
      }
    };
    const h = setInterval(tick, intervalMs);
    return () => {
      alive = false;
      clearInterval(h);
    };
  }, [trackId, intervalMs]);
}
