import { useEffect, useRef } from 'react';
import { parseSections, type Section, type SectionsResponse } from './engine/tracks';

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

// The section-view counterpart to useTrackPoll: poll /sections?track=<id> (every
// tracks/<id>/NN.strudel file, returned inline) and fire onChange with the
// freshly-parsed sections whenever any of them changes on disk. Raw-text diff +
// res.ok guard so a transient fetch error never looks like a change. First read
// seeds the baseline so we don't fire on load.
export function useSectionsPoll(
  trackId: string,
  onChange: (sections: Section[]) => void,
  intervalMs = 900
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
        const res = await fetch(`/sections?track=${encodeURIComponent(trackId)}`, {
          cache: 'no-cache',
        });
        if (!res.ok || !alive) return;
        const text = await res.text();
        if (!alive) return;
        if (lastRef.current !== null && text !== lastRef.current) {
          try {
            cbRef.current(parseSections(JSON.parse(text) as SectionsResponse));
          } catch {
            /* malformed payload — skip this tick */
          }
        }
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
