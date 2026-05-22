// Visualizers — ported from the vanilla player. Butterchurn (WebGL milkdrop)
// behind cheap canvas2d layers (mandala, scrolling spectrogram, waveform,
// per-voice particle field). Driven by the analyser tap from audio-patch.
//
// The analyser + audio context don't exist until the engine boots (async,
// after this mounts), so everything reads getAnalyser()/getStrudelCtx() LAZILY
// each frame and butterchurn inits the first frame the context is available.

import { getAnalyser, getStrudelCtx } from '../audio-patch';
import { themeColor } from './color';
import { drawVoiceField, activeVoiceCount } from './voices';

const BUTTERCHURN_URL = 'https://esm.sh/butterchurn@2.6.7';
const BUTTERCHURN_PRESETS_URL = 'https://esm.sh/butterchurn-presets@2.4.7';

interface VizEls {
  butterchurn: HTMLCanvasElement;
  mandala: HTMLCanvasElement;
  spec: HTMLCanvasElement;
  wave: HTMLCanvasElement;
  voices: HTMLCanvasElement;
  beatRing: HTMLElement | null;
  voicesCount: HTMLElement | null;
  presetLabel: HTMLElement | null;
  isPlaying: () => boolean;
}

export function startViz(els: VizEls): () => void {
  const ctxMandala = els.mandala.getContext('2d')!;
  const ctxSpec = els.spec.getContext('2d')!;
  const ctxWave = els.wave.getContext('2d')!;
  const ctxVoices = els.voices.getContext('2d')!;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let bc: any = null;
  let bcTried = false;
  let bcSkip = false;
  let warmupFrames = 0;
  const WARMUP_MAX = 45; // develop a butterchurn frame before play, then freeze
  let raf = 0;
  let presetTimer = 0;
  let lastRms = 0;
  let lastBeatAt = 0;
  const bcDisabled = localStorage.getItem('toaster-strudel:bc-disabled') === '1';

  function resize() {
    for (const c of [els.mandala, els.spec, els.wave, els.voices]) {
      const r = c.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      c.width = Math.max(1, r.width * dpr);
      c.height = Math.max(1, r.height * dpr);
      c.getContext('2d')!.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    bcResize();
  }
  function bcResize() {
    if (!bc) return;
    const r = els.butterchurn.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = Math.max(2, Math.floor(r.width * dpr * 0.5));
    const h = Math.max(2, Math.floor(r.height * dpr * 0.5));
    els.butterchurn.width = w;
    els.butterchurn.height = h;
    bc.setRendererSize(w, h);
  }

  async function initButterchurn() {
    const strudelCtx = getStrudelCtx();
    const analyser = getAnalyser();
    if (bcDisabled || !strudelCtx) return;
    try {
      const [butterchurn, presets] = await Promise.all([
        import(/* @vite-ignore */ BUTTERCHURN_URL).then((m) => m.default || m),
        import(/* @vite-ignore */ BUTTERCHURN_PRESETS_URL).then((m) => m.default || m),
      ]);
      const rect = els.butterchurn.getBoundingClientRect();
      bc = butterchurn.createVisualizer(strudelCtx, els.butterchurn, {
        width: rect.width || 320,
        height: rect.height || 240,
        pixelRatio: window.devicePixelRatio || 1,
        textureRatio: 1,
      });
      const all = presets.getPresets();
      const keys = Object.keys(all);
      const rich =
        /flexi|martin|geiss|krash|psych|fractopia|fvese|mindblob|aurora|amen|cope|rovastar|stahlberg|illusion|tsunami/i;
      const pool = keys.filter((k) => rich.test(k));
      const usable = pool.length ? pool : keys;
      let idx = keys.indexOf(usable[Math.floor(Math.random() * usable.length)]);
      const setLabel = () => {
        if (els.presetLabel) els.presetLabel.textContent = keys[idx].split(/[—–-]/)[0].slice(0, 40);
      };
      bc.loadPreset(all[keys[idx]], 2.0);
      setLabel();
      if (analyser) bc.connectAudio(analyser);
      bcResize();
      presetTimer = window.setInterval(() => {
        if (!keys.length) return;
        idx = (idx + 1) % keys.length;
        try {
          bc.loadPreset(all[keys[idx]], 2.0);
          setLabel();
        } catch {
          /* skip bad preset */
        }
      }, 45000);
    } catch {
      /* butterchurn unavailable — cheap layers still run */
    }
  }

  function maybePulseBeat(rms: number) {
    const now = performance.now();
    if (rms - lastRms > 0.06 && now - lastBeatAt > 250 && els.beatRing) {
      els.beatRing.classList.remove('pulse');
      void els.beatRing.offsetWidth;
      els.beatRing.classList.add('pulse');
      lastBeatAt = now;
    }
    lastRms = lastRms * 0.7 + rms * 0.3;
  }

  function drawMandala(analyser: AnalyserNode) {
    const cssW = els.mandala.clientWidth;
    const cssH = els.mandala.clientHeight;
    const cx = cssW / 2;
    const cy = cssH / 2;
    const r0 = Math.min(cssW, cssH) * 0.18;
    const rMax = Math.min(cssW, cssH) * 0.45;
    const bins = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(bins);
    const nyquist = (getStrudelCtx()?.sampleRate || 44100) / 2;
    const bars = 72;
    const minF = 30;
    const maxF = 12000;
    let rmsSum = 0;
    ctxMandala.clearRect(0, 0, cssW, cssH);
    ctxMandala.save();
    ctxMandala.translate(cx, cy);
    ctxMandala.rotate(performance.now() / 30000);
    const accent = themeColor('accent');
    ctxMandala.strokeStyle = accent;
    ctxMandala.lineWidth = 2.2;
    ctxMandala.lineCap = 'round';
    ctxMandala.shadowBlur = 0;
    ctxMandala.beginPath();
    for (let i = 0; i < bars; i++) {
      const f = minF * Math.pow(maxF / minF, i / (bars - 1));
      const idx = Math.min(bins.length - 1, Math.floor((f / nyquist) * bins.length));
      const v = bins[idx] / 255;
      rmsSum += v * v;
      if (v < 0.03) continue;
      const angle = (i / bars) * Math.PI * 2;
      const len = Math.pow(v, 1.2) * (rMax - r0);
      ctxMandala.moveTo(Math.cos(angle) * r0, Math.sin(angle) * r0);
      ctxMandala.lineTo(Math.cos(angle) * (r0 + len), Math.sin(angle) * (r0 + len));
    }
    ctxMandala.stroke();
    ctxMandala.lineWidth = 1;
    ctxMandala.strokeStyle = `${accent}55`;
    ctxMandala.beginPath();
    ctxMandala.arc(0, 0, r0, 0, Math.PI * 2);
    ctxMandala.stroke();
    ctxMandala.restore();
    maybePulseBeat(Math.sqrt(rmsSum / bars));
  }

  function drawSpectrogram(analyser: AnalyserNode) {
    const cssW = els.spec.clientWidth;
    const cssH = els.spec.clientHeight;
    ctxSpec.globalCompositeOperation = 'copy';
    ctxSpec.drawImage(els.spec, -1, 0);
    ctxSpec.globalCompositeOperation = 'source-over';
    const bins = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(bins);
    const nyquist = (getStrudelCtx()?.sampleRate || 44100) / 2;
    const minF = 30;
    const maxF = 16000;
    const x = cssW - 1;
    ctxSpec.clearRect(x, 0, 1, cssH);
    const strip = 4;
    const a2 = themeColor('accent2');
    for (let y = 0; y < cssH; y += strip) {
      const f = minF * Math.pow(maxF / minF, 1 - y / cssH);
      const idx = Math.min(bins.length - 1, Math.floor((f / nyquist) * bins.length));
      const v = bins[idx] / 255;
      if (v < 0.04) continue;
      const a = Math.pow(v, 0.9);
      ctxSpec.fillStyle = `${a2}${Math.floor(a * 255).toString(16).padStart(2, '0')}`;
      ctxSpec.fillRect(x, y, 1, strip);
    }
  }

  function drawWaveform(analyser: AnalyserNode) {
    const cssW = els.wave.clientWidth;
    const cssH = els.wave.clientHeight;
    ctxWave.clearRect(0, 0, cssW, cssH);
    const wave = new Uint8Array(analyser.fftSize);
    analyser.getByteTimeDomainData(wave);
    ctxWave.strokeStyle = themeColor('warm');
    ctxWave.lineWidth = 1.2;
    ctxWave.shadowBlur = 0;
    ctxWave.beginPath();
    const step = cssW / wave.length;
    for (let i = 0; i < wave.length; i++) {
      const v = (wave[i] - 128) / 128;
      const y = cssH * 0.5 + v * cssH * 0.22;
      if (i === 0) ctxWave.moveTo(0, y);
      else ctxWave.lineTo(i * step, y);
    }
    ctxWave.stroke();
  }

  function draw() {
    raf = requestAnimationFrame(draw);
    const analyser = getAnalyser();
    if (!analyser) return; // engine not booted yet
    if (!bcTried && getStrudelCtx()) {
      bcTried = true;
      void initButterchurn();
    }
    const live = els.isPlaying();
    if (bc && !bcDisabled) {
      if (live) {
        if (!bcSkip) {
          bc.render();
          bcSkip = true;
        } else {
          bcSkip = false;
        }
      } else if (warmupFrames < WARMUP_MAX) {
        // before play: render a developed frame, then hold it static
        bc.render();
        warmupFrames++;
      }
    }
    if (!live) {
      if (els.voicesCount) els.voicesCount.textContent = '';
      return;
    }
    drawSpectrogram(analyser);
    drawMandala(analyser);
    drawVoiceField(ctxVoices, els.voices);
    drawWaveform(analyser);
    if (els.voicesCount) {
      const n = activeVoiceCount();
      els.voicesCount.textContent = n > 0 ? `${n} voice${n === 1 ? '' : 's'} live` : '';
    }
  }

  resize();
  const onResize = () => resize();
  window.addEventListener('resize', onResize);
  let ro: ResizeObserver | null = null;
  if ('ResizeObserver' in window) {
    ro = new ResizeObserver(() => resize());
    ro.observe(els.butterchurn.parentElement ?? els.butterchurn);
  }
  draw();

  return () => {
    cancelAnimationFrame(raf);
    clearInterval(presetTimer);
    window.removeEventListener('resize', onResize);
    ro?.disconnect();
  };
}
