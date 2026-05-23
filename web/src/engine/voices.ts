// Per-voice particle field — ported from the vanilla player. Each distinct
// pattern voice (by source location) gets a fixed angular position; the
// highlight tap calls registerVoiceHit on every note, and the viz draws them.

import { colorForHap, type HapValue } from './color';

const VOICE_PALETTE = [
  '#9b6dff', '#5dd0ff', '#ff8a3d', '#5dffb1',
  '#ff7ad9', '#ffd56b', '#b16dff', '#6dffd0',
  '#ff5d8f', '#5dffe6', '#ffae5d', '#a5ff5d',
];

interface Voice {
  angle: number;
  color: string;
  lastHit: number;
  hits: number;
  intensity: number;
}
interface Particle {
  radius: number;
  speed: number;
  drift: number;
  life: number;
  decay: number;
  color: string;
  size: number;
  spawnAng: number;
}

export const voiceMap = new Map<string, Voice>();
const particles: Particle[] = [];
const PARTICLE_MAX = 800;

function spawnParticle(voice: Voice, gain: number, color: string) {
  if (particles.length >= PARTICLE_MAX) return;
  const speed = 0.6 + Math.random() * 1.4 + gain * 1.0;
  const spread = 0.35;
  particles.push({
    radius: 0,
    speed,
    drift: (Math.random() - 0.5) * 0.015,
    life: 1,
    decay: 0.012 + Math.random() * 0.008,
    color: color || voice.color,
    size: 1.5 + Math.random() * 2.8,
    spawnAng: voice.angle + (Math.random() - 0.5) * spread,
  });
}

export function registerVoiceHit(loc: { start: number; end: number }, value: HapValue) {
  const key = `${loc.start}-${loc.end}`;
  let v = voiceMap.get(key);
  const fallback = VOICE_PALETTE[voiceMap.size % VOICE_PALETTE.length];
  const hapColor = colorForHap(value, fallback);
  if (!v) {
    const i = voiceMap.size;
    v = { angle: i * 2.399963, color: hapColor, lastHit: 0, hits: 0, intensity: 0 };
    voiceMap.set(key, v);
  }
  v.color = hapColor;
  v.lastHit = performance.now();
  v.hits++;
  v.intensity = Math.min(1, v.intensity + 0.4);
  const gain = (value.gain ?? 0.4) * (value.velocity ?? 1);
  const n = Math.min(6, 1 + Math.floor(gain * 6));
  for (let k = 0; k < n; k++) spawnParticle(v, gain, hapColor);
}

export function drawVoiceField(ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement) {
  const cssW = canvas.clientWidth;
  const cssH = canvas.clientHeight;
  const cx = cssW / 2;
  const cy = cssH / 2;
  const rMax = Math.min(cssW, cssH) * 0.48;

  ctx.globalCompositeOperation = 'destination-out';
  ctx.fillStyle = 'rgba(0,0,0,0.12)';
  ctx.fillRect(0, 0, cssW, cssH);
  ctx.globalCompositeOperation = 'lighter';
  ctx.shadowBlur = 0;

  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.radius += p.speed;
    p.spawnAng += p.drift;
    p.life -= p.decay;
    if (p.life <= 0 || p.radius > rMax) {
      particles.splice(i, 1);
      continue;
    }
    const x = cx + Math.cos(p.spawnAng) * p.radius;
    const y = cy + Math.sin(p.spawnAng) * p.radius;
    ctx.globalAlpha = p.life;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(x, y, p.size * p.life, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';

  const now = performance.now();
  for (const [key, v] of voiceMap) {
    const age = (now - v.lastHit) / 1000;
    // Prune dead voices instead of skipping them. Keys are source locations,
    // so every section advance / live edit / track switch mints new ones; without
    // this the map (and the per-frame loops over it) grow for the whole session.
    if (age > 8) {
      voiceMap.delete(key);
      continue;
    }
    const liveness = Math.max(0, 1 - age / 8);
    v.intensity *= 0.96;
    const r = 24 + liveness * 6;
    const arcLen = 0.25 + v.intensity * 0.4;
    ctx.strokeStyle = v.color;
    ctx.lineWidth = 1.4 + v.intensity * 2;
    ctx.globalAlpha = 0.4 + liveness * 0.6;
    ctx.beginPath();
    ctx.arc(cx, cy, r, v.angle - arcLen, v.angle + arcLen);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;
}

export function activeVoiceCount(): number {
  const now = performance.now();
  let n = 0;
  for (const v of voiceMap.values()) if (now - v.lastHit < 8000) n++;
  return n;
}
