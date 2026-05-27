// Track + section data — fetched from the existing server (proxied by Vite).
// Pure data access; the audio engine (strudel.ts) consumes the code strings.

export interface Track {
  id: string;
  label: string;
  group?: string; // subfolder: "ep", "v2-gen", … ("" = loose top-level)
}

export interface Section {
  index: number;
  file: string;
  code: string;
  ascii: string;
  cycles: number | null;
  label: string;
}

export async function fetchTracks(): Promise<Track[]> {
  const res = await fetch('/tracks', { cache: 'no-cache' });
  if (!res.ok) throw new Error(`/tracks ${res.status}`);
  return (await res.json()) as Track[];
}

// The live working copy the player polls — tracks/<id>.strudel.
export async function loadTrackCode(id: string): Promise<string> {
  const res = await fetch(`/tracks/${encodeURIComponent(id)}.strudel`, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`failed to load track ${id} (${res.status})`);
  return res.text();
}

interface SectionManifestEntry {
  cycles?: number;
  label?: string;
}
interface SectionsResponse {
  manifest?: { sections?: SectionManifestEntry[]; slots?: SectionManifestEntry[] } | null;
  sections?: { file: string; code: string; ascii?: string }[];
}

// The server enumerates tracks/<id>/NN.strudel and returns code + ascii inline
// (no blind 404 probing). Manifest cycles/label override per-file directives.
export async function fetchSections(id: string): Promise<Section[]> {
  let data: SectionsResponse = {};
  try {
    const res = await fetch(`/sections?track=${encodeURIComponent(id)}`, { cache: 'no-cache' });
    if (res.ok) data = (await res.json()) as SectionsResponse;
  } catch {
    /* no sections */
  }
  const manSections = data.manifest?.sections ?? data.manifest?.slots;
  return (data.sections ?? []).map((s, idx) => {
    const cyclesMatch = s.code.match(/\/\/\s*@cycles\s+(\d+)/i);
    const man = manSections?.[idx] ?? null;
    const cycles = man?.cycles ?? (cyclesMatch ? parseInt(cyclesMatch[1], 10) : null);
    return {
      index: idx + 1,
      file: s.file,
      code: s.code,
      ascii: s.ascii ?? '',
      cycles,
      label: man?.label ?? `v${idx + 1}`,
    };
  });
}

export function parseCps(code: string): number | null {
  const m = code.match(/setcps\s*\(\s*([\d.]+)/);
  return m ? parseFloat(m[1]) : null;
}

export function cpsToBpm(cps: number): number {
  return Math.round(cps * 60 * 4); // 4 beats / cycle
}

// Rewrite setcps() to an absolute override cps (tempo nudge), like the vanilla
// transformCode. null = no override (passthrough).
export function transformCps(code: string, override: number | null): string {
  if (override == null) return code;
  return code.replace(/setcps\s*\(\s*([\d.]+)\s*\)/, `setcps(${override.toFixed(3)})`);
}

// First contiguous // comment line = the track/section title.
export function parseTitle(code: string): string {
  for (const raw of code.split('\n')) {
    const line = raw.trim();
    if (line.startsWith('//')) return line.replace(/^\/\/\s?/, '');
    if (line !== '') break;
  }
  return '';
}
