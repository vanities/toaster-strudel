// strudel · skills — in-page player
//
// Uses @strudel/web for playback so we control the AudioContext and can tap
// an AnalyserNode for the visualisers. The audio tap is set up *before*
// initStrudel() so we catch the master-out connection and every per-voice
// route into ctx.destination.

// ── audio tap (must run before any AudioContext is created) ────
let analyser = null;
let strudelCtx = null;

(function patchAudio() {
  const OrigCtx = window.AudioContext || window.webkitAudioContext;
  if (!OrigCtx) return;
  class TappedAudioContext extends OrigCtx {
    constructor(...args) {
      super(...args);
      if (!strudelCtx) {
        strudelCtx = this;
        analyser = this.createAnalyser();
        analyser.fftSize = 4096;
        analyser.smoothingTimeConstant = 0.82;
        // Log state transitions — helps diagnose suspend/resume glitches
        this.addEventListener?.('statechange', () => {
          if (typeof window.__dlog === 'function') {
            window.__dlog('audio', `AudioContext state → ${this.state}`);
          }
        });
      }
    }
  }
  window.AudioContext = TappedAudioContext;
  if (window.webkitAudioContext) window.webkitAudioContext = TappedAudioContext;

  // Stats so we can see cross-context attempts + reach to each destination
  window.__connectStats = {
    total: 0,
    crossContext: 0,
    crossContextErrors: 0,
    toAnyDestination: 0,
    perDestinationCounts: new WeakMap(),
  };
  // Cross-context redirect mode — when ON, any attempt to connect a node
  // in one AudioContext to a node in another is rewritten to connect to
  // this.context.destination instead. Strudel caches a master output node
  // at initStrudel() time (in the live context). When the offline renderer
  // swaps the context, new sources still try to connect to that cached
  // master → cross-context error → caught silently → audio dies. With
  // this flag on, those final connections are redirected to the offline
  // destination so audio reaches the rendered buffer.
  //
  // It's blunt: we lose whatever master-bus processing (limiter, master
  // gain) was applied — but that beats total silence, and we can refine.
  window.__crossContextRedirect = false;
  window.__connectStats = {
    total: 0,
    crossContext: 0,
    crossContextErrors: 0,
    crossContextRedirected: 0,
    toAnyDestination: 0,
    perDestinationCounts: new WeakMap(),
  };
  const originalConnect = AudioNode.prototype.connect;
  AudioNode.prototype.connect = function (target, ...rest) {
    const stats = window.__connectStats;
    stats.total++;
    // Cross-context detection
    if (target && target instanceof AudioNode && this.context !== target.context) {
      stats.crossContext++;
      if (window.__crossContextRedirect) {
        target = this.context.destination;
        stats.crossContextRedirected++;
      }
    }
    if (target instanceof AudioDestinationNode) {
      stats.toAnyDestination++;
      const c = (stats.perDestinationCounts.get(target) || 0) + 1;
      stats.perDestinationCounts.set(target, c);
    }
    let result;
    try {
      result = originalConnect.call(this, target, ...rest);
    } catch (e) {
      if (target instanceof AudioNode && this.context !== target.context) {
        stats.crossContextErrors++;
      }
      throw e;
    }
    if (analyser && this !== analyser && target instanceof AudioDestinationNode) {
      try { originalConnect.call(this, analyser); } catch (_) {}
    }
    return result;
  };

  // Track every AudioWorklet.addModule URL globally so we can replay them
  // into a fresh OfflineAudioContext before offline rendering. Without this,
  // any AudioWorkletNode Strudel creates in the offline context fails
  // silently because the processor name isn't registered.
  window.__registeredWorkletURLs = new Set();
  if (window.AudioWorklet) {
    const origAdd = window.AudioWorklet.prototype.addModule;
    window.AudioWorklet.prototype.addModule = function (url, ...rest) {
      try { window.__registeredWorkletURLs.add(String(url)); } catch (_) {}
      return origAdd.call(this, url, ...rest);
    };
  }

  // Per-context node creation counters. Each context gets its own counter
  // object stored as a non-enumerable property. We diff these before vs.
  // after a render to know which context Strudel actually targeted.
  const CREATE_METHODS = [
    'createGain', 'createOscillator', 'createBufferSource', 'createBuffer',
    'createBiquadFilter', 'createDelay', 'createDynamicsCompressor',
    'createPanner', 'createStereoPanner', 'createWaveShaper',
    'createConvolver', 'createAnalyser', 'createChannelMerger',
    'createChannelSplitter', 'createConstantSource', 'createIIRFilter',
    'createPeriodicWave', 'createScriptProcessor',
  ];
  CREATE_METHODS.forEach((m) => {
    const proto = (window.BaseAudioContext && window.BaseAudioContext.prototype)
      || (window.AudioContext && window.AudioContext.prototype);
    if (!proto || typeof proto[m] !== 'function') return;
    const orig = proto[m];
    proto[m] = function (...args) {
      try {
        this.__ctxNodeCounts = this.__ctxNodeCounts || {};
        this.__ctxNodeCounts[m] = (this.__ctxNodeCounts[m] || 0) + 1;
      } catch (_) {}
      return orig.apply(this, args);
    };
  });
  // Also patch AudioWorkletNode constructor — superdough uses one
  if (window.AudioWorkletNode) {
    const OrigAWN = window.AudioWorkletNode;
    window.AudioWorkletNode = function (ctx, name, opts) {
      try {
        ctx.__ctxNodeCounts = ctx.__ctxNodeCounts || {};
        const key = `AudioWorkletNode(${name})`;
        ctx.__ctxNodeCounts[key] = (ctx.__ctxNodeCounts[key] || 0) + 1;
      } catch (_) {}
      return new OrigAWN(ctx, name, opts);
    };
    window.AudioWorkletNode.prototype = OrigAWN.prototype;
  }
})();

// ── strudel ────────────────────────────────────────────────────
import {
  initStrudel, hush, evaluate, getAudioContext, samples,
  setAudioContext, webaudioOutput, superdough,
  getSuperdoughAudioController, setSuperdoughAudioController,
} from 'https://unpkg.com/@strudel/web@1.3.0/dist/index.mjs';

// ── diagnostic logging ─────────────────────────────────────────
// Always-on. Prefixed + timestamped so glitches are easy to correlate
// with the rest of the console (especially "skip query: too late" lines).
const T0 = performance.now();
function dlog(category, ...args) {
  const t = ((performance.now() - T0) / 1000).toFixed(2);
  console.log(`%c[${t.padStart(7)}s][${category}]`, 'color:#9b6dff;font-weight:600', ...args);
}
function dwarn(category, ...args) {
  const t = ((performance.now() - T0) / 1000).toFixed(2);
  console.warn(`%c[${t.padStart(7)}s][${category}]`, 'color:#ff8a3d;font-weight:600', ...args);
}
window.__dlog = dlog;

// Remote logging — JSON-line POST to /log so we can tail /tmp/strudel-debug.log
// instead of screen-scraping the DevTools console.
function dremote(category, payload) {
  const t = ((performance.now() - T0) / 1000).toFixed(2);
  const entry = { tSec: t, category, payload };
  // Don't await — fire and forget; failures are silent
  try {
    fetch('/log', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry),
    }).catch(() => {});
  } catch (_) {}
  // Also log locally
  dlog(category, payload);
}
window.__dremote = dremote;

dlog('boot', 'player.js loaded; T0=', new Date().toISOString());
dremote('boot', { ua: navigator.userAgent, ts: new Date().toISOString() });

// Watch for Strudel's "skip query: too late" warnings — wrap console.log to
// flag them with our diagnostic prefix so they line up with our other logs.
(() => {
  const origLog = console.log;
  console.log = function (...args) {
    if (args[0] && typeof args[0] === 'string' && args[0].startsWith('skip query: too late')) {
      const t = ((performance.now() - T0) / 1000).toFixed(2);
      origLog.call(console, `%c[${t.padStart(7)}s][AUDIO-GLITCH]`, 'background:#ff3d6b;color:#fff;font-weight:700;padding:2px 4px', args[0]);
      return;
    }
    return origLog.apply(console, args);
  };
})();

const SAMPLE_BASE = 'https://raw.githubusercontent.com/felixroos/dough-samples/main';

// ── state / refs ───────────────────────────────────────────────
// Auto-discovered at boot from GET /tracks (the server lists tracks/*.strudel).
// Don't hardcode track entries here — the menu reflects what's on disk.
let TRACKS = [];

const $ = (id) => document.getElementById(id);
const els = {
  select:    $('track-select'),
  prev:      $('prev'),
  play:      $('play'),
  stop:      $('stop'),
  next:      $('next'),
  reload:    $('reload'),
  openCc:    $('open-cc'),
  trackNum:  $('track-num'),
  title:     $('track-title'),
  notes:     $('track-notes'),
  hint:      $('hint'),
  bpm:       $('bpm'),
  state:     $('state'),
  timeReadout: $('time-readout'),
  nextReadout: $('next-readout'),
  themeBtn:  $('theme-btn'),
  helpBtn:   $('help-btn'),
  help:      $('help'),
  helpClose: $('help-close'),
  butterchurn: $('butterchurn'),
  mandala:   $('mandala'),
  spec:      $('spectrogram'),
  wave:      $('wave'),
  voices:    $('voices'),
  rune:      $('center-rune'),
  beatRing:  $('beat-ring'),
  vizPreset: $('viz-preset'),
  vizVoicesCount: $('viz-voices-count'),
  codePanel: $('code-panel'),
  codePre:   $('code-pre'),
  codePath:  $('code-path'),
  patchFlash:$('patch-flash'),
  tlStrip:   $('tl-strip'),
  tlPrev:    $('tl-prev'),
  tlNext:    $('tl-next'),
  tlAuto:    $('tl-auto'),
  tlReplay:  $('tl-replay'),
  tlInfo:    $('tl-info'),
  tlClear:   $('tl-clear'),
};

let currentIndex = 0;
let currentCode = '';
let currentCps = 0.5;
let cpsOverride = null;          // [/] adjustments
let isPlaying = false;
let isMuted = false;
let strudelReady = false;

// ── themes ─────────────────────────────────────────────────────
const THEMES = ['aurora', 'sunset', 'forest', 'void'];
let themeIdx = Math.max(0, THEMES.indexOf(localStorage.getItem('theme') || 'aurora'));

function applyTheme() {
  const name = THEMES[themeIdx];
  document.documentElement.setAttribute('data-theme', name);
  els.themeBtn.textContent = name;
  localStorage.setItem('theme', name);
}
function cycleTheme() {
  themeIdx = (themeIdx + 1) % THEMES.length;
  applyTheme();
}
applyTheme();

const themeColor = (name) =>
  getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim() || '#fff';

// ── populate dropdown (called after tracks are discovered) ────
function populateTrackMenu() {
  els.select.innerHTML = '';
  for (const t of TRACKS) {
    const opt = document.createElement('option');
    opt.value = t.id;
    opt.textContent = t.label;
    els.select.appendChild(opt);
  }
}

// ── strudel init + sample load ────────────────────────────────
let strudelRepl = null;

const loaderEl  = document.getElementById('loader');
const loaderStep = document.getElementById('loader-step');
const loaderFill = document.getElementById('loader-fill');
function setLoader(step, pct) {
  if (loaderStep) loaderStep.textContent = step;
  if (loaderFill) loaderFill.style.width = `${pct}%`;
  if (pct >= 100 && loaderEl) {
    setTimeout(() => loaderEl.classList.add('hide'), 350);
  }
}

setLoader('booting audio engine', 8);
setStatus('booting');
(async () => {
  try {
    const t1 = performance.now();
    strudelRepl = await initStrudel();
    dlog('init', `initStrudel took ${(performance.now() - t1).toFixed(0)}ms`);
    window.__repl = strudelRepl;

    setLoader('loading drum samples', 22);
    const t2 = performance.now();
    await samples(`${SAMPLE_BASE}/tidal-drum-machines.json`);
    dlog('init', `drum samples (683 sounds) loaded in ${(performance.now() - t2).toFixed(0)}ms`);

    setLoader('loading piano', 30);
    const t3 = performance.now();
    await samples(`${SAMPLE_BASE}/piano.json`);
    dlog('init', `piano loaded in ${(performance.now() - t3).toFixed(0)}ms`);

    // VCSL — 128 orchestral instruments. The big one: kalimba (Bonobo!),
    // vibraphone, marimba, sax, glockenspiel, tubularbells, harp.
    setLoader('loading orchestral (VCSL)', 38);
    const t4 = performance.now();
    await samples(`${SAMPLE_BASE}/vcsl.json`);
    dlog('init', `VCSL (128 instruments) loaded in ${(performance.now() - t4).toFixed(0)}ms`);

    // Mridangam — South Indian hand drum, for FP/DJRUM hand-percussion feel
    setLoader('loading mridangam', 44);
    const t5 = performance.now();
    await samples(`${SAMPLE_BASE}/mridangam.json`);
    dlog('init', `mridangam (13 articulations) loaded in ${(performance.now() - t5).toFixed(0)}ms`);

    // EmuSP12 — boom-bap hip-hop drum kit alternative to AkaiLinn
    setLoader('loading SP-12', 50);
    const t6 = performance.now();
    await samples(`${SAMPLE_BASE}/EmuSP12.json`);
    dlog('init', `EmuSP12 (14 sounds) loaded in ${(performance.now() - t6).toFixed(0)}ms`);

    // Dirt-Samples curated — field recordings (wind/crow/insect) + textures
    setLoader('loading textures', 53);
    const t7 = performance.now();
    await samples(`${SAMPLE_BASE}/Dirt-Samples.json`);
    dlog('init', `Dirt-Samples curated (9 folders) loaded in ${(performance.now() - t7).toFixed(0)}ms`);

    // Full TidalCycles Dirt-Samples — 218 folders. Adds tabla, sitar, jvbass,
    // breaks125/152/157/165 (jungle/dnb breaks), speakspell, etc.
    setLoader('loading full dirt set', 58);
    const t8 = performance.now();
    try {
      await samples('github:tidalcycles/Dirt-Samples');
      dlog('init', `tidalcycles/Dirt-Samples (218 folders) loaded in ${(performance.now() - t8).toFixed(0)}ms`);
    } catch (e) {
      dwarn('init', 'full Dirt-Samples load failed (ok to skip):', e.message);
    }

    strudelReady = true;
    setLoader('loading visualizer', 62);
    initButterchurn()
      .then(() => dlog('init', 'butterchurn ready'))
      .catch(err => dwarn('init', 'butterchurn skipped:', err.message));

    setLoader('warming up samples', 75);
    // Pre-warm the AkaiLinn drum samples we use in nearly every track.
    // Mid-cycle sample loads block the audio thread → "skip query: too
    // late" stutters. Loading them up-front fixes glitches on play.
    await prewarmSamples();

    setLoader('ready', 100);
    setStatus('ready');
    setupHighlightTap();
    dlog('init', 'audio context state:', strudelCtx?.state, 'sample rate:', strudelCtx?.sampleRate);
  } catch (err) {
    console.error(err);
    setStatus('init failed');
    dwarn('init', 'failed:', err.message);
    if (loaderStep) loaderStep.textContent = `error: ${String(err.message || err).slice(0, 40)}`;
  }
})();

async function prewarmSamples() {
  // Trigger decoder for the common AkaiLinn drum hits + piano sample.
  // We do this by evaluating a silent-gain pattern that touches each sample.
  // Then `hush()` to stop. The decoded buffers stay in the sample cache.
  const t = performance.now();
  try {
    await evaluate(`stack(
      s("bd").bank("AkaiLinn").gain(0.001),
      s("sd").bank("AkaiLinn").gain(0.001),
      s("hh").bank("AkaiLinn").gain(0.001),
      s("cp").bank("AkaiLinn").gain(0.001),
      s("oh").bank("AkaiLinn").gain(0.001),
      s("rd").bank("AkaiLinn").gain(0.001),
      s("cb").bank("AkaiLinn").gain(0.001),
      note("C3").s("piano").gain(0.001),
    ).slow(8)`);
    // Let the scheduler tick a few times to actually fetch + decode samples.
    await new Promise(r => setTimeout(r, 600));
    hush();
    dlog('init', `sample prewarm took ${(performance.now() - t).toFixed(0)}ms`);
  } catch (e) {
    dwarn('init', 'sample prewarm failed:', e.message);
  }
}

// ── butterchurn (WebGL milkdrop-style visualizer) ─────────────
let bcVisualizer = null;
let bcPresets = null;
let bcPresetKeys = [];
let bcPresetIdx = 0;
let bcAnalyserSrc = null;
async function initButterchurn() {
  const [butterchurn, butterchurnPresets] = await Promise.all([
    import('https://esm.sh/butterchurn@2.6.7').then(m => m.default || m),
    import('https://esm.sh/butterchurn-presets@2.4.7').then(m => m.default || m),
  ]);
  const canvas = els.butterchurn;
  if (!canvas || !strudelCtx) throw new Error('no canvas/ctx');
  const rect = canvas.getBoundingClientRect();
  bcVisualizer = butterchurn.createVisualizer(strudelCtx, canvas, {
    width: rect.width,
    height: rect.height,
    pixelRatio: window.devicePixelRatio || 1,
    textureRatio: 1,
  });
  window.__bc = bcVisualizer;
  window.__analyser = analyser;
  bcPresets = butterchurnPresets.getPresets();
  bcPresetKeys = Object.keys(bcPresets);
  // Bias toward presets known to be visually rich and audio-reactive
  const richRegex = /flexi|martin|geiss|krash|psych|fractopia|fvese|mindblob|aurora|amen|cope|rovastar|stahlberg|illusion|tsunami/i;
  const ranked = bcPresetKeys.filter(k => richRegex.test(k));
  const pool = ranked.length ? ranked : bcPresetKeys;
  const pickKey = pool[Math.floor(Math.random() * pool.length)];
  bcPresetIdx = bcPresetKeys.indexOf(pickKey);
  bcLoadPreset(bcPresetIdx);

  // Hook into our existing audio graph: connect analyser to butterchurn's input
  if (analyser) {
    bcVisualizer.connectAudio(analyser);
    bcAnalyserSrc = analyser;
  }
  // Resize Butterchurn to match its current rendered size
  bcResize();
  // Cycle preset every 45s for variety
  setInterval(() => cycleBcPreset(1), 45000);
}

function bcLoadPreset(idx) {
  if (!bcVisualizer || !bcPresetKeys.length) return;
  const key = bcPresetKeys[idx];
  try {
    bcVisualizer.loadPreset(bcPresets[key], 2.0); // 2.0s blend transition
    if (els.vizPreset) els.vizPreset.textContent = key.split(/[—–-]/)[0].slice(0, 40);
  } catch (e) {
    console.warn('preset load failed:', e);
  }
}

function cycleBcPreset(delta = 1) {
  if (!bcPresetKeys.length) return;
  bcPresetIdx = (bcPresetIdx + delta + bcPresetKeys.length) % bcPresetKeys.length;
  bcLoadPreset(bcPresetIdx);
}

function bcResize() {
  if (!bcVisualizer || !els.butterchurn) return;
  const r = els.butterchurn.getBoundingClientRect();
  // Half-resolution rendering — shaders run on 4× fewer pixels, upscaled via
  // CSS. Visual cost drops from ~25ms/frame to ~6ms/frame on typical setups.
  const renderScale = 0.5;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const w = Math.max(2, Math.floor(r.width * dpr * renderScale));
  const h = Math.max(2, Math.floor(r.height * dpr * renderScale));
  els.butterchurn.width = w;
  els.butterchurn.height = h;
  bcVisualizer.setRendererSize(w, h);
}

// ── helpers ───────────────────────────────────────────────────
function setStatus(t) { els.state.textContent = t; }

function parseHeader(code) {
  const lines = code.split('\n');
  const head = [];
  for (const raw of lines) {
    const line = raw.trim();
    if (line.startsWith('//')) head.push(line.replace(/^\/\/\s?/, ''));
    else if (line === '') { if (head.length) break; }
    else break;
  }
  return { title: head[0] || '', notes: head.slice(1).join('\n') };
}

function parseCps(code) {
  const m = code.match(/setcps\s*\(\s*([\d.]+)/);
  return m ? parseFloat(m[1]) : null;
}

function cpsToBpm(cps) { return Math.round(cps * 60 * 4); } // assume 4 beats / cycle

function updateBpm() {
  const cps = cpsOverride || currentCps;
  els.bpm.textContent = `${cpsToBpm(cps)}`;
}

function fmtMMSS(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

let playStartedAt = 0;
function updateTimeReadout() {
  if (!els.timeReadout) return;
  const list = getSections(TRACKS[currentIndex]?.id);
  const totalSecs = autoAdvance && list.length > 0
    ? list.reduce((sum, s) => sum + sectionSeconds(s), 0)
    : sectionSeconds(list?.[viewedIndex < 0 ? 0 : viewedIndex] || { cycles: null });
  const elapsed = isPlaying ? performance.now() - playStartedAt : 0;
  els.timeReadout.textContent = `${fmtMMSS(elapsed)} / ${fmtMMSS(totalSecs * 1000)}`;
}

let nextSectionAt = 0;
function updateNextReadout() {
  if (!els.nextReadout) return;
  if (!autoAdvance || !nextSectionAt) {
    els.nextReadout.textContent = '—';
    return;
  }
  const remain = Math.max(0, nextSectionAt - performance.now());
  els.nextReadout.textContent = fmtMMSS(remain);
}

setInterval(() => { updateTimeReadout(); updateNextReadout(); }, 250);

function transformCode(raw) {
  // If user nudged tempo, replace setcps in the code so Strudel re-evaluates at the new tempo.
  if (cpsOverride == null) return raw;
  return raw.replace(/setcps\s*\(\s*([\d.]+)\s*\)/, `setcps(${cpsOverride.toFixed(3)})`);
}

// ── track loading ─────────────────────────────────────────────
async function loadTrack(index) {
  currentIndex = (index + TRACKS.length) % TRACKS.length;
  const track = TRACKS[currentIndex];
  els.select.value = track.id;
  els.trackNum.textContent = track.label.split(' — ')[0];
  els.codePath.textContent = `tracks/${track.id}.strudel`;
  setStatus('loading');

  try {
    const res = await fetch(`../tracks/${track.id}.strudel`, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const code = await res.text();

    currentCode = code;
    cpsOverride = null;
    currentCps = parseCps(code) ?? 0.5;
    updateBpm();

    const header = parseHeader(code);
    els.title.textContent = header.title || track.label;
    if (els.notes) els.notes.textContent = header.notes;
    if (els.hint) els.hint.innerHTML = `<kbd>space</kbd> play · <kbd>?</kbd> help`;

    renderCode(code);
    els.openCc.href = `https://strudel.cc/#${codeToHash(code)}`;

    // Fetch file-backed sections from tracks/<id>/NN.strudel
    viewedIndex = -1;
    await fetchSections(track.id);
    lastSectionCount = getSections(track.id).length;
    renderTimeline();

    if (isPlaying) await play(); // hot-swap if already playing
    else setStatus(strudelReady ? 'ready' : 'loading samples…');
  } catch (err) {
    els.title.textContent = 'failed to load';
    if (els.notes) els.notes.textContent = err.message;
    setStatus('error');
  }
}

// ── code panel rendering + auto-reload ────────────────────────
const STRUDEL_FNS = new Set([
  'setcps','stack','note','s','cat','seq','sine','saw','sawtooth','square',
  'triangle','cos','perlin','silence','hush','white','bd','sd','hh','cp','oh','pink',
]);

function tokenize(code) {
  const tokens = [];
  let i = 0;
  while (i < code.length) {
    const rest = code.slice(i);
    let m;
    if (m = rest.match(/^\/\/[^\n]*/))            { tokens.push({ type: 'comment', start: i, end: i + m[0].length, text: m[0] }); i += m[0].length; continue; }
    if (m = rest.match(/^"(?:[^"\\]|\\.)*"/))     { tokens.push({ type: 'string',  start: i, end: i + m[0].length, text: m[0] }); i += m[0].length; continue; }
    if (m = rest.match(/^\d+\.?\d*/))             { tokens.push({ type: 'number',  start: i, end: i + m[0].length, text: m[0] }); i += m[0].length; continue; }
    if (m = rest.match(/^[a-zA-Z_$][\w$]*/)) {
      const isMethod = i > 0 && code[i - 1] === '.';
      const type = isMethod ? 'method' : (STRUDEL_FNS.has(m[0]) ? 'fn' : 'ident');
      tokens.push({ type, start: i, end: i + m[0].length, text: m[0] }); i += m[0].length; continue;
    }
    tokens.push({ type: 'op', start: i, end: i + 1, text: code[i] });
    i++;
  }
  return tokens;
}

function renderCode(code) {
  const tokens = tokenize(code);
  // Build a per-char class map so each character can be its own span,
  // carrying its token's syntax class but flashable independently.
  const classAt = new Array(code.length);
  for (const t of tokens) for (let i = t.start; i < t.end; i++) classAt[i] = `tk-${t.type}`;
  const esc = (c) =>
    c === '<' ? '&lt;' : c === '>' ? '&gt;' : c === '&' ? '&amp;' : c;
  const parts = [];
  for (let i = 0; i < code.length; i++) {
    const ch = code[i];
    if (ch === '\n') { parts.push('\n'); continue; }
    parts.push(`<span class="${classAt[i] || 'tk-op'}" data-pos="${i}">${esc(ch)}</span>`);
  }
  els.codePre.innerHTML = parts.join('');
  charSpans = new Array(code.length);
  for (const span of els.codePre.querySelectorAll('span[data-pos]')) {
    charSpans[+span.dataset.pos] = span;
  }
}

function flashPatch(label = 'patched') {
  els.patchFlash.textContent = `● ${label}`;
  els.patchFlash.classList.add('show');
  setTimeout(() => els.patchFlash.classList.remove('show'), 1200);
}

// ── live highlight tap ────────────────────────────────────────
// Strudel attaches `.context.locations` to each hap telling us where in the
// source it came from. The Cyclist scheduler captures its default onTrigger
// into a constructor closure (no way to swap it), but Pattern.onTrigger(fn,
// dominant=false) chains a side-effect onto the pattern itself, running
// alongside the default audio output. Re-apply this after every evaluate.
let charSpans = [];

function buildTap(pattern) {
  if (!pattern || pattern.__tapped) return pattern;
  // Callback signature (per-hap onTrigger): (hap, currentTime, cps, targetTime)
  const tapped = pattern.onTrigger((hap, _now, cps, targetTime) => {
    try {
      const locs = hap?.context?.locations || [];
      const color = colorForHap(hap);
      const v = hap?.value || {};
      // Note length in seconds = whole-event span (cycles) ÷ cps. Long/held
      // notes (pads, drones) stay lit and pulse for their full duration.
      let durSec = 0;
      if (hap?.whole && cps > 0) {
        durSec = (Number(hap.whole.end) - Number(hap.whole.begin)) / cps;
      }
      // Loudness drives "lighter → more color": gain×velocity. Attack drives
      // the swell-in. Glow pulses at the beat (1 cycle = 4 beats), phase-locked
      // to the beat grid so held notes breathe together.
      const gain = (v.gain ?? 0.4) * (v.velocity ?? 1);
      const attackSec = Number(v.attack) || 0;
      const beatSec = cps > 0 ? 1 / (cps * 4) : 0.5;
      let pulseDelay = 0;
      if (cps > 0 && Number.isFinite(targetTime)) {
        const beatPhase = ((targetTime * cps * 4) % 1 + 1) % 1;
        pulseDelay = -beatPhase * beatSec;
      }
      const opts = { durSec, gain, attackSec, beatSec, pulseDelay };
      for (const loc of locs) flashRange(loc.start, loc.end, color, opts);
      if (locs.length) registerVoiceHit(locs[0], hap);
    } catch (_) {}
  }, false);
  tapped.__tapped = true;
  return tapped;
}

// Monkey-patch scheduler.setPattern so the highlight tap is applied INSIDE
// the single setPattern call evaluate makes — instead of evaluate doing
// setPattern then us doing a second setPattern after. Two pattern swaps in
// rapid succession make the cyclist worker re-fetch events, causing an
// audible gap when jumping sections. One swap = no gap.
function setupHighlightTap() {
  const sched = strudelRepl?.scheduler;
  if (!sched) return;
  if (sched.__patched) return;
  const orig = sched.setPattern.bind(sched);
  sched.setPattern = (pattern, autoStart) => orig(buildTap(pattern), autoStart);
  sched.__patched = true;
  // Wrap whatever's already set
  if (sched.pattern && !sched.pattern.__tapped) sched.setPattern(sched.pattern, false);
}

// Kept as a no-op for back-compat with existing call sites.
function hookPattern() { /* setPattern is patched — pattern is already tapped */ }

// ── click-to-audition (stopped mode) ──────────────────────────
// When stopped, clicking a note in the code plays just that note in its own
// voice. The same `context.locations` the highlight tap uses (absolute char
// offsets into the source) run in reverse here: compile the current code once,
// index every unique note by its source range + its full control object
// (s/note/gain/lpf/…), and on click fire a one-shot through superdough — the
// same engine + instrument + effects the scheduler would use.
const AUDITION_CYCLES = 32;   // query enough to capture slow melodies (.slow(16))
const AUDITION_DUR = 0.6;     // seconds to hold each auditioned note
let auditionCode = null;      // the currentCode auditionLocs were built for
let auditionLocs = [];        // [{ start, end, value }] — one per unique note location

async function ensureAuditionMap() {
  if (auditionCode === currentCode) return;   // cached + still fresh
  auditionCode = currentCode;
  auditionLocs = [];
  let pat = null;
  try {
    await evaluate(transformCode(currentCode));
    pat = strudelRepl?.scheduler?.pattern;     // capture BEFORE hush (hush may clear it)
  } catch (e) {
    dwarn('audition', 'compile failed:', e?.message);
  } finally {
    // We're auditioning while stopped — never let the compile keep playing.
    if (!isPlaying) { try { hush(); clearHighlights(); } catch (_) {} }
  }
  if (!pat) return;
  const byLoc = new Map();
  try {
    const haps = pat.queryArc(0, AUDITION_CYCLES, { _cps: currentCps, cyclist: 'neocyclist' }) || [];
    for (const h of haps) {
      const v = h?.value;
      if (!v || typeof v !== 'object') continue;
      for (const loc of (h.context?.locations || [])) {
        if (!Number.isInteger(loc.start) || !Number.isInteger(loc.end)) continue;
        const key = loc.start + ':' + loc.end;
        if (!byLoc.has(key)) byLoc.set(key, { start: loc.start, end: loc.end, value: v });
      }
    }
  } catch (e) {
    dwarn('audition', 'query failed:', e?.message);
  }
  auditionLocs = [...byLoc.values()];
}

async function auditionAt(offset) {
  await ensureAuditionMap();
  const hits = auditionLocs.filter((l) => offset >= l.start && offset < l.end);
  if (!hits.length) return;
  const ctx = getAudioContext();
  if (ctx?.state === 'suspended') { try { await ctx.resume(); } catch (_) {} }
  const t = (ctx ? ctx.currentTime : 0) + 0.04;
  for (const h of hits) {
    try { superdough(h.value, t, AUDITION_DUR, currentCps); } catch (e) { dwarn('audition', e?.message); }
    flashRange(h.start, h.end, colorForHap({ value: h.value }), {
      durSec: 0.4, gain: h.value.gain ?? 0.4, attackSec: h.value.attack || 0,
    });
  }
}

function onCodeClick(e) {
  if (isPlaying || !strudelReady) return;      // audition is a stopped-mode tool
  const span = e.target.closest?.('span[data-pos]');
  if (!span) return;
  const offset = +span.dataset.pos;
  if (Number.isInteger(offset)) auditionAt(offset);
}

// ── recorder: capture raw PCM and download as WAV ─────────────
// One ScriptProcessor sits behind the analyser node. Its output is gain-zero
// so it doesn't double-add audio; its input is the same signal Butterchurn
// and the visualisers analyse. Convert WAV → FLAC with ffmpeg afterwards.
let captureProcessor = null;
let recBuffers = [];
let isRecording = false;
let recStartedAt = 0;

// ScriptProcessor runs on the MAIN THREAD — leaving it in the audio chain
// permanently causes "skip query: too late" errors in Strudel's scheduler
// (the audio thread gets starved when scrolling/heavy paint). So we
// connect it only WHILE recording, and disconnect when stopped.
let captureMuteOut = null;
function setupRecorder() {
  if (!strudelCtx || !analyser || captureProcessor) return;
  try {
    captureProcessor = strudelCtx.createScriptProcessor(4096, 2, 2);
  } catch (_) { return; }
  captureMuteOut = strudelCtx.createGain();
  captureMuteOut.gain.value = 0;
  // NOTE: not connecting yet — connectRecorder() does that
  captureProcessor.onaudioprocess = (e) => {
    if (!isRecording) return;
    const l = e.inputBuffer.getChannelData(0);
    const r = e.inputBuffer.numberOfChannels > 1 ? e.inputBuffer.getChannelData(1) : l;
    recBuffers.push({ l: new Float32Array(l), r: new Float32Array(r) });
  };
}

function connectRecorder() {
  if (!captureProcessor || !analyser || !captureMuteOut) return;
  try {
    analyser.connect(captureProcessor);
    captureProcessor.connect(captureMuteOut);
    captureMuteOut.connect(strudelCtx.destination);
  } catch (_) {}
}

function disconnectRecorder() {
  if (!captureProcessor) return;
  try { analyser.disconnect(captureProcessor); } catch (_) {}
  try { captureProcessor.disconnect(); } catch (_) {}
  try { captureMuteOut.disconnect(); } catch (_) {}
}

function recordDuration() { return isRecording ? performance.now() - recStartedAt : 0; }

// ── always-on ring buffer ──────────────────────────────────────
// AudioWorklet (audio-thread) captures the last 30s of master output.
// Uploaded to the server every 2s so Claude can curl /audio?seconds=N
// and get a WAV without driving the UI.
//
// Topology note: the worklet is a SINK (0 outputs). We deliberately do NOT
// connect it to destination — the patched AudioNode.connect at the top of
// this file would auto-route any-→destination edges to analyser, creating
// a cycle (analyser → ringNode → analyser) that mutes the analyser tap
// (which the waveform visualiser reads from).
let ringNode = null;
let ringUploadTimer = null;
let lastUploadAt = 0;
const RING_SECONDS = 30;
const UPLOAD_EVERY_MS = 2000;

async function setupRingBuffer() {
  if (!strudelCtx || !analyser || ringNode) return;
  try {
    await strudelCtx.audioWorklet.addModule('/player/ring-buffer-worklet.js');
    ringNode = new AudioWorkletNode(strudelCtx, 'ring-buffer', {
      numberOfInputs: 1,
      numberOfOutputs: 0,
      processorOptions: { seconds: RING_SECONDS },
    });
    analyser.connect(ringNode);
    dlog('ring', `capturing last ${RING_SECONDS}s of audio · sr=${strudelCtx.sampleRate}`);
    startRingUploadLoop();
    // Expose for manual triggering / debugging
    window.__ringNode = ringNode;
    window.__uploadRingBuffer = uploadRingBuffer;
  } catch (e) {
    dwarn('ring', 'setupRingBuffer failed:', e.message);
  }
}

// Always expose the setup function so it can be invoked manually (e.g. from
// agent-browser in headless mode where the autoplay user-gesture chain
// doesn't fire reliably).
window.__setupRingBuffer = () => setupRingBuffer();

function startRingUploadLoop() {
  if (ringUploadTimer) return;
  ringUploadTimer = setInterval(uploadRingBuffer, UPLOAD_EVERY_MS);
}

async function uploadRingBuffer() {
  if (!ringNode || !strudelCtx) return;
  // Don't upload if we just did — avoid stacking pending msg responses.
  // (Even when suspended we still upload — the ring buffer keeps the most
  // recent audio so /audio?seconds=N stays meaningful after stop.)
  const now = performance.now();
  if (now - lastUploadAt < UPLOAD_EVERY_MS - 200) return;
  lastUploadAt = now;

  const data = await new Promise((resolve) => {
    const handler = (e) => {
      ringNode.port.removeEventListener('message', handler);
      resolve(e.data);
    };
    ringNode.port.addEventListener('message', handler);
    ringNode.port.start?.();
    ringNode.port.postMessage({ cmd: 'getBuffer' });
  });

  const { left, right, sampleRate, writePos } = data;
  const numSamples = left.length;
  // Linearize so oldest sample is at index 0
  const linL = new Float32Array(numSamples);
  const linR = new Float32Array(numSamples);
  for (let i = 0; i < numSamples; i++) {
    const src = (writePos + i) % numSamples;
    linL[i] = left[src];
    linR[i] = right[src];
  }
  // Wire format: [sampleRate u32][numSamples u32][left f32...][right f32...]
  const out = new ArrayBuffer(8 + numSamples * 4 * 2);
  const view = new DataView(out);
  view.setUint32(0, sampleRate, true);
  view.setUint32(4, numSamples, true);
  new Float32Array(out, 8, numSamples).set(linL);
  new Float32Array(out, 8 + numSamples * 4, numSamples).set(linR);
  try {
    await fetch('/upload-buffer', {
      method: 'POST',
      body: out,
      headers: { 'Content-Type': 'application/octet-stream' },
    });
  } catch (_) { /* server may be offline; that's fine */ }
}

function toggleRecord() {
  setupRecorder();
  if (isRecording) {
    isRecording = false;
    disconnectRecorder();  // pull ScriptProcessor out of audio chain immediately
    const trackId = TRACKS[currentIndex]?.id || 'song';
    downloadWav(`toaster-strudel_${trackId}_${Date.now()}.wav`);
    updateRecordUI(false);
  } else {
    recBuffers = [];
    isRecording = true;
    recStartedAt = performance.now();
    connectRecorder();  // only in the audio path during active recording
    updateRecordUI(true);
  }
}

function updateRecordUI(rec) {
  const btn = document.getElementById('rec-btn');
  if (!btn) return;
  if (rec) {
    btn.classList.add('recording');
    btn.title = 'Stop recording — click to save .wav';
  } else {
    btn.classList.remove('recording');
    btn.title = 'Record (start). Convert WAV → FLAC with: ffmpeg -i in.wav -c:a flac out.flac';
  }
}

function downloadWav(filename) {
  if (!recBuffers.length) return;
  const totalLen = recBuffers.reduce((s, b) => s + b.l.length, 0);
  const left  = new Float32Array(totalLen);
  const right = new Float32Array(totalLen);
  let off = 0;
  for (const b of recBuffers) {
    left.set(b.l, off);
    right.set(b.r, off);
    off += b.l.length;
  }
  const sr = strudelCtx.sampleRate;
  const wav = encodeWav(left, right, sr);
  const blob = new Blob([wav], { type: 'audio/wav' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 100);
}

// ── offline render: synthesise the whole album to WAV (no real-time) ─
// Swap Strudel's audio context for an OfflineAudioContext sized to the
// total song length, replay each section's haps at absolute times via
// webaudioOutput, then render. Faster than real-time. Limitations:
// drum samples baked into the live context may not transfer; synth voices
// (sine/sawtooth/triangle/white/piano) work cleanly.
async function renderAlbumOffline() {
  const id = TRACKS[currentIndex].id;
  const list = getSections(id);
  if (!list.length) return;

  dremote('render', { phase: 'start', track: id, sections: list.length });

  // Pause anything live
  if (isPlaying) stop();
  hush();

  const sampleRate = 44100;
  const cpsBase = parseCps(list[0].code) || 0.4;
  const totalSecs = list.reduce((s, snap) => s + sectionCycles(snap) / cpsBase, 0);
  const totalSamples = Math.ceil(sampleRate * totalSecs) + sampleRate; // 1s pad
  showRenderLoader(`rendering ${fmtMMSS(totalSecs * 1000)} of audio…`, 5);

  const liveCtx = getAudioContext();
  const offlineCtx = new OfflineAudioContext({
    numberOfChannels: 2,
    length: totalSamples,
    sampleRate,
  });

  dremote('render', {
    phase: 'contexts-created',
    liveCtxSampleRate: liveCtx.sampleRate,
    liveCtxState: liveCtx.state,
    offlineCtxSampleRate: offlineCtx.sampleRate,
    offlineCtxLength: offlineCtx.length,
    totalSecs, cpsBase,
  });

  // Replay every AudioWorklet module Strudel registered in the live context
  // into the offline context. Without this, AudioWorkletNodes created in
  // offlineCtx (which is how superdough actually makes sound) silently
  // fail because the processor name isn't registered.
  const workletURLs = Array.from(window.__registeredWorkletURLs || []);
  dremote('render', { phase: 'replaying-worklets', count: workletURLs.length, urls: workletURLs });
  for (const url of workletURLs) {
    try {
      await offlineCtx.audioWorklet.addModule(url);
    } catch (e) {
      dremote('render', { phase: 'worklet-replay-fail', url, error: String(e?.message || e) });
    }
  }

  // ── swap the SuperdoughAudioController so per-orbit reverb/delay/master
  // get rebuilt against offlineCtx, not the live context.
  //
  // Why: superdough caches a single SuperdoughAudioController at first call
  // (with the live AudioContext). It owns the per-orbit Orbit objects
  // (reverbNode, delayNode, summingNode, output gain) plus the
  // SuperdoughOutput (channelMerger → destinationGain → ac.destination).
  // All of those live in the live context. When we just swap the context,
  // new sources spawn in offlineCtx but try to connect to live-context
  // master nodes → cross-context error → silence (or mono-mixed wreck
  // when redirected to destination).
  //
  // Solution: instantiate a fresh controller bound to offlineCtx. Strudel
  // calls getSuperdoughAudioController() during webaudioOutput, finds the
  // new offline-context controller, and builds everything correctly.
  const liveController = getSuperdoughAudioController();
  const offlineController = new liveController.constructor(offlineCtx);
  setSuperdoughAudioController(offlineController);
  dremote('render', {
    phase: 'controller-swap',
    liveCtor: liveController.constructor?.name,
    offlineCtxIs: offlineController.audioContext === offlineCtx,
  });

  // Keep the redirect hack OFF — with the proper controller swap, all
  // connections should be within-offline-ctx now. If we hit any
  // cross-context attempts in the diagnostic, that's a follow-up bug.
  window.__crossContextRedirect = false;

  // Strudel reads getAudioContext() lazily for each note; setAudioContext
  // swaps the global ref so subsequent webaudioOutput calls target offline.
  try {
    setAudioContext(offlineCtx);
  } catch (e) {
    console.error('setAudioContext failed:', e);
  }
  // Diagnostic: did the swap actually take? If false, Strudel will keep
  // routing to the live context and the render will be silent.
  const ctxAfterSwap = getAudioContext();
  dremote('render', {
    phase: 'after-setAudioContext',
    swapSucceeded: offlineCtx === ctxAfterSwap,
    reportedSampleRate: ctxAfterSwap.sampleRate,
    reportedState: ctxAfterSwap.state || 'n/a',
    isOfflineCtx: ctxAfterSwap instanceof OfflineAudioContext,
  });

  // Snapshot per-context node creation counts BEFORE scheduling.
  const snapshotCtxCounts = (ctx) =>
    JSON.parse(JSON.stringify(ctx?.__ctxNodeCounts || {}));
  const beforeLive    = snapshotCtxCounts(liveCtx);
  const beforeOffline = snapshotCtxCounts(offlineCtx);
  const beforeConnStats = {
    total: window.__connectStats.total,
    crossContext: window.__connectStats.crossContext,
    crossContextErrors: window.__connectStats.crossContextErrors,
    toAnyDestination: window.__connectStats.toAnyDestination,
    toLiveDest: window.__connectStats.perDestinationCounts.get(liveCtx.destination) || 0,
    toOfflineDest: window.__connectStats.perDestinationCounts.get(offlineCtx.destination) || 0,
  };
  dremote('render', { phase: 'counts-before',
    live: beforeLive, offline: beforeOffline, conns: beforeConnStats });


  let timeCursor = 0;
  let scheduledHaps = 0;
  for (let i = 0; i < list.length; i++) {
    const snap = list[i];
    const sectionCyclesV = sectionCycles(snap);
    const cps = parseCps(snap.code) || cpsBase;
    const sectionSecs = sectionCyclesV / cps;
    showRenderLoader(`scheduling section ${i + 1}/${list.length} (${snap.label})`, 5 + (i / list.length) * 55);

    try {
      await evaluate(snap.code);
    } catch (e) {
      console.warn(`eval failed for ${snap.file}:`, e);
      timeCursor += sectionSecs;
      continue;
    }

    const sched = strudelRepl?.scheduler;
    const pattern = sched?.pattern;
    if (!pattern) { timeCursor += sectionSecs; continue; }

    let haps;
    try {
      haps = pattern.queryArc(0, sectionCyclesV, { _cps: cps, cyclist: 'neocyclist' });
    } catch (e) {
      console.warn('queryArc failed:', e);
      timeCursor += sectionSecs;
      continue;
    }

    let sectionHapsScheduled = 0, sectionHapErrors = [];
    let firstHapValue = null;
    for (const hap of haps) {
      if (!hap.hasOnset?.()) continue;
      try {
        const startCyc = Number(hap.whole.begin);
        const endCyc   = Number(hap.whole.end);
        const t   = timeCursor + (startCyc / cps);
        const dur = Math.max(0.001, (endCyc - startCyc) / cps);
        if (!firstHapValue) {
          firstHapValue = { t, dur, value: hap.value };
        }
        webaudioOutput(hap, 0, dur, cps, t);
        scheduledHaps++;
        sectionHapsScheduled++;
      } catch (e) {
        if (sectionHapErrors.length < 3) {
          sectionHapErrors.push(String(e?.message || e));
        }
      }
    }
    dremote('render', {
      phase: 'section-scheduled',
      i, file: snap.file, label: snap.label,
      cps, sectionCyclesV, sectionSecs,
      totalHaps: haps.length,
      onsetHaps: sectionHapsScheduled,
      errors: sectionHapErrors,
      firstHap: firstHapValue,
    });

    timeCursor += sectionSecs;
  }

  // Snapshot AFTER all haps have been scheduled but before render kicks off.
  // Diff against the BEFORE snapshot to know exactly which nodes Strudel
  // created in which context during its webaudioOutput() calls.
  const afterLive    = snapshotCtxCounts(liveCtx);
  const afterOffline = snapshotCtxCounts(offlineCtx);
  const afterConnStats = {
    total: window.__connectStats.total,
    crossContext: window.__connectStats.crossContext,
    crossContextErrors: window.__connectStats.crossContextErrors,
    toAnyDestination: window.__connectStats.toAnyDestination,
    toLiveDest: window.__connectStats.perDestinationCounts.get(liveCtx.destination) || 0,
    toOfflineDest: window.__connectStats.perDestinationCounts.get(offlineCtx.destination) || 0,
  };
  const diffCounts = (before, after) => {
    const out = {};
    const keys = new Set([...Object.keys(before), ...Object.keys(after)]);
    for (const k of keys) {
      const d = (after[k] || 0) - (before[k] || 0);
      if (d !== 0) out[k] = d;
    }
    return out;
  };
  const connDiff = diffCounts(beforeConnStats, afterConnStats);
  dremote('render', { phase: 'counts-after-scheduling',
    liveDiff:    diffCounts(beforeLive,    afterLive),
    offlineDiff: diffCounts(beforeOffline, afterOffline),
    connDiff,
    interpretation:
      (connDiff.toOfflineDest === undefined || connDiff.toOfflineDest === 0)
        ? `ZERO connections to offlineCtx.destination → audio never reaches offline output. ${connDiff.toLiveDest ? 'But '+connDiff.toLiveDest+' to liveCtx.destination — cached master in live context.' : ''} ${connDiff.crossContextErrors ? connDiff.crossContextErrors+' cross-context errors caught.' : ''}`
        : `${connDiff.toOfflineDest} connections to offlineCtx.destination — but audio still silent. Investigate node chain.`,
  });

  // ── progress polling during the render ──
  // Poll offlineCtx.currentTime — it advances as the render progresses, and
  // the setInterval fires while we're awaiting startRendering(). Works in
  // every implementation; OfflineAudioContext.suspend() doesn't (notably
  // absent in some Chromium builds — gives "is not a function" at runtime).
  showRenderLoader(`rendering ${scheduledHaps} events…`, 60);
  const renderStartPct = 60, renderEndPct = 90;
  const totalRenderSecs = totalSamples / sampleRate;
  const progressInterval = setInterval(() => {
    const t = offlineCtx.currentTime || 0;
    if (t <= 0 || t >= totalRenderSecs) return;
    const frac = Math.min(1, t / totalRenderSecs);
    const pct = renderStartPct + frac * (renderEndPct - renderStartPct);
    showRenderLoader(
      `rendering · ${fmtMMSS(t * 1000)} / ${fmtMMSS(totalRenderSecs * 1000)}`,
      pct,
    );
  }, 200);

  let buffer;
  try {
    buffer = await offlineCtx.startRendering();
  } catch (e) {
    console.error('startRendering failed:', e);
    setAudioContext(liveCtx);
    clearInterval(progressInterval);
    hideRenderLoader();
    alert('Offline render failed: ' + e.message);
    return;
  } finally {
    clearInterval(progressInterval);
  }

  // Restore live context and live controller
  setAudioContext(liveCtx);
  setSuperdoughAudioController(liveController);
  window.__crossContextRedirect = false;
  dremote('render', { phase: 'controller-restored', toLive: getSuperdoughAudioController() === liveController });

  // Diagnostic: peak/rms of the rendered buffer. Also sample a few windows
  // across the timeline to know if any audio appeared anywhere.
  {
    let peak = 0, sumSq = 0, n = 0;
    const windowPeaks = [];
    const numWindows = 10;
    const wSize = Math.floor(buffer.length / numWindows);
    for (let c = 0; c < buffer.numberOfChannels; c++) {
      const d = buffer.getChannelData(c);
      for (let i = 0; i < d.length; i++) {
        const v = Math.abs(d[i]);
        if (v > peak) peak = v;
        sumSq += d[i] * d[i];
        n++;
      }
      if (c === 0) {
        for (let w = 0; w < numWindows; w++) {
          let wp = 0;
          for (let i = w * wSize; i < Math.min((w + 1) * wSize, d.length); i++) {
            const v = Math.abs(d[i]);
            if (v > wp) wp = v;
          }
          windowPeaks.push(Number(wp.toFixed(4)));
        }
      }
    }
    const rms = Math.sqrt(sumSq / n);
    dremote('render', {
      phase: 'buffer-rendered',
      scheduledHaps,
      bufferLength: buffer.length,
      bufferChannels: buffer.numberOfChannels,
      bufferDurationSec: buffer.length / buffer.sampleRate,
      peak: Number(peak.toFixed(6)),
      rms: Number(rms.toFixed(6)),
      windowPeaks,
      verdict: peak === 0 ? 'ALL_ZERO' : (peak < 0.001 ? 'NEAR_SILENT' : 'HAS_AUDIO'),
    });
  }

  showRenderLoader('encoding WAV…', 92);

  const wav = audioBufferToWav(buffer);

  // ── auto-upload to server so Claude can grab the render without touching
  // the Downloads folder. Fire-and-forget — failure here doesn't block the
  // local download.
  showRenderLoader('uploading…', 96);
  try {
    const r = await fetch(`/save-wav?name=${encodeURIComponent(id)}`, {
      method: 'POST',
      body: wav,
      headers: { 'Content-Type': 'audio/wav' },
    });
    if (r.ok) {
      const j = await r.json().catch(() => ({}));
      dlog('render', `uploaded to ${j.path || 'server'} (${j.size || wav.byteLength} bytes)`);
    }
  } catch (e) {
    dwarn('render', 'save-wav upload failed:', e.message);
  }

  const blob = new Blob([wav], { type: 'audio/wav' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `toaster-strudel_${id}_album.wav`;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 200);

  // Stop Strudel's scheduler from auto-resuming with the last-evaluated
  // section pattern. Without this, after render the player would start
  // playing section 8 of whichever track was rendered.
  try { hush(); } catch (_) {}
  try { await evaluate('silence'); } catch (_) {}
  isPlaying = false;
  els.play.disabled = false;
  els.stop.disabled = true;
  setStatus('rendered · stopped');

  showRenderLoader(`done · ${scheduledHaps} events rendered`, 100);
  setTimeout(hideRenderLoader, 1800);
}

function audioBufferToWav(buffer) {
  const nch = buffer.numberOfChannels;
  const sr = buffer.sampleRate;
  const dataLen = buffer.length * nch * 2;
  const buf = new ArrayBuffer(44 + dataLen);
  const view = new DataView(buf);
  let o = 0;
  const wstr = (s) => { for (let i = 0; i < s.length; i++) view.setUint8(o++, s.charCodeAt(i)); };
  wstr('RIFF');
  view.setUint32(o, 36 + dataLen, true); o += 4;
  wstr('WAVE'); wstr('fmt ');
  view.setUint32(o, 16, true); o += 4;
  view.setUint16(o, 1, true); o += 2;
  view.setUint16(o, nch, true); o += 2;
  view.setUint32(o, sr, true); o += 4;
  view.setUint32(o, sr * nch * 2, true); o += 4;
  view.setUint16(o, nch * 2, true); o += 2;
  view.setUint16(o, 16, true); o += 2;
  wstr('data');
  view.setUint32(o, dataLen, true); o += 4;
  const channels = [];
  for (let c = 0; c < nch; c++) channels.push(buffer.getChannelData(c));
  for (let i = 0; i < buffer.length; i++) {
    for (let c = 0; c < nch; c++) {
      const s = Math.max(-1, Math.min(1, channels[c][i]));
      view.setInt16(o, s * 32767, true); o += 2;
    }
  }
  return buf;
}

function showRenderLoader(msg, pct) {
  const loaderEl = document.getElementById('loader');
  const stepEl = document.getElementById('loader-step');
  const fillEl = document.getElementById('loader-fill');
  if (!loaderEl) return;
  loaderEl.classList.remove('hide');
  if (stepEl) stepEl.textContent = msg;
  if (fillEl) fillEl.style.width = `${pct}%`;
}
function hideRenderLoader() {
  const loaderEl = document.getElementById('loader');
  if (loaderEl) loaderEl.classList.add('hide');
}

function encodeWav(left, right, sampleRate) {
  const numChannels = 2;
  const bitDepth = 16;
  const dataLength = left.length * numChannels * 2;
  const buf = new ArrayBuffer(44 + dataLength);
  const view = new DataView(buf);
  let o = 0;
  const wstr = (s) => { for (let i = 0; i < s.length; i++) view.setUint8(o++, s.charCodeAt(i)); };
  wstr('RIFF');
  view.setUint32(o, 36 + dataLength, true); o += 4;
  wstr('WAVE');
  wstr('fmt ');
  view.setUint32(o, 16, true); o += 4;
  view.setUint16(o, 1, true); o += 2;
  view.setUint16(o, numChannels, true); o += 2;
  view.setUint32(o, sampleRate, true); o += 4;
  view.setUint32(o, sampleRate * numChannels * bitDepth / 8, true); o += 4;
  view.setUint16(o, numChannels * bitDepth / 8, true); o += 2;
  view.setUint16(o, bitDepth, true); o += 2;
  wstr('data');
  view.setUint32(o, dataLength, true); o += 4;
  for (let i = 0; i < left.length; i++) {
    const l = Math.max(-1, Math.min(1, left[i]))  * 32767;
    const r = Math.max(-1, Math.min(1, right[i])) * 32767;
    view.setInt16(o, l, true); o += 2;
    view.setInt16(o, r, true); o += 2;
  }
  return buf;
}

// ── color system ───────────────────────────────────────────────
// Each event (hap) gets a color from its musical content:
//   - Pitched notes → hue from pitch class (C=0°, C#=30°, ..., B=330°),
//     saturation/lightness modulated by sound type, octave shifts lightness.
//   - Drums / untuned samples → role-based palette (kick, snare, hat, ...).
//   - Anything unrecognized → falls back to VOICE_PALETTE indexed by voice.
// Tune any of these to taste.

// Pitch-class hue around the wheel
const PITCH_HUE = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];
//                 C  C# D  D#  E    F   F#   G   G#   A   A#   B

// Sound family → saturation/lightness for pitched voices
const SOUND_MOD = {
  sawtooth: { s: 85, l: 55 },
  saw:      { s: 85, l: 55 },
  square:   { s: 90, l: 55 },
  triangle: { s: 65, l: 65 },
  sine:     { s: 45, l: 70 },
  piano:    { s: 70, l: 60 },
  kalimba:  { s: 80, l: 65 },
  marimba:  { s: 75, l: 60 },
  vibraphone:{s: 70, l: 70 },
  white:    { s: 0,  l: 80 },
};

// Untuned / drum samples → role-based colors
const DRUM_COLOR = {
  bd:  'hsl(345, 80%, 60%)',  // kick   — red
  sd:  'hsl(25,  85%, 60%)',  // snare  — orange
  rim: 'hsl(40,  80%, 65%)',
  cp:  'hsl(180, 75%, 60%)',  // clap   — cyan
  hh:  'hsl(85,  75%, 60%)',  // hat    — lime
  oh:  'hsl(75,  70%, 70%)',
  cy:  'hsl(265, 70%, 65%)',  // cymbal — purple
  sh:  'hsl(50,  60%, 70%)',  // shaker — gold
  tom: 'hsl(15,  70%, 55%)',
  perc:'hsl(200, 70%, 65%)',
};

function parseNote(note) {
  if (typeof note !== 'string') return null;
  const m = note.trim().match(/^([a-gA-G])([#b]?)(-?\d+)?$/);
  if (!m) return null;
  const [, letter, acc, oct] = m;
  const base = { c: 0, d: 2, e: 4, f: 5, g: 7, a: 9, b: 11 }[letter.toLowerCase()];
  const shift = acc === '#' ? 1 : acc === 'b' ? -1 : 0;
  const pc = (base + shift + 12) % 12;
  return { pc, octave: oct != null ? parseInt(oct, 10) : 4 };
}

function colorForHap(hap, fallback) {
  const v = hap?.value || {};
  const s = String(v.s || '').toLowerCase();

  // Sample name might be "bd:5" — strip the variant suffix
  const sBase = s.split(':')[0];

  // Untuned / drum samples
  if (DRUM_COLOR[sBase]) return DRUM_COLOR[sBase];

  // Pitched: try v.note first, then fall back to v.freq → note name
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

// ── per-voice particle system ──────────────────────────────────
// Each distinct voice in the running pattern (identified by its source
// location) gets a fixed angular position around the center. Particle
// colors come from `colorForHap()`; the voice anchor takes the color of
// its first hap (stable arc, melodic particles).
const VOICE_PALETTE = [
  '#9b6dff', '#5dd0ff', '#ff8a3d', '#5dffb1',
  '#ff7ad9', '#ffd56b', '#b16dff', '#6dffd0',
  '#ff5d8f', '#5dffe6', '#ffae5d', '#a5ff5d',
];
const voiceMap = new Map();    // locationKey -> { angle, color, lastHit, hits, intensity }
const particles = [];          // active particles
const PARTICLE_MAX = 800;

function registerVoiceHit(loc, hap) {
  const key = `${loc.start}-${loc.end}`;
  let v = voiceMap.get(key);
  const fallback = VOICE_PALETTE[voiceMap.size % VOICE_PALETTE.length];
  const hapColor = colorForHap(hap, fallback);
  if (!v) {
    const i = voiceMap.size;
    // golden-angle distribution gives even-ish spread regardless of count
    v = {
      angle: ((i * 137.508) % 360) * Math.PI / 180,
      color: hapColor,
      lastHit: 0,
      hits: 0,
      intensity: 0,
    };
    voiceMap.set(key, v);
  }
  v.lastHit = performance.now();
  v.hits++;
  v.intensity = Math.min(1, v.intensity + 0.4);
  // burst of particles from this voice's emitter point — each particle
  // takes the CURRENT hap's color, so melodic voices fan out in a gradient
  const gain = hap?.value?.gain ?? 0.5;
  const n = 4 + Math.floor(gain * 6);
  for (let i = 0; i < n; i++) spawnParticle(v, gain, hapColor);
  if (particles.length > PARTICLE_MAX) particles.splice(0, particles.length - PARTICLE_MAX);
}

function spawnParticle(voice, gain, color) {
  const speed = 0.6 + Math.random() * 1.4 + gain * 1.0;
  const spread = 0.35;
  const ang = voice.angle + (Math.random() - 0.5) * spread;
  particles.push({
    angle: voice.angle,
    radius: 0,
    speed,
    drift: (Math.random() - 0.5) * 0.015,
    life: 1,
    decay: 0.012 + Math.random() * 0.008,
    color: color || voice.color,
    size: 1.5 + Math.random() * 2.8,
    spawnAng: ang,
  });
}

function drawVoiceField() {
  const cssW = els.voices.clientWidth, cssH = els.voices.clientHeight;
  const cx = cssW / 2, cy = cssH / 2;
  const rMax = Math.min(cssW, cssH) * 0.48;

  // additive trails: don't fully clear — slight fade so trails persist
  ctxVoices.globalCompositeOperation = 'destination-out';
  ctxVoices.fillStyle = 'rgba(0,0,0,0.12)';
  ctxVoices.fillRect(0, 0, cssW, cssH);
  ctxVoices.globalCompositeOperation = 'lighter';

  // Update + draw particles — NO per-particle shadowBlur (was 800 software
  // shadows per frame). Glow comes from screen-blend overlap + the
  // composite-operation `lighter` already set above.
  ctxVoices.shadowBlur = 0;
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.radius += p.speed;
    p.spawnAng += p.drift;
    p.life -= p.decay;
    if (p.life <= 0 || p.radius > rMax) { particles.splice(i, 1); continue; }

    const x = cx + Math.cos(p.spawnAng) * p.radius;
    const y = cy + Math.sin(p.spawnAng) * p.radius;
    const a = p.life;

    ctxVoices.globalAlpha = a;
    ctxVoices.fillStyle = p.color;
    ctxVoices.beginPath();
    ctxVoices.arc(x, y, p.size * a, 0, Math.PI * 2);
    ctxVoices.fill();
  }
  ctxVoices.globalAlpha = 1;
  ctxVoices.globalCompositeOperation = 'source-over';

  // Voice anchor arcs — also dropped shadowBlur (was per-voice). The
  // screen blend mode + colored fills give enough visual interest.
  const now = performance.now();
  ctxVoices.shadowBlur = 0;
  for (const v of voiceMap.values()) {
    const age = (now - v.lastHit) / 1000;
    if (age > 8) continue;
    const liveness = Math.max(0, 1 - age / 8);
    v.intensity *= 0.96;
    const r = 24 + liveness * 6;
    const arcLen = 0.25 + v.intensity * 0.4;
    ctxVoices.strokeStyle = v.color;
    ctxVoices.lineWidth = 1.4 + v.intensity * 2;
    ctxVoices.globalAlpha = 0.4 + liveness * 0.6;
    ctxVoices.beginPath();
    ctxVoices.arc(cx, cy, r, v.angle - arcLen, v.angle + arcLen);
    ctxVoices.stroke();
  }
  ctxVoices.globalAlpha = 1;
}

const HELD_MIN_SEC = 0.5;   // notes ≥ this stay lit + pulse; shorter ones flash
// Track gains sit ~0.18–0.6; normalise over that so quiet=pale, loud=full colour.
const GAIN_FULL = 0.55;

function flashRange(start, end, color, opts = {}) {
  const { durSec = 0, gain = 0.4, attackSec = 0, beatSec = 0.6, pulseDelay = 0 } = opts;
  const held = durSec >= HELD_MIN_SEC;
  const intensity = Math.max(0, Math.min(1, gain / GAIN_FULL));
  // Swell-in can't outlast the note itself.
  const attackDur = Math.max(0, Math.min(attackSec, durSec));
  for (let i = start; i < end; i++) {
    const span = charSpans[i];
    if (!span) continue;
    if (color) span.style.setProperty('--lit', color);
    span.style.setProperty('--intensity', intensity.toFixed(3));
    // Cancel any pending un-light so an earlier note's timer can't cut this
    // one short (matters for held notes that outlive a previous flash).
    if (span.__litTimer) { clearTimeout(span.__litTimer); span.__litTimer = null; }
    span.classList.remove('lit', 'held');
    void span.offsetWidth;   // restart the animation
    if (held) {
      span.style.setProperty('--held-dur', `${beatSec.toFixed(3)}s`);
      span.style.setProperty('--attack-dur', `${attackDur.toFixed(3)}s`);
      span.style.setProperty('--pulse-delay', `${pulseDelay.toFixed(3)}s`);
      span.classList.add('held');
      span.__litTimer = setTimeout(() => releaseHeld(span), durSec * 1000);
    } else {
      span.classList.add('lit');
      span.__litTimer = setTimeout(() => {
        span.classList.remove('lit');
        span.__litTimer = null;
      }, 500);
    }
  }
}

// A held note ended — drop the steady glow; the base-span text-shadow
// transition (styles.css) eases it back out rather than hard-cutting.
function releaseHeld(span) {
  span.classList.remove('held');
  span.__litTimer = null;
}

function clearHighlights() {
  for (const span of charSpans) {
    if (!span) continue;
    if (span.__litTimer) { clearTimeout(span.__litTimer); span.__litTimer = null; }
    span.classList.remove('lit', 'held');
  }
}

// ── section timeline (file-backed) ──────────────────────────
// Sections live as files on disk in `tracks/<id>/NN.strudel` (01.strudel,
// 02.strudel, ...). The player auto-discovers them by trying sequential
// numbers until a 404. This means sections are durable, git-trackable,
// editable in any text editor, and you can write them with the same tools
// you write the live track.
//
// The live file `tracks/<id>.strudel` is the editable working copy. Clicking
// a section dot evaluates that section's code without overwriting the
// live file.
const sections = new Map();  // trackId → [{ index, file, code, label }]

function getSections(id) { return sections.get(id) || []; }

async function fetchSections(id) {
  // The server enumerates tracks/<id>/ for us — it has filesystem access; the
  // browser can't list a directory, which is why this used to blind-probe
  // 01,02,03… until a 404. Now one request returns the real section list with
  // code + ascii inlined → no 404s. Manifest `cycles`/`label` still override
  // the per-file @cycles directive and header title.
  let data = { manifest: null, sections: [] };
  try {
    const res = await fetch(`/sections?track=${encodeURIComponent(id)}`, { cache: 'no-cache' });
    if (res.ok) data = await res.json();
  } catch (e) {
    dwarn('sections', `discovery failed for ${id}:`, e.message);
  }

  // Accept both `sections` (preferred) and `slots` (legacy) in manifest
  const manSections = data.manifest?.sections || data.manifest?.slots;
  const list = data.sections.map((s, idx) => {
    const header = parseHeader(s.code);
    const cyclesMatch = s.code.match(/\/\/\s*@cycles\s+(\d+)/i);
    const sectionMan = manSections?.[idx] || null;
    const cycles = sectionMan?.cycles ?? (cyclesMatch ? parseInt(cyclesMatch[1], 10) : null);
    return {
      index: idx + 1,
      file: s.file,
      code: s.code,
      ascii: s.ascii || '',
      cycles,
      label: sectionMan?.label || header.title || `v${idx + 1}`,
    };
  });
  sections.set(id, list);
  return list;
}

function sectionCycles(snap) { return snap?.cycles || AUTO_ADVANCE_CYCLES; }
function sectionSeconds(snap) { return sectionCycles(snap) / (cpsOverride || currentCps || 0.4); }

let viewedIndex = -1;  // -1 = live (track latest); else index into history
let replayTimer = null;

// Auto-advance: cycles through sections in order, looping. Synced to
// cycle boundaries so each version gets a full song-length to play.
// Default ON — most users want a full album experience; persist so anyone
// who turns it off stays off.
let autoAdvance = localStorage.getItem('toaster-strudel:auto-advance') !== 'false';
let autoAdvanceTimer = null;
let autoAdvanceProgress = null;

// When you click a section dot, do we reset the section timer to its
// full duration (true), or keep counting down from the previous timer
// (false)? Default on — most natural "I picked this section, give it its
// full play". User can toggle with Z or the ↺ button.
let resetOnSwap = localStorage.getItem('toaster-strudel:reset-on-swap') !== 'false';
const SECTION_LEN_OPTIONS = [4, 8, 16, 32, 64, 128];
let AUTO_ADVANCE_CYCLES = parseInt(localStorage.getItem('toaster-strudel:section-len') || '32', 10);
function autoAdvanceSeconds() { return AUTO_ADVANCE_CYCLES / (cpsOverride || currentCps || 0.4); }

function cycleSectionLen(delta = 1) {
  const i = SECTION_LEN_OPTIONS.indexOf(AUTO_ADVANCE_CYCLES);
  const next = SECTION_LEN_OPTIONS[(i + delta + SECTION_LEN_OPTIONS.length) % SECTION_LEN_OPTIONS.length];
  AUTO_ADVANCE_CYCLES = next;
  localStorage.setItem('toaster-strudel:section-len', String(next));
  updateSlotPill();
  if (autoAdvance) startAutoAdvance();
  updateTimeReadout();
}

function updateSlotPill() {
  const btn = document.getElementById('tl-section-len');
  if (!btn) return;
  const list = getSections(TRACKS[currentIndex]?.id);
  const cur = list?.[viewedIndex < 0 ? 0 : viewedIndex];
  if (cur?.cycles) {
    btn.textContent = `${cur.cycles}c`;
    btn.classList.add('from-config');
    btn.title = `${cur.cycles} cycles for THIS section (from manifest.json or // @cycles directive in ${cur.file}).\n\n` +
      `Edit tracks/${TRACKS[currentIndex].id}/manifest.json to change per-section values.\n` +
      `Click to change the global fallback (${AUTO_ADVANCE_CYCLES}c) for sections without overrides.`;
  } else {
    btn.textContent = `${AUTO_ADVANCE_CYCLES}c`;
    btn.classList.remove('from-config');
    btn.title = `${AUTO_ADVANCE_CYCLES} cycles (global default — this section has no override).\n\n` +
      `Click to cycle. To set this section specifically, add 'cycles': N in tracks/${TRACKS[currentIndex]?.id}/manifest.json or '// @cycles N' in ${cur?.file || 'the .strudel file'}.`;
  }
}

function toggleAutoAdvance() {
  autoAdvance = !autoAdvance;
  localStorage.setItem('toaster-strudel:auto-advance', String(autoAdvance));
  if (autoAdvance) {
    els.tlAuto.classList.add('active');
    if (isPlaying) startAutoAdvance();
  } else {
    els.tlAuto.classList.remove('active');
    stopAutoAdvance();
  }
}

// Reflect persisted state on the auto-advance button at boot.
function applyAutoAdvanceUI() {
  if (autoAdvance) els.tlAuto?.classList.add('active');
  else els.tlAuto?.classList.remove('active');
}

function toggleResetOnSwap() {
  resetOnSwap = !resetOnSwap;
  localStorage.setItem('toaster-strudel:reset-on-swap', String(resetOnSwap));
  applyResetUI();
  dlog('viz', `reset-on-swap ${resetOnSwap ? 'ON' : 'OFF'}`);
}
function applyResetUI() {
  const btn = document.getElementById('tl-reset');
  if (!btn) return;
  btn.classList.toggle('active', resetOnSwap);
  btn.title = resetOnSwap
    ? 'Reset-on-swap ON — clicking a section restarts its full duration (Z)'
    : 'Reset-on-swap OFF — clicking a section keeps the running section timer (Z)';
}

function startAutoAdvance() {
  stopAutoAdvance();
  scheduleNextAdvance();
}

function scheduleNextAdvance() {
  const list = getSections(TRACKS[currentIndex].id);
  if (!list.length) return;
  const cur = viewedIndex < 0 ? 0 : viewedIndex;
  const secs = sectionSeconds(list[cur]);
  nextSectionAt = performance.now() + secs * 1000;
  startAutoAdvanceProgress(secs);
  autoAdvanceTimer = setTimeout(async () => {
    if (!autoAdvance) return;
    const list2 = getSections(TRACKS[currentIndex].id);
    if (!list2.length) return;
    const curIdx = viewedIndex < 0 ? 0 : viewedIndex;
    if (curIdx + 1 >= list2.length) {
      // End of track — advance to the next track's first section.
      // This is what makes the album play as one continuous flow.
      await advanceToNextTrack();
    } else {
      await jumpToSection(curIdx + 1, { auto: true });
    }
    if (autoAdvance) scheduleNextAdvance();
  }, secs * 1000);
}

async function advanceToNextTrack() {
  const nextTrackIdx = (currentIndex + 1) % TRACKS.length;
  dlog('track', `end of ${TRACKS[currentIndex].id} → ${TRACKS[nextTrackIdx].id}`);
  await loadTrack(nextTrackIdx);
  // After loadTrack, viewedIndex is reset and section 1 is current.
  if (isPlaying && !isMuted) {
    await evaluate(transformCode(currentCode));
    hookPattern();
  }
}

function stopAutoAdvance() {
  if (autoAdvanceTimer) { clearInterval(autoAdvanceTimer); autoAdvanceTimer = null; }
  nextSectionAt = 0;
  stopAutoAdvanceProgress();
}

function startAutoAdvanceProgress(totalSecs) {
  stopAutoAdvanceProgress();
  // Insert a progress bar into the timeline strip parent
  let bar = document.querySelector('.tl-progress');
  if (!bar) {
    bar = document.createElement('div');
    bar.className = 'tl-progress';
    document.getElementById('timeline').appendChild(bar);
  }
  const startedAt = performance.now();
  autoAdvanceProgress = setInterval(() => {
    const elapsed = (performance.now() - startedAt) / 1000;
    const frac = (elapsed % totalSecs) / totalSecs;
    bar.style.width = (frac * 100) + '%';
  }, 100);
}

function stopAutoAdvanceProgress() {
  if (autoAdvanceProgress) { clearInterval(autoAdvanceProgress); autoAdvanceProgress = null; }
  const bar = document.querySelector('.tl-progress');
  if (bar) bar.remove();
}

function renderTimeline() {
  const id = TRACKS[currentIndex].id;
  const list = getSections(id);
  els.tlStrip.innerHTML = '';
  const activeIdx = viewedIndex;
  updateSlotPill();
  list.forEach((snap, i) => {
    const dot = document.createElement('div');
    dot.className = 'tl-dot' + (i === activeIdx ? ' active' : '') + (autoAdvance && i === activeIdx ? ' advancing' : '');
    const cycLabel = snap.cycles ? `${snap.cycles}c` : `${AUTO_ADVANCE_CYCLES}c (default)`;
    dot.title = `${snap.file}\n${snap.label}\n${cycLabel} · ${sectionSeconds(snap).toFixed(1)}s`;
    dot.addEventListener('click', () => jumpToSection(i));
    els.tlStrip.appendChild(dot);
  });
  requestAnimationFrame(() => {
    const active = els.tlStrip.querySelector('.tl-dot.active');
    if (active) active.scrollIntoView({ inline: 'center', block: 'nearest' });
  });
  if (autoAdvance) {
    els.tlInfo.textContent = `auto · ${activeIdx + 1}/${list.length}`;
    els.tlInfo.classList.remove('frozen'); els.tlInfo.classList.remove('live');
  } else if (viewedIndex < 0) {
    els.tlInfo.textContent = `live · ${list.length} sections`;
    els.tlInfo.classList.remove('frozen'); els.tlInfo.classList.add('live');
  } else {
    els.tlInfo.textContent = `${list[activeIdx]?.file || `${activeIdx+1}/${list.length}`}`;
    els.tlInfo.classList.add('frozen'); els.tlInfo.classList.remove('live');
  }
}

async function jumpToSection(index, opts = {}) {
  const id = TRACKS[currentIndex].id;
  const list = getSections(id);
  if (!list.length) return;
  const clamped = Math.max(0, Math.min(list.length - 1, index));
  const t0 = performance.now();
  dlog('section', `jump → ${list[clamped]?.file} (section ${clamped + 1}/${list.length})`);
  viewedIndex = clamped;
  const snap = list[clamped];
  currentCode = snap.code;
  currentCps = parseCps(snap.code) ?? currentCps;
  cpsOverride = null;
  updateBpm();
  const header = parseHeader(snap.code);
  els.title.textContent = header.title || els.title.textContent;
  if (els.notes) els.notes.textContent = header.notes;
  renderCode(snap.code);
  setAscii(snap.ascii || '');
  flashPatch(snap.file);
  renderTimeline();
  if (bcVisualizer && bcPresetKeys.length) {
    bcPresetIdx = (clamped * 13 + 7) % bcPresetKeys.length;
    bcLoadPreset(bcPresetIdx);
  }
  if (isPlaying && !isMuted) {
    const te = performance.now();
    await evaluate(transformCode(snap.code));
    dlog('section', `evaluate ${snap.file} took ${(performance.now() - te).toFixed(0)}ms`);
    hookPattern();
  }
  // If this was a manual jump and reset-on-swap is on, restart the section
  // timer with the new section's full duration. Auto jumps from the
  // scheduler already re-schedule themselves naturally.
  if (!opts.auto && resetOnSwap && autoAdvance && isPlaying) {
    stopAutoAdvance();
    scheduleNextAdvance();
  }
  dlog('section', `total jump ${(performance.now() - t0).toFixed(0)}ms (manual=${!opts.auto})`);
}

function setAscii(text) {
  const el = document.getElementById('ascii-overlay');
  if (!el) return;
  el.textContent = text;
  if (text) {
    el.classList.add('show');
    // Fade out after a few seconds so it doesn't permanently cover the viz
    clearTimeout(setAscii._t);
    el.style.opacity = '0.85';
    setAscii._t = setTimeout(() => { el.style.opacity = '0.18'; }, 4000);
  } else {
    el.classList.remove('show');
  }
}

function stepSection(delta) {
  const id = TRACKS[currentIndex].id;
  const list = getSections(id);
  if (!list.length) return;
  const cur = viewedIndex < 0 ? 0 : viewedIndex;
  let next = cur + delta;
  if (next < 0) next = list.length - 1;
  if (next >= list.length) next = 0;
  jumpToSection(next);
}

function toggleReplay() {
  if (replayTimer) {
    clearInterval(replayTimer);
    replayTimer = null;
    els.tlReplay.textContent = '⏵⏵';
    return;
  }
  const id = TRACKS[currentIndex].id;
  const list = getSections(id);
  if (!list.length) return;
  let i = 0;
  els.tlReplay.textContent = '■';
  replayTimer = setInterval(async () => {
    if (i >= list.length) { toggleReplay(); return; }
    await jumpToSection(i);
    i++;
  }, 3500);
}

// "Clear" no longer makes sense for file-backed sections — those are managed
// on disk. Kept as a no-op that just re-fetches the directory listing.
async function clearHistory() {
  const id = TRACKS[currentIndex].id;
  await fetchSections(id);
  renderTimeline();
  flashPatch('refreshed');
}

// ── poll for file changes (live file + sections dir) ──────
const POLL_MS = 700;
const SNAPSHOT_POLL_MS = 30000; // 30s — was 2500 (caused HEAD spam contending with audio thread)
let lastSectionCount = 0;

async function pollForChanges() {
  if (!TRACKS[currentIndex]) return;
  if (viewedIndex >= 0) return; // viewing a section — don't auto-follow live
  try {
    const res = await fetch(`../tracks/${TRACKS[currentIndex].id}.strudel`, { cache: 'no-cache' });
    if (!res.ok) return;
    const code = await res.text();
    if (code !== currentCode) {
      currentCode = code;
      currentCps = parseCps(code) ?? currentCps;
      cpsOverride = null;
      updateBpm();
      const header = parseHeader(code);
      els.title.textContent = header.title || els.title.textContent;
      if (els.notes) els.notes.textContent = header.notes;
      renderCode(code);
      flashPatch();
      if (isPlaying && !isMuted) {
        await evaluate(transformCode(code));
        hookPattern();
      }
    }
  } catch (_) { /* network blip */ }
}

// Detects sections added/removed on disk so the timeline updates live.
// The server enumerates the folder (no 404 probing), so we just re-list and
// re-render when the section count actually changes.
async function pollForSections() {
  if (!TRACKS[currentIndex]) return;
  const id = TRACKS[currentIndex].id;
  const known = getSections(id).length;
  const list = await fetchSections(id);
  if (list.length !== lastSectionCount) {
    lastSectionCount = list.length;
    renderTimeline();
    if (list.length > 0 && known !== 0) flashPatch(`${list.length} sections`);
  }
}

setInterval(pollForChanges, POLL_MS);
setInterval(pollForSections, SNAPSHOT_POLL_MS);

function codeToHash(code) {
  const bytes = new TextEncoder().encode(code);
  let bin = '';
  for (const b of bytes) bin += String.fromCharCode(b);
  return encodeURIComponent(btoa(bin));
}

// ── transport ─────────────────────────────────────────────────
async function play() {
  if (!strudelReady) { setStatus('not ready yet'); return; }
  if (!currentCode) return;
  try {
    if (strudelCtx?.state === 'suspended') {
      dlog('audio', 'AudioContext suspended → resume()');
      try { await strudelCtx.resume(); } catch (_) {}
      dlog('audio', 'AudioContext state now:', strudelCtx?.state);
    }
    // Set up the ring buffer once the context is alive — first play() is the
    // earliest reliable moment the AudioContext is running and the worklet
    // module can be loaded.
    if (!ringNode) setupRingBuffer();
    const t0 = performance.now();
    await evaluate(transformCode(currentCode));
    dlog('eval', `play() evaluate took ${(performance.now() - t0).toFixed(0)}ms`);
    hookPattern();
    isPlaying = true;
    isMuted = false;
    playStartedAt = performance.now();
    setStatus('playing');
    els.play.disabled = true;
    els.stop.disabled = false;
    els.codePre.classList.remove('can-audition');
    updateTimeReadout();
    if (autoAdvance && !autoAdvanceTimer) startAutoAdvance();
  } catch (err) {
    console.error(err);
    setStatus(`error: ${err.message.slice(0, 40)}`);
    dwarn('eval', 'play failed:', err.message);
  }
}

function stop() {
  hush();
  clearHighlights();
  isPlaying = false;
  stopAutoAdvance();
  setStatus('stopped');
  els.play.disabled = false;
  els.stop.disabled = true;
  els.codePre.classList.add('can-audition');
}

async function toggleMute() {
  if (!isPlaying) return;
  if (isMuted) {
    await evaluate(transformCode(currentCode));
    isMuted = false;
    setStatus('playing');
  } else {
    await evaluate('silence');
    isMuted = true;
    setStatus('muted');
  }
}

async function nudgeCps(deltaFactor) {
  const base = cpsOverride || currentCps;
  cpsOverride = Math.max(0.1, Math.min(4, base * deltaFactor));
  updateBpm();
  if (isPlaying && !isMuted) await play();
}

// ── visualisers ───────────────────────────────────────────────
const ctxMandala = els.mandala.getContext('2d');
const ctxSpec    = els.spec.getContext('2d');
const ctxWave    = els.wave.getContext('2d');
const ctxVoices  = els.voices.getContext('2d');

function resizeCanvases() {
  for (const c of [els.mandala, els.spec, els.wave, els.voices]) {
    const r = c.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    c.width = r.width * dpr;
    c.height = r.height * dpr;
    c.getContext('2d').setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  // Butterchurn manages its own canvas dimensions via setRendererSize
  bcResize();
}
resizeCanvases();
window.addEventListener('resize', () => { resizeCanvases(); bcResize(); });
// Catch parent-container size changes (sidebar toggles, layout reflow, etc.)
// that don't fire window.resize but still shift the canvas's CSS box.
const vizEl = document.getElementById('viz');
if (vizEl && 'ResizeObserver' in window) {
  new ResizeObserver(() => { resizeCanvases(); bcResize(); }).observe(vizEl);
}

// onset / beat detection (very rough — RMS spike)
let lastRms = 0;
let lastBeatAt = 0;
function maybePulseBeat(rms) {
  const now = performance.now();
  if (rms - lastRms > 0.06 && now - lastBeatAt > 250) {
    els.beatRing.classList.remove('pulse');
    void els.beatRing.offsetWidth;  // restart animation
    els.beatRing.classList.add('pulse');
    lastBeatAt = now;
  }
  lastRms = lastRms * 0.7 + rms * 0.3;
}

// Per-layer frame timing. Long frames starve audio thread → "skip query: too
// late". Butterchurn is the prime suspect (GPU shaders). Toggle B to disable
// it entirely as a diagnostic A/B test — if glitches vanish, it's confirmed.
let bcDisabled = localStorage.getItem('toaster-strudel:bc-disabled') === '1';
dlog('init', bcDisabled ? 'Butterchurn DISABLED (press B to enable)' : 'Butterchurn enabled (press B to disable for A/B)');

let frameStatsAcc = { slowFrames: 0, maxMs: 0, sampledFrames: 0, lastReport: 0, bcTotal: 0, restTotal: 0 };
function draw() {
  requestAnimationFrame(draw);
  if (!analyser) return;
  if (!isPlaying || isMuted) {
    if (els.vizVoicesCount) els.vizVoicesCount.textContent = '';
    return;
  }
  const fStart = performance.now();
  let bcStart = fStart;
  // Butterchurn rendered at 30fps (every other frame) so the heavy shader
  // pass only runs half as often. Our cheap visualizers stay at 60fps.
  if (bcVisualizer && !bcDisabled) {
    if (!draw._bcSkip) { bcVisualizer.render(); draw._bcSkip = true; }
    else { draw._bcSkip = false; }
  }
  const bcEnd = performance.now();
  drawSpectrogram();
  drawMandala();
  drawVoiceField();
  drawWaveform();
  if (els.vizVoicesCount) {
    const now = performance.now();
    let active = 0;
    for (const v of voiceMap.values()) if (now - v.lastHit < 8000) active++;
    els.vizVoicesCount.textContent = active > 0 ? `${active} voice${active === 1 ? '' : 's'} live` : '';
  }
  const ms = performance.now() - fStart;
  frameStatsAcc.sampledFrames++;
  frameStatsAcc.bcTotal += (bcEnd - bcStart);
  frameStatsAcc.restTotal += (performance.now() - bcEnd);
  if (ms > frameStatsAcc.maxMs) frameStatsAcc.maxMs = ms;
  if (ms > 33) frameStatsAcc.slowFrames++;
  if (fStart - frameStatsAcc.lastReport > 5000) {
    const f = frameStatsAcc.sampledFrames || 1;
    const avgBc = (frameStatsAcc.bcTotal / f).toFixed(1);
    const avgRest = (frameStatsAcc.restTotal / f).toFixed(1);
    if (frameStatsAcc.slowFrames > 0 || frameStatsAcc.maxMs > 50) {
      dwarn('draw', `last 5s: ${frameStatsAcc.slowFrames} slow frames (>33ms), peak ${frameStatsAcc.maxMs.toFixed(0)}ms · avg butterchurn ${avgBc}ms · avg rest ${avgRest}ms / ${f} sampled`);
    } else {
      dlog('draw', `last 5s: smooth · avg butterchurn ${avgBc}ms · avg rest ${avgRest}ms · peak ${frameStatsAcc.maxMs.toFixed(0)}ms / ${f} frames`);
    }
    frameStatsAcc = { slowFrames: 0, maxMs: 0, sampledFrames: 0, lastReport: fStart, bcTotal: 0, restTotal: 0 };
  }
}

// Scroll event logging — confirms if glitches correlate with scroll
let lastScrollLog = 0;
window.addEventListener('scroll', () => {
  const now = performance.now();
  if (now - lastScrollLog > 200) {
    dlog('scroll', 'event');
    lastScrollLog = now;
  }
}, { passive: true });
window.addEventListener('wheel', () => {
  const now = performance.now();
  if (now - lastScrollLog > 200) {
    dlog('scroll', 'wheel');
    lastScrollLog = now;
  }
}, { passive: true });

// PERF: removed per-bar shadowBlur (was being applied 144 times per frame —
// canvas2d shadow is software-rendered, hugely expensive). Now one glow
// pass per frame via globalCompositeOperation. Bars reduced 144 → 72.
// Mirrored inner bars dropped — barely visible, not worth the cost.
function drawMandala() {
  const cssW = els.mandala.clientWidth, cssH = els.mandala.clientHeight;
  const cx = cssW / 2, cy = cssH / 2;
  const r0 = Math.min(cssW, cssH) * 0.18;
  const rMax = Math.min(cssW, cssH) * 0.45;

  const bins = new Uint8Array(analyser.frequencyBinCount);
  analyser.getByteFrequencyData(bins);

  const sr = strudelCtx?.sampleRate || 44100;
  const nyquist = sr / 2;
  const bars = 72;
  const minF = 30, maxF = 12000;

  let rmsSum = 0;

  ctxMandala.clearRect(0, 0, cssW, cssH);
  ctxMandala.save();
  ctxMandala.translate(cx, cy);
  ctxMandala.rotate(performance.now() / 30000);

  const accent  = themeColor('accent');
  const accent2 = themeColor('accent2');
  const warm    = themeColor('warm');

  // ONE stroke style for all bars (gradient computed once, not per-bar)
  ctxMandala.strokeStyle = accent;
  ctxMandala.lineWidth = 2.2;
  ctxMandala.lineCap = 'round';
  // No per-bar shadowBlur. We rely on screen blend mode + the spectrogram
  // layer behind for visual depth. Way cheaper.
  ctxMandala.shadowBlur = 0;

  ctxMandala.beginPath();
  for (let i = 0; i < bars; i++) {
    const f = minF * Math.pow(maxF / minF, i / (bars - 1));
    const idx = Math.min(bins.length - 1, Math.floor(f / nyquist * bins.length));
    const v = bins[idx] / 255;
    rmsSum += v * v;
    if (v < 0.03) continue;

    const angle = (i / bars) * Math.PI * 2;
    const len = Math.pow(v, 1.2) * (rMax - r0);
    const x1 = Math.cos(angle) * r0;
    const y1 = Math.sin(angle) * r0;
    const x2 = Math.cos(angle) * (r0 + len);
    const y2 = Math.sin(angle) * (r0 + len);
    ctxMandala.moveTo(x1, y1);
    ctxMandala.lineTo(x2, y2);
  }
  ctxMandala.stroke();

  // Inner ring — one path
  ctxMandala.lineWidth = 1;
  ctxMandala.strokeStyle = `${accent}55`;
  ctxMandala.beginPath();
  ctxMandala.arc(0, 0, r0, 0, Math.PI * 2);
  ctxMandala.stroke();

  ctxMandala.restore();
  maybePulseBeat(Math.sqrt(rmsSum / bars));
}

// PERF: scroll the canvas left by 1px using drawImage (GPU-only) instead of
// getImageData/putImageData (which forces a GPU→CPU readback every frame —
// was ~70ms per call on the user's setup).
function drawSpectrogram() {
  const cssW = els.spec.clientWidth, cssH = els.spec.clientHeight;
  // Shift the existing image one pixel to the left using drawImage
  ctxSpec.globalCompositeOperation = 'copy';
  ctxSpec.drawImage(els.spec, -1, 0);
  ctxSpec.globalCompositeOperation = 'source-over';

  const bins = new Uint8Array(analyser.frequencyBinCount);
  analyser.getByteFrequencyData(bins);

  const sr = strudelCtx?.sampleRate || 44100;
  const nyquist = sr / 2;
  const minF = 30, maxF = 16000;
  const x = cssW - 1;
  ctxSpec.clearRect(x, 0, 1, cssH);

  // Bucket pixels into 4-row strips to cut fillRect calls 4x
  const strip = 4;
  const a2 = themeColor('accent2');
  for (let y = 0; y < cssH; y += strip) {
    const f = minF * Math.pow(maxF / minF, 1 - y / cssH);
    const idx = Math.min(bins.length - 1, Math.floor(f / nyquist * bins.length));
    const v = bins[idx] / 255;
    if (v < 0.04) continue;
    const a = Math.pow(v, 0.9);
    ctxSpec.fillStyle = `${a2}${Math.floor(a * 255).toString(16).padStart(2, '0')}`;
    ctxSpec.fillRect(x, y, 1, strip);
  }
}

function drawWaveform() {
  const cssW = els.wave.clientWidth, cssH = els.wave.clientHeight;
  ctxWave.clearRect(0, 0, cssW, cssH);

  const wave = new Uint8Array(analyser.fftSize);
  analyser.getByteTimeDomainData(wave);

  ctxWave.strokeStyle = themeColor('warm');
  ctxWave.lineWidth = 1.2;
  ctxWave.shadowBlur = 0; // was 8 — software shadow per stroke is expensive
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
draw();

// ── help overlay ───────────────────────────────────────────────
function openHelp()  { els.help.hidden = false; }
function closeHelp() { els.help.hidden = true; }

// ── keybinds ──────────────────────────────────────────────────
window.addEventListener('keydown', (e) => {
  // Don't hijack typing in the dropdown.
  if (e.target.tagName === 'INPUT') return;

  switch (e.code) {
    case 'Space':
      e.preventDefault();
      isPlaying ? stop() : play();
      return;
    case 'ArrowLeft':
      e.preventDefault();
      loadTrack(currentIndex - 1);
      return;
    case 'ArrowRight':
      e.preventDefault();
      loadTrack(currentIndex + 1);
      return;
    case 'Escape':
      closeHelp();
      return;
  }

  switch (e.key) {
    case '1': case '2': case '3': case '4':
      loadTrack(parseInt(e.key, 10) - 1);
      return;
    case 'r': case 'R':
      loadTrack(currentIndex);
      return;
    case 't': case 'T':
      cycleTheme();
      return;
    case 'm': case 'M':
      toggleMute();
      return;
    case '?':
      openHelp();
      return;
    case '[':
      nudgeCps(0.9);
      return;
    case ']':
      nudgeCps(1.1);
      return;
    // 'c' keybind removed — code panel is always visible in new layout
    case ',':
      stepSection(-1);
      return;
    case '.':
      stepSection(1);
      return;
    case '\\':
      toggleReplay();
      return;
    case 'k': case 'K':
      clearHistory();
      return;
    case 'a': case 'A':
      toggleAutoAdvance();
      return;
    case 'b': case 'B':
      bcDisabled = !bcDisabled;
      localStorage.setItem('toaster-strudel:bc-disabled', bcDisabled ? '1' : '0');
      dlog('viz', `Butterchurn ${bcDisabled ? 'DISABLED' : 'enabled'} — A/B for audio glitches`);
      if (els.butterchurn) els.butterchurn.style.opacity = bcDisabled ? '0' : '0.85';
      return;
    case 'z': case 'Z':
      toggleResetOnSwap();
      return;
  }
});


// ── click wiring ──────────────────────────────────────────────
els.select.addEventListener('change', () => {
  const idx = TRACKS.findIndex((t) => t.id === els.select.value);
  if (idx >= 0) loadTrack(idx);
});
els.play  .addEventListener('click', play);
els.stop  .addEventListener('click', stop);
els.prev  .addEventListener('click', () => loadTrack(currentIndex - 1));
els.next  .addEventListener('click', () => loadTrack(currentIndex + 1));
els.reload.addEventListener('click', () => loadTrack(currentIndex));
els.codePre.addEventListener('click', onCodeClick);
els.codePre.classList.add('can-audition');   // player boots stopped
els.themeBtn.addEventListener('click', cycleTheme);
els.helpBtn .addEventListener('click', openHelp);
els.helpClose.addEventListener('click', closeHelp);
els.help    .addEventListener('click', (e) => { if (e.target === els.help) closeHelp(); });
els.tlPrev.addEventListener('click', () => stepSection(-1));
els.tlNext.addEventListener('click', () => stepSection(1));
els.tlAuto.addEventListener('click', toggleAutoAdvance);
els.tlReplay.addEventListener('click', toggleReplay);
els.tlClear.addEventListener('click', clearHistory);
const recBtn = document.getElementById('rec-btn');
if (recBtn) recBtn.addEventListener('click', toggleRecord);
const renderBtn = document.getElementById('render-btn');
if (renderBtn) renderBtn.addEventListener('click', async () => {
  try {
    // Warmup: on a fresh page-load the worklet registry is empty (Strudel
    // only registers its worklets on first play). Without this, the very
    // first Render produces silence because there are no worklets to
    // replay into offlineCtx. We do a brief play→stop dance to populate
    // the registry before kicking off the render.
    const registered = (window.__registeredWorkletURLs || new Set()).size;
    if (registered === 0) {
      showRenderLoader('warming up the audio engine…', 2);
      try { await play(); } catch (_) {}
      // Wait until at least one worklet is registered (or 1.5s ceiling)
      const t0 = performance.now();
      while ((window.__registeredWorkletURLs || new Set()).size === 0
             && performance.now() - t0 < 1500) {
        await new Promise(r => setTimeout(r, 50));
      }
      try { stop(); } catch (_) {}
      // Give the scheduler a tick to settle
      await new Promise(r => setTimeout(r, 100));
      dremote('render', {
        phase: 'warmup-complete',
        workletsRegistered: (window.__registeredWorkletURLs || new Set()).size,
        elapsedMs: Math.round(performance.now() - t0),
      });
    }
    await renderAlbumOffline();
  } catch (e) {
    console.error(e);
    hideRenderLoader();
    alert('Render failed: ' + e.message);
  }
});
const sectionLenBtn = document.getElementById('tl-section-len');
if (sectionLenBtn) {
  sectionLenBtn.textContent = `${AUTO_ADVANCE_CYCLES}c`;
  sectionLenBtn.addEventListener('click', (e) => cycleSectionLen(e.shiftKey ? -1 : 1));
  sectionLenBtn.addEventListener('contextmenu', (e) => { e.preventDefault(); cycleSectionLen(-1); });
}

// ── draggable pane splitter ───────────────────────────────────
(() => {
  const splitter = document.getElementById('splitter');
  const main = document.querySelector('main');
  const saved = localStorage.getItem('strudel-skills:code-width');
  if (saved) main.style.setProperty('--code-width', saved);

  let dragging = false;
  splitter.addEventListener('mousedown', (e) => {
    dragging = true;
    document.body.classList.add('dragging');
    splitter.classList.add('dragging');
    e.preventDefault();
  });
  document.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const w = Math.max(260, Math.min(window.innerWidth - 260, e.clientX));
    const wStr = `${w}px`;
    main.style.setProperty('--code-width', wStr);
    localStorage.setItem('strudel-skills:code-width', wStr);
    resizeCanvases();
  });
  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    document.body.classList.remove('dragging');
    splitter.classList.remove('dragging');
    resizeCanvases();
  });
})();

// Discover tracks from disk via the dev server, then build the menu.
async function discoverTracks() {
  try {
    const res = await fetch('/tracks', { cache: 'no-cache' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    TRACKS = await res.json();
  } catch (err) {
    dwarn('init', 'track discovery failed:', err.message);
    TRACKS = [];
  }
  return TRACKS;
}

// kick off
applyAutoAdvanceUI();
applyResetUI();
const resetBtn = document.getElementById('tl-reset');
if (resetBtn) resetBtn.addEventListener('click', toggleResetOnSwap);
(async () => {
  await discoverTracks();
  populateTrackMenu();
  if (TRACKS.length === 0) {
    setStatus('no tracks found');
    return;
  }
  await loadTrack(0);
})();
