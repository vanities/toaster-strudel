import { useEffect, useMemo, useRef } from 'react';
import { tokenize, noteRefAt } from './engine/code';
import { parseCps } from './engine/tracks';
import { setCharSpans, clearHighlights } from './engine/highlight';
import { auditionAt } from './engine/audition';

// Per-character syntax view. Each char is its own span (data-pos) so the
// highlight engine can light arbitrary source ranges by mutating styles
// directly (flashing through React state would re-render on every note).
// Shift-click → chat reference; plain click (when stopped) → audition.
export default function CodePanel({
  code,
  trackId,
  segment = 'live',
  playing,
}: {
  code: string;
  trackId: string | null;
  segment?: string;
  playing: boolean;
}) {
  const preRef = useRef<HTMLPreElement>(null);

  const classAt = useMemo(() => {
    const map = new Array<string>(code.length);
    for (const t of tokenize(code)) for (let i = t.start; i < t.end; i++) map[i] = `tk-${t.type}`;
    return map;
  }, [code]);

  // Register the rendered char spans with the highlight engine after each render.
  useEffect(() => {
    const pre = preRef.current;
    if (!pre) return;
    const spans = new Array<HTMLElement | null>(code.length).fill(null);
    pre.querySelectorAll<HTMLElement>('span[data-pos]').forEach((s) => {
      const i = Number(s.dataset.pos);
      if (Number.isInteger(i)) spans[i] = s;
    });
    setCharSpans(spans);
    clearHighlights();
  }, [code]);

  function onClick(e: React.MouseEvent<HTMLPreElement>) {
    const span = (e.target as HTMLElement).closest('span[data-pos]');
    if (!span) return;
    const offset = Number(span.getAttribute('data-pos'));
    if (!Number.isInteger(offset)) return;
    if (e.shiftKey) {
      e.preventDefault();
      const ref = noteRefAt(code, offset, trackId, segment);
      if (ref) window.dispatchEvent(new CustomEvent('strudel:note-pick', { detail: ref }));
      return;
    }
    if (!playing) void auditionAt(offset, code, parseCps(code) ?? 0.4);
  }

  return (
    <pre className="code" ref={preRef} onClick={onClick}>
      {Array.from(code, (ch, i) =>
        ch === '\n' ? (
          '\n'
        ) : (
          <span key={i} className={classAt[i] || 'tk-op'} data-pos={i}>
            {ch}
          </span>
        )
      )}
    </pre>
  );
}
