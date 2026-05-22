// Per-note colours — ported from the vanilla player. Drives both the code
// highlight tint and the visualiser particles.

const PITCH_HUE = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];

const SOUND_MOD: Record<string, { s: number; l: number }> = {
  sawtooth: { s: 85, l: 55 },
  saw: { s: 85, l: 55 },
  square: { s: 90, l: 55 },
  triangle: { s: 65, l: 65 },
  sine: { s: 45, l: 70 },
  piano: { s: 70, l: 60 },
  kalimba: { s: 80, l: 65 },
  marimba: { s: 75, l: 60 },
  vibraphone: { s: 70, l: 70 },
  white: { s: 0, l: 80 },
};

const DRUM_COLOR: Record<string, string> = {
  bd: 'hsl(345, 80%, 60%)',
  sd: 'hsl(25, 85%, 60%)',
  rim: 'hsl(40, 80%, 65%)',
  cp: 'hsl(180, 75%, 60%)',
  hh: 'hsl(85, 75%, 60%)',
  oh: 'hsl(75, 70%, 70%)',
  cy: 'hsl(265, 70%, 65%)',
  sh: 'hsl(50, 60%, 70%)',
  tom: 'hsl(15, 70%, 55%)',
  perc: 'hsl(200, 70%, 65%)',
};

export function parseNote(note: unknown): { pc: number; octave: number } | null {
  if (typeof note !== 'string') return null;
  const m = note.trim().match(/^([a-gA-G])([#b]?)(-?\d+)?$/);
  if (!m) return null;
  const [, letter, acc, oct] = m;
  const base = ({ c: 0, d: 2, e: 4, f: 5, g: 7, a: 9, b: 11 } as Record<string, number>)[
    letter.toLowerCase()
  ];
  const shift = acc === '#' ? 1 : acc === 'b' ? -1 : 0;
  const pc = (base + shift + 12) % 12;
  return { pc, octave: oct != null ? parseInt(oct, 10) : 4 };
}

export interface HapValue {
  s?: string;
  note?: unknown;
  gain?: number;
  velocity?: number;
  attack?: number;
}

export function colorForHap(value: HapValue | undefined, fallback?: string): string {
  const v = value ?? {};
  const s = String(v.s ?? '').toLowerCase();
  const sBase = s.split(':')[0];
  if (DRUM_COLOR[sBase]) return DRUM_COLOR[sBase];
  const parsed = parseNote(v.note);
  if (parsed) {
    const hue = PITCH_HUE[parsed.pc];
    const mod = SOUND_MOD[sBase] || { s: 70, l: 60 };
    const lShift = (parsed.octave - 4) * 5;
    const L = Math.max(30, Math.min(80, mod.l + lShift));
    return `hsl(${hue}, ${mod.s}%, ${L}%)`;
  }
  return fallback || 'hsl(0, 0%, 70%)';
}

export function themeColor(name: string): string {
  return (
    getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim() || '#fff'
  );
}
