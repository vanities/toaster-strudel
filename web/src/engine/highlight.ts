// Live highlight tap — ported from the vanilla player. Monkey-patches the
// Strudel scheduler's setPattern so every evaluated pattern gets an onTrigger
// side-effect that lights up the matching source characters as they play.
//
// Operates directly on the code panel's per-char spans (registered by
// CodePanel) — flashing through React state would re-render on every note.

import { colorForHap, type HapValue } from './color';
import { registerVoiceHit } from './voices';

let charSpans: (HTMLElement | null)[] = [];
const timers = new WeakMap<HTMLElement, number>();

export function setCharSpans(spans: (HTMLElement | null)[]) {
  charSpans = spans;
}

const HELD_MIN_SEC = 0.5;
const GAIN_FULL = 0.55;

interface FlashOpts {
  durSec?: number;
  gain?: number;
  attackSec?: number;
  beatSec?: number;
  pulseDelay?: number;
}

export function flashRange(start: number, end: number, color: string, opts: FlashOpts = {}) {
  const { durSec = 0, gain = 0.4, attackSec = 0, beatSec = 0.6, pulseDelay = 0 } = opts;
  const held = durSec >= HELD_MIN_SEC;
  const intensity = Math.max(0, Math.min(1, gain / GAIN_FULL));
  const attackDur = Math.max(0, Math.min(attackSec, durSec));
  for (let i = start; i < end; i++) {
    const span = charSpans[i];
    if (!span) continue;
    if (color) span.style.setProperty('--lit', color);
    span.style.setProperty('--intensity', intensity.toFixed(3));
    const prev = timers.get(span);
    if (prev) {
      clearTimeout(prev);
      timers.delete(span);
    }
    span.classList.remove('lit', 'held');
    void span.offsetWidth; // restart animation
    if (held) {
      span.style.setProperty('--held-dur', `${beatSec.toFixed(3)}s`);
      span.style.setProperty('--attack-dur', `${attackDur.toFixed(3)}s`);
      span.style.setProperty('--pulse-delay', `${pulseDelay.toFixed(3)}s`);
      span.classList.add('held');
      timers.set(
        span,
        window.setTimeout(() => {
          span.classList.remove('held');
          timers.delete(span);
        }, durSec * 1000)
      );
    } else {
      span.classList.add('lit');
      timers.set(
        span,
        window.setTimeout(() => {
          span.classList.remove('lit');
          timers.delete(span);
        }, 500)
      );
    }
  }
}

export function clearHighlights() {
  for (const span of charSpans) {
    if (!span) continue;
    const prev = timers.get(span);
    if (prev) {
      clearTimeout(prev);
      timers.delete(span);
    }
    span.classList.remove('lit', 'held');
  }
}

interface Hap {
  context?: { locations?: { start: number; end: number }[] };
  value?: HapValue;
  whole?: { begin: number; end: number };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Pattern = any;

function buildTap(pattern: Pattern): Pattern {
  if (!pattern || pattern.__tapped) return pattern;
  const tapped = pattern.onTrigger(
    (hap: Hap, _now: number, cps: number, targetTime: number) => {
      try {
        const locs = hap?.context?.locations || [];
        const value = hap?.value || {};
        const color = colorForHap(value);
        let durSec = 0;
        if (hap?.whole && cps > 0) durSec = (Number(hap.whole.end) - Number(hap.whole.begin)) / cps;
        const gain = (value.gain ?? 0.4) * (value.velocity ?? 1);
        const attackSec = Number(value.attack) || 0;
        const beatSec = cps > 0 ? 1 / (cps * 4) : 0.5;
        let pulseDelay = 0;
        if (cps > 0 && Number.isFinite(targetTime)) {
          const beatPhase = (((targetTime * cps * 4) % 1) + 1) % 1;
          pulseDelay = -beatPhase * beatSec;
        }
        for (const loc of locs) flashRange(loc.start, loc.end, color, { durSec, gain, attackSec, beatSec, pulseDelay });
        if (locs.length) registerVoiceHit(locs[0], value);
      } catch {
        /* ignore one bad hap */
      }
    },
    false
  );
  tapped.__tapped = true;
  return tapped;
}

// Patch scheduler.setPattern so the tap is applied inside the single
// setPattern call evaluate makes (avoids a second pattern swap → audible gap).
export function setupHighlightTap(scheduler: Pattern) {
  if (!scheduler || scheduler.__patched) return;
  const orig = scheduler.setPattern.bind(scheduler);
  scheduler.setPattern = (pattern: Pattern, autoStart: boolean) => orig(buildTap(pattern), autoStart);
  scheduler.__patched = true;
  if (scheduler.pattern && !scheduler.pattern.__tapped) scheduler.setPattern(scheduler.pattern, false);
}
