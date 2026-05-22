import { useEffect, useRef, useState } from 'react';

// Hum → Melody — ported from player/hum.html. Mic → autocorrelation pitch
// detection → live waveform/spectrum/pitch-trail → on stop, smooth + quantize
// to a grid/scale → a Strudel pattern. Uses its own AudioContext (independent
// of the player engine). High-frequency readouts write to refs, not state.

const NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const midiToName = (m: number) => NOTES[((m % 12) + 12) % 12] + (Math.floor(m / 12) - 1);
const freqToMidi = (f: number) => 12 * Math.log2(f / 440) + 69;
const SCALES: Record<string, number[] | null> = {
  chromatic: null,
  'C# major': [1, 3, 5, 6, 8, 10, 0],
  'C minor': [0, 2, 3, 5, 7, 8, 10],
};

function snapMidi(midi: number, name: string): number {
  const sc = SCALES[name];
  if (!sc) return midi;
  const pc = ((midi % 12) + 12) % 12;
  let best = sc[0];
  let bd = 99;
  for (const t of sc) {
    const d = Math.min(Math.abs(pc - t), 12 - Math.abs(pc - t));
    if (d < bd) {
      bd = d;
      best = t;
    }
  }
  let cand = midi - pc + best;
  if (cand - midi > 6) cand -= 12;
  else if (midi - cand > 6) cand += 12;
  return cand;
}

function autoCorrelate(b: Float32Array, rate: number): number {
  const SIZE = b.length;
  let rms = 0;
  for (let i = 0; i < SIZE; i++) rms += b[i] * b[i];
  rms = Math.sqrt(rms / SIZE);
  if (rms < 0.004) return -1;
  let r1 = 0;
  let r2 = SIZE - 1;
  const thr = 0.2;
  for (let i = 0; i < SIZE / 2; i++) if (Math.abs(b[i]) < thr) { r1 = i; break; }
  for (let i = 1; i < SIZE / 2; i++) if (Math.abs(b[SIZE - i]) < thr) { r2 = SIZE - i; break; }
  const s = b.slice(r1, r2);
  const n = s.length;
  const c = new Float32Array(n);
  for (let i = 0; i < n; i++) for (let j = 0; j < n - i; j++) c[i] += s[j] * s[j + i];
  let d = 0;
  while (d < n - 1 && c[d] > c[d + 1]) d++;
  let maxv = -1;
  let maxp = -1;
  for (let i = d; i < n; i++) if (c[i] > maxv) { maxv = c[i]; maxp = i; }
  let T = maxp;
  const x1 = c[T - 1] || 0;
  const x2 = c[T];
  const x3 = c[T + 1] || 0;
  const a = (x1 + x3 - 2 * x2) / 2;
  const b2 = (x3 - x1) / 2;
  if (a) T = T - b2 / (2 * a);
  const f = rate / T;
  return f > 60 && f < 1500 ? f : -1;
}

const median = (arr: number[]) => {
  const a = [...arr].sort((x, y) => x - y);
  return a[a.length >> 1];
};

interface Sample {
  t: number;
  midi: number | null;
}
interface Evt {
  midi: number | null;
  start: number;
  end: number;
}
interface NoteRow {
  name: string;
  start: number;
  dur: number;
  steps: number;
}
interface Captured {
  snippet: string;
  notes: NoteRow[];
}

function smoothToEvents(samples: Sample[]): Evt[] | null {
  if (samples.filter((s) => s.midi != null).length < 3) return null;
  const W = 2;
  const sm = samples.map((s, i) => {
    const win: number[] = [];
    for (let k = -W; k <= W; k++) {
      const v = samples[i + k];
      if (v && v.midi != null) win.push(v.midi);
    }
    return { t: s.t, midi: win.length ? median(win) : null };
  });
  const HOLD = 5;
  let held: number | null = null;
  let pend: number | null = null;
  let pc = 0;
  const stable = sm.map((s) => {
    if (s.midi === held) {
      pend = null;
      pc = 0;
    } else if (s.midi === pend) {
      if (++pc >= HOLD) {
        held = pend;
        pend = null;
        pc = 0;
      }
    } else {
      pend = s.midi;
      pc = 1;
    }
    return { t: s.t, midi: held };
  });
  const events: Evt[] = [];
  let cur: Evt | null = null;
  for (const s of stable) {
    if (!cur || s.midi !== cur.midi) {
      if (cur) {
        cur.end = s.t;
        events.push(cur);
      }
      cur = { midi: s.midi, start: s.t, end: s.t };
    }
  }
  if (cur) {
    cur.end = stable[stable.length - 1].t;
    events.push(cur);
  }
  const MIN = 0.09;
  const clean = events.map((e) => (e.midi != null && e.end - e.start < MIN ? { ...e, midi: null } : e));
  const merged: Evt[] = [];
  for (const e of clean) {
    const last = merged[merged.length - 1];
    if (last && last.midi === e.midi) last.end = e.end;
    else merged.push({ ...e });
  }
  return merged;
}

function quantize(raw: Evt[], bpm: number, spb: number, scale: string): Captured | null {
  if (!raw.length) return null;
  const step = 60 / bpm / spb;
  const total = raw[raw.length - 1].end;
  const nSteps = Math.max(1, Math.round(total / step));
  const grid = new Array<string>(nSteps).fill('~');
  const rows: NoteRow[] = [];
  for (const e of raw) {
    if (e.midi == null) continue;
    const a = Math.round(e.start / step);
    const b = Math.max(a + 1, Math.round(e.end / step));
    const name = midiToName(snapMidi(e.midi, scale));
    for (let i = a; i < Math.min(nSteps, b); i++) grid[i] = name;
    rows.push({ name, start: e.start, dur: e.end - e.start, steps: b - a });
  }
  const toks: string[] = [];
  for (let i = 0; i < nSteps; ) {
    let j = i + 1;
    while (j < nSteps && grid[j] === grid[i]) j++;
    const w = j - i;
    toks.push(w > 1 ? `${grid[i]}@${w}` : grid[i]);
    i = j;
  }
  const gName = ({ 1: '1/4', 2: '1/8', 4: '1/16', 8: '1/32' } as Record<number, string>)[spb] || `${spb}/beat`;
  const pattern = `note("${toks.join(' ')}")`;
  const snippet =
    `setcps(${bpm}/60/4)\n${pattern}\n  .slow(${(nSteps / (spb * 4)).toFixed(2)})        // ${nSteps} steps @ ${gName}` +
    (scale !== 'chromatic' ? `, snapped to ${scale}` : '') +
    `\n  .s("sawtooth").attack(0.02).release(0.4).gain(0.3).room(0.4)`;
  return { snippet, notes: rows };
}

export default function Hum({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [micReady, setMicReady] = useState(false);
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState('click Enable mic, then Record and hum');
  const [result, setResult] = useState<Captured | null>(null);
  const [bpm, setBpm] = useState(144);
  const [grid, setGrid] = useState(4);
  const [scale, setScale] = useState('chromatic');
  const [boost, setBoost] = useState(8);

  const wave = useRef<HTMLCanvasElement>(null);
  const spectrum = useRef<HTMLCanvasElement>(null);
  const trail = useRef<HTMLCanvasElement>(null);
  const noteNow = useRef<HTMLDivElement>(null);

  const ac = useRef<AudioContext | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const inGain = useRef<GainNode | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const recordingRef = useRef(false);
  const samples = useRef<Sample[]>([]);
  const live = useRef<Sample[]>([]);
  const rawCapture = useRef<Evt[] | null>(null);
  const recStart = useRef(0);
  const rafId = useRef(0);

  const ctrl = useRef({ bpm, grid, scale });
  ctrl.current = { bpm, grid, scale };

  // stop everything when the panel closes
  useEffect(() => {
    if (open) return;
    cancelAnimationFrame(rafId.current);
    stream.current?.getTracks().forEach((t) => t.stop());
    ac.current?.close().catch(() => {});
    ac.current = null;
    analyser.current = null;
    stream.current = null;
    recordingRef.current = false;
    setMicReady(false);
    setRecording(false);
    setResult(null);
  }, [open]);

  function loop() {
    const an = analyser.current;
    const context = ac.current;
    if (!an || !context) return;
    const buf = new Float32Array(an.fftSize);
    const freqBuf = new Uint8Array(an.frequencyBinCount);
    an.getFloatTimeDomainData(buf);
    an.getByteFrequencyData(freqBuf);
    const f = autoCorrelate(buf, context.sampleRate);
    let midi: number | null = null;
    if (f > 0) {
      const m = freqToMidi(f);
      midi = Math.round(m);
      if (noteNow.current) noteNow.current.textContent = midiToName(midi);
    } else if (noteNow.current) {
      noteNow.current.textContent = '—';
    }
    const now = context.currentTime;
    live.current.push({ t: now, midi });
    if (live.current.length > 700) live.current.shift();
    if (recordingRef.current) samples.current.push({ t: now - recStart.current, midi });
    drawWave(buf);
    drawSpectrum(freqBuf);
    drawTrail();
    rafId.current = requestAnimationFrame(loop);
  }

  function drawWave(buf: Float32Array) {
    const cv = wave.current;
    const ctx = cv?.getContext('2d');
    if (!cv || !ctx) return;
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.strokeStyle = '#7bd88f';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    const step = buf.length / cv.width;
    const mid = cv.height / 2;
    for (let x = 0; x < cv.width; x++) {
      const v = buf[Math.floor(x * step)] || 0;
      const y = mid - v * mid * 0.95;
      x ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    }
    ctx.stroke();
  }
  function drawSpectrum(freqBuf: Uint8Array) {
    const cv = spectrum.current;
    const ctx = cv?.getContext('2d');
    if (!cv || !ctx) return;
    const grad = ctx.createLinearGradient(0, cv.height, 0, 0);
    grad.addColorStop(0, '#5a2bd0');
    grad.addColorStop(0.6, '#9b6dff');
    grad.addColorStop(1, '#e3556e');
    ctx.clearRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = grad;
    const bins = 256;
    const bw = cv.width / bins;
    for (let i = 0; i < bins; i++) {
      const h = (freqBuf[i] / 255) ** 2 * cv.height;
      ctx.fillRect(i * bw, cv.height - h, bw * 0.8, h);
    }
  }
  function drawTrail() {
    const cv = trail.current;
    const ctx = cv?.getContext('2d');
    if (!cv || !ctx) return;
    ctx.clearRect(0, 0, cv.width, cv.height);
    const l = live.current;
    if (l.length < 2) return;
    const t0 = l[0].t;
    const span = Math.max(0.5, l[l.length - 1].t - t0);
    const ms = l.filter((s) => s.midi != null).map((s) => s.midi as number);
    const lo = (ms.length ? Math.min(...ms) : 48) - 3;
    const hi = (ms.length ? Math.max(...ms) : 72) + 3;
    ctx.fillStyle = recordingRef.current ? '#e3556e' : '#9b6dff';
    for (const s of l) {
      if (s.midi == null) continue;
      const x = ((s.t - t0) / span) * cv.width;
      const y = cv.height - ((s.midi - lo) / Math.max(1, hi - lo)) * cv.height;
      ctx.beginPath();
      ctx.arc(x, y, 2.4, 0, 7);
      ctx.fill();
    }
  }

  async function enableMic() {
    try {
      setStatus('requesting mic… allow the prompt');
      stream.current = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false },
      });
      const context = new AudioContext();
      ac.current = context;
      const an = context.createAnalyser();
      an.fftSize = 2048;
      an.smoothingTimeConstant = 0.75;
      analyser.current = an;
      const src = context.createMediaStreamSource(stream.current);
      const g = context.createGain();
      g.gain.value = boost;
      inGain.current = g;
      src.connect(g);
      g.connect(an);
      setMicReady(true);
      setStatus('mic ready — Record and hum');
      loop();
    } catch (e) {
      setStatus(`mic failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  }

  function startRec() {
    if (!ac.current) return;
    samples.current = [];
    recStart.current = ac.current.currentTime;
    recordingRef.current = true;
    setRecording(true);
    setResult(null);
    setStatus('recording… hum your line, then Stop');
  }
  function stopRec() {
    recordingRef.current = false;
    setRecording(false);
    const events = smoothToEvents(samples.current);
    if (!events) {
      setStatus('no pitch captured — raise boost, hum louder/closer, retry');
      return;
    }
    rawCapture.current = events;
    const cap = quantize(events, ctrl.current.bpm, ctrl.current.grid, ctrl.current.scale);
    setResult(cap);
    setStatus(cap ? `captured ${cap.notes.length} notes` : 'nothing to quantize');
  }
  function requantize() {
    if (!rawCapture.current) return;
    setResult(quantize(rawCapture.current, ctrl.current.bpm, ctrl.current.grid, ctrl.current.scale));
  }

  function sendToChat() {
    if (!result) return;
    window.dispatchEvent(new CustomEvent('strudel:hum-pattern', { detail: { snippet: result.snippet } }));
    setStatus('sent to chat ✓');
  }

  if (!open) return null;
  return (
    <div className="hum-overlay">
      <div className="hum-card">
        <header className="hum-head">
          <span>hum → melody</span>
          <button className="cbtn" onClick={onClose}>×</button>
        </header>
        <p className="hum-sub">Hum a line. On Stop it becomes notes + a Strudel pattern you can send to the chat.</p>

        <div className="hum-row">
          {!micReady ? (
            <button className="cbtn primary" onClick={enableMic}>Enable mic</button>
          ) : !recording ? (
            <button className="cbtn primary" onClick={startRec}>● Record</button>
          ) : (
            <button className="cbtn rec" onClick={stopRec}>■ Stop</button>
          )}
          <label className="hum-lab">bpm <input type="number" value={bpm} min={40} max={300} onChange={(e) => setBpm(+e.target.value || 144)} onBlur={requantize} /></label>
          <label className="hum-lab">grid <select value={grid} onChange={(e) => { setGrid(+e.target.value); setTimeout(requantize, 0); }}>
            <option value={4}>1/16</option><option value={2}>1/8</option><option value={1}>1/4</option><option value={8}>1/32</option>
          </select></label>
          <label className="hum-lab">snap <select value={scale} onChange={(e) => { setScale(e.target.value); setTimeout(requantize, 0); }}>
            <option value="chromatic">off</option><option value="C# major">C# major</option><option value="C minor">C minor</option>
          </select></label>
          <label className="hum-lab">boost <input type="range" min={1} max={24} value={boost} onChange={(e) => { setBoost(+e.target.value); if (inGain.current) inGain.current.gain.value = +e.target.value; }} /></label>
        </div>

        <div className="hum-note" ref={noteNow}>—</div>
        <div className="hum-status">{status}</div>

        <canvas ref={wave} className="hum-canvas" width={1600} height={160} style={{ height: 70 }} />
        <canvas ref={spectrum} className="hum-canvas" width={1600} height={220} style={{ height: 90 }} />
        <canvas ref={trail} className="hum-canvas" width={1600} height={300} style={{ height: 120 }} />

        {result && (
          <div className="hum-out">
            <pre>{result.snippet}</pre>
            <div className="hum-row">
              <button className="cbtn" onClick={() => navigator.clipboard.writeText(result.snippet)}>copy</button>
              <button className="cbtn primary" onClick={sendToChat}>→ chat</button>
            </div>
            <div className="hum-pills">
              {result.notes.map((r, i) => (
                <span className="hum-pill" key={i}>{r.name} · {r.dur.toFixed(2)}s</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
