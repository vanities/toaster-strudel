import { useCallback, useEffect, useRef, useState } from 'react';
import * as engine from './engine/strudel';
import {
  fetchTracks,
  loadTrackCode,
  loadArrangement,
  fetchSections,
  parseCps,
  parseTitle,
  cpsToBpm,
  transformCps,
  type Track,
  type Section,
} from './engine/tracks';
import { startRecording, stopRecording } from './engine/recorder';
import { startRing } from './engine/ring';
import { renderAlbumOffline } from './engine/render';
import { useTheme } from './useTheme';
import { useTrackPoll, useSectionsPoll } from './useTrackPoll';
import CodePanel from './CodePanel';
import Timeline from './Timeline';
import Viz from './Viz';
import Help from './Help';
import Loader from './Loader';
import Hum from './Hum';
import Keyboard from './Keyboard';
import ChatPanel from './chat/ChatPanel';

type Status = 'idle' | 'loading' | 'playing' | 'error';
const SECTION_LEN_OPTIONS = [4, 8, 16, 32, 64, 128];
// Strudel pattern swaps need a little time to evaluate before the next cycle
// boundary. Auto-advancing exactly at the boundary can miss/cut the first onset
// of the new section, so arm the next pattern just before the boundary while
// keeping the UI timer anchored to the intended musical start time.
const SECTION_SWITCH_LEAD_MS = 300;

function fmtMMSS(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}
function downloadBlob(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function App() {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [currentId, setCurrentId] = useState('');
  const [code, setCode] = useState('');
  const [sections, setSections] = useState<Section[]>([]);
  const [viewedIndex, setViewedIndex] = useState(-1);
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string | null>(null);
  const [recording, setRecording] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [humOpen, setHumOpen] = useState(false);
  const [kbdOpen, setKbdOpen] = useState(false);
  const [muted, setMuted] = useState(false);
  const [cpsOverride, setCpsOverride] = useState<number | null>(null);
  const [reloadNonce, setReloadNonce] = useState(0);
  const [splitPct, setSplitPct] = useState(() => {
    const v = parseFloat(localStorage.getItem('toaster-strudel:split') || '');
    return Number.isFinite(v) && v >= 20 && v <= 80 ? v : 50;
  });
  const [patchFlash, setPatchFlash] = useState('');
  const [, setNowTick] = useState(0);
  const [boot, setBoot] = useState({ show: true, msg: 'booting…', pct: 0 });
  const [render, setRender] = useState({ show: false, msg: '', pct: 0 });
  const [sectionLen, setSectionLen] = useState(
    () => parseInt(localStorage.getItem('toaster-strudel:section-len') || '32', 10) || 32
  );
  const [autoAdvance, setAutoAdvance] = useState(
    () => localStorage.getItem('toaster-strudel:auto-advance') !== 'false'
  );
  const [resetOnSwap, setResetOnSwap] = useState(
    () => localStorage.getItem('toaster-strudel:reset-on-swap') !== 'false'
  );
  // Radio mode: at the end of a track's section arc, roll into the NEXT track in
  // the station (tracks sharing its group, e.g. v2-gen) and keep playing — a
  // continuous, self-refreshing stream that picks up freshly-generated cranks.
  const [radio, setRadio] = useState(
    () => localStorage.getItem('toaster-strudel:radio') === 'true'
  );
  // Arc mode: play the whole section arc as ONE continuous pattern — the
  // generated tracks/<id>/arrange.strudel (arrange([cycles, …section…], …)) —
  // instead of stepping section-by-section. The way to actually listen to a
  // track "as it was meant to be ran". arcCode is '' until the file loads (or
  // when a track has no arrangement, which disables the toggle).
  const [arcMode, setArcMode] = useState(
    () => localStorage.getItem('toaster-strudel:arc') === 'true'
  );
  const [arcCode, setArcCode] = useState('');
  const { theme, cycle } = useTheme();

  const playStartedAt = useRef(0);
  const sectionStartedAt = useRef(0);
  const radioPlayPending = useRef(false); // set when a radio hop should auto-play the new track

  const playing = status === 'playing';
  // Mirror playback + sections into refs so the track-load effect and the
  // live-reload polls can read the latest without re-subscribing on every change.
  const playingRef = useRef(false);
  playingRef.current = playing;
  const sectionsRef = useRef<Section[]>([]);
  sectionsRef.current = sections;
  const arcCodeRef = useRef('');
  arcCodeRef.current = arcCode;
  const arcModeRef = useRef(false);
  arcModeRef.current = arcMode;
  // Arc mode only "active" once an arrangement is actually loaded for this track.
  const arcActive = arcMode && !!arcCode;
  const displayedSection = !arcActive && viewedIndex >= 0 ? sections[viewedIndex] : null;
  const displayedCode = arcActive ? arcCode : displayedSection ? displayedSection.code : code;
  const segment = arcActive ? 'arrange.strudel' : displayedSection ? displayedSection.file : 'live';
  const baseCps = parseCps(displayedCode) ?? 0.4;
  const effectiveCps = cpsOverride ?? baseCps;
  const trackNum = currentId.includes('-') ? currentId.split('-')[0] : '';
  const trackTitle = parseTitle(displayedCode) || currentId.split('-').slice(1).join('-') || currentId;
  const sectionSeconds = (snap: Section | undefined) => (snap?.cycles ?? sectionLen) / effectiveCps;

  const flash = useCallback((label: string) => {
    setPatchFlash(label);
    window.setTimeout(() => setPatchFlash((c) => (c === label ? '' : c)), 1200);
  }, []);

  useEffect(() => {
    engine
      .boot((msg, pct) => setBoot({ show: pct < 100, msg, pct }))
      .finally(() => setBoot((b) => ({ ...b, show: false })));
  }, []);

  useEffect(() => {
    fetchTracks()
      .then((list) => {
        setTracks(list);
        if (list.length) setCurrentId(list[0].id);
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!currentId) return;
    let alive = true;
    setCpsOverride(null);
    Promise.all([loadTrackCode(currentId), fetchSections(currentId), loadArrangement(currentId)])
      .then(([src, secs, arc]) => {
        if (!alive) return;
        setCode(src);
        setSections(secs);
        setArcCode(arc ?? '');
        // Jump to the first segment (section 01) on track select, not the live
        // working copy.
        setViewedIndex(secs.length ? 0 : -1);
        // Arc mode wins when the freshly-loaded track actually has an arrangement.
        const arcNow = arcModeRef.current && !!arc;
        flash(
          arcNow
            ? `tracks/${currentId}/arrange.strudel`
            : secs.length
              ? secs[0].file
              : `tracks/${currentId}.strudel`
        );
        // Cut the transport over to the freshly-loaded track when we arrived
        // here while already playing (manual switch) or via a radio hop: play
        // the whole arc (arc mode) or its section 01 (or the live working copy
        // if it has none), which replaces the old pattern at the next cycle
        // boundary. When stopped we stay put — no autoplay on boot, and an
        // intentional stop is respected.
        const playNow = radioPlayPending.current || playingRef.current;
        radioPlayPending.current = false;
        if (playNow) {
          const startCode = arcNow ? arc! : secs.length ? secs[0].code : src;
          engine.play(transformCps(startCode, null)).catch(() => {});
          playStartedAt.current = performance.now();
          sectionStartedAt.current = performance.now();
        }
      })
      .catch((e) => alive && setError(e instanceof Error ? e.message : String(e)));
    return () => {
      alive = false;
    };
  }, [currentId, reloadNonce, flash]);

  useEffect(() => {
    const h = setInterval(() => setNowTick((n) => n + 1), 200);
    return () => clearInterval(h);
  }, []);

  const onFileChange = useCallback(
    (next: string) => {
      setCode(next);
      // In arc mode the single-loop file isn't playing — don't let its edits
      // hot-swap over (and kill) the running arrangement.
      if (arcActive) return;
      flash('patched');
      if (playing && viewedIndex < 0) engine.play(transformCps(next, cpsOverride)).catch(() => {});
    },
    [playing, viewedIndex, cpsOverride, flash, arcActive]
  );
  useTrackPoll(currentId, onFileChange);

  // Section files (tracks/<id>/NN.strudel) live-reload too: refresh the section
  // list on any change and, if we're playing the section that actually changed,
  // hot-swap it in. The live working copy (viewedIndex < 0) is handled above.
  const onSectionsChange = useCallback(
    (next: Section[]) => {
      if (!arcActive && viewedIndex >= 0) {
        const cur = sectionsRef.current[viewedIndex];
        const nx = next[viewedIndex];
        // Viewed section's source changed on disk: flash + refresh the panel,
        // and hot-swap the audio when we're playing it.
        if (nx && (!cur || cur.code !== nx.code)) {
          flash('patched');
          if (playing) engine.play(transformCps(nx.code, cpsOverride)).catch(() => {});
        }
      }
      setSections(next);
    },
    [playing, viewedIndex, cpsOverride, flash, arcActive]
  );
  useSectionsPoll(currentId, onSectionsChange);

  const jumpToSection = useCallback(
    (i: number, opts?: { startedAt?: number }) => {
      if (!sections.length) return;
      // Scrubbing to a specific section means leaving the whole-arc view.
      if (arcMode) {
        setArcMode(false);
        localStorage.setItem('toaster-strudel:arc', 'false');
      }
      const c = Math.max(0, Math.min(sections.length - 1, i));
      setViewedIndex(c);
      sectionStartedAt.current = opts?.startedAt ?? performance.now();
      flash(sections[c].file);
      if (playing) engine.play(transformCps(sections[c].code, cpsOverride)).catch(() => {});
    },
    [sections, playing, cpsOverride, flash, arcMode]
  );

  const stepSection = useCallback(
    (d: number) => {
      if (!sections.length) return;
      const base = viewedIndex < 0 ? 0 : viewedIndex;
      jumpToSection((base + d + sections.length) % sections.length);
    },
    [sections, viewedIndex, jumpToSection]
  );

  // Radio: refetch the catalog (so freshly-generated cranks join the rotation),
  // then hop to the next track in the same group as the current one, wrapping.
  // The track-load effect auto-plays it (radioPlayPending).
  const advanceStation = useCallback(async () => {
    let list = tracks;
    try { list = await fetchTracks(); setTracks(list); } catch { /* keep current list */ }
    const cur = list.find((t) => t.id === currentId);
    const station = cur?.group ? list.filter((t) => t.group === cur.group) : list;
    if (!station.length) return;
    const i = station.findIndex((t) => t.id === currentId);
    const next = station[(i + 1) % station.length];
    radioPlayPending.current = true;
    setCurrentId(next.id);
  }, [tracks, currentId]);

  useEffect(() => {
    // Arc mode plays one continuous pattern — arrange() owns the sequencing, so
    // the section auto-advance timer must stand down.
    if (!autoAdvance || arcActive || !playing || sections.length === 0) return;
    const idx = viewedIndex < 0 ? 0 : viewedIndex;
    const cps = (cpsOverride ?? parseCps(sections[idx]?.code ?? code)) || 0.4;
    const ms = Math.max(1000, ((sections[idx]?.cycles ?? sectionLen) / cps) * 1000);
    const last = idx >= sections.length - 1;
    const h = window.setTimeout(() => {
      const switchAt = sectionStartedAt.current + ms;
      if (radio && last) void advanceStation();         // end of the arc → next track
      else jumpToSection((idx + 1) % sections.length, { startedAt: switchAt });  // arm just before boundary
    }, Math.max(0, ms - SECTION_SWITCH_LEAD_MS));
    return () => clearTimeout(h);
  }, [autoAdvance, arcActive, playing, viewedIndex, sections, sectionLen, code, cpsOverride, jumpToSection, radio, advanceStation]);

  const play = useCallback(async () => {
    setError(null);
    setStatus('loading');
    setMuted(false);
    try {
      let src: string;
      if (arcActive) {
        src = arcCode; // the whole arrangement as one pattern
      } else {
        const startSection = autoAdvance && sections.length ? 0 : viewedIndex;
        if (startSection >= 0 && sections[startSection]) setViewedIndex(startSection);
        src = startSection >= 0 && sections[startSection] ? sections[startSection].code : code;
      }
      await engine.play(transformCps(src, cpsOverride));
      void startRing();
      playStartedAt.current = performance.now();
      sectionStartedAt.current = performance.now();
      setStatus('playing');
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStatus('error');
    }
  }, [arcActive, arcCode, autoAdvance, sections, viewedIndex, code, cpsOverride]);

  const stop = useCallback(async () => {
    await engine.stop();
    setStatus('idle');
  }, []);

  const toggleMute = useCallback(() => {
    if (!playing) return;
    const next = !muted;
    setMuted(next);
    void engine.setMuted(next, transformCps(displayedCode, cpsOverride));
  }, [playing, muted, displayedCode, cpsOverride]);

  const nudge = useCallback(
    (factor: number) => {
      const base = cpsOverride ?? baseCps;
      const next = Math.max(0.1, Math.min(4, base * factor));
      setCpsOverride(next);
      if (playing && !muted) engine.play(transformCps(displayedCode, next)).catch(() => {});
    },
    [cpsOverride, baseCps, playing, muted, displayedCode]
  );

  const stepTrack = useCallback(
    (delta: number) => {
      if (!tracks.length) return;
      const i = tracks.findIndex((t) => t.id === currentId);
      setCurrentId(tracks[(i + delta + tracks.length) % tracks.length].id);
    },
    [tracks, currentId]
  );

  const jumpTrack = useCallback((n: number) => tracks[n] && setCurrentId(tracks[n].id), [tracks]);

  const toggleAuto = useCallback(() => {
    setAutoAdvance((a) => {
      const v = !a;
      localStorage.setItem('toaster-strudel:auto-advance', String(v));
      return v;
    });
  }, []);

  const toggleRadio = useCallback(() => {
    setRadio((on) => {
      const v = !on;
      localStorage.setItem('toaster-strudel:radio', String(v));
      if (v) {
        setAutoAdvance(true); // radio rides the section auto-advance to move
        localStorage.setItem('toaster-strudel:auto-advance', 'true');
      }
      return v;
    });
  }, []);

  const toggleArc = useCallback(() => {
    setArcMode((on) => {
      const v = !on;
      localStorage.setItem('toaster-strudel:arc', String(v));
      const arc = arcCodeRef.current;
      if (v && !arc) return v; // track has no arrangement yet — nothing to switch to
      // Cut the running transport into / out of the whole-arc pattern.
      if (playingRef.current) {
        if (v) {
          engine.play(transformCps(arc, cpsOverride)).catch(() => {});
        } else {
          const idx = viewedIndex < 0 ? 0 : viewedIndex;
          setViewedIndex(idx);
          engine.play(transformCps(sections[idx]?.code ?? code, cpsOverride)).catch(() => {});
        }
        playStartedAt.current = performance.now();
        sectionStartedAt.current = performance.now();
      }
      return v;
    });
  }, [cpsOverride, viewedIndex, sections, code]);

  const toggleReset = useCallback(() => {
    setResetOnSwap((r) => {
      const v = !r;
      localStorage.setItem('toaster-strudel:reset-on-swap', String(v));
      return v;
    });
  }, []);

  const cycleLen = useCallback((d: number) => {
    setSectionLen((cur) => {
      const i = SECTION_LEN_OPTIONS.indexOf(cur);
      const v = SECTION_LEN_OPTIONS[(i + d + SECTION_LEN_OPTIONS.length) % SECTION_LEN_OPTIONS.length];
      localStorage.setItem('toaster-strudel:section-len', String(v));
      return v;
    });
  }, []);

  const toggleRecord = useCallback(() => {
    if (recording) {
      const blob = stopRecording();
      setRecording(false);
      if (blob) downloadBlob(blob, `toaster-strudel_${currentId || 'song'}_${Date.now()}.wav`);
    } else if (startRecording()) {
      setRecording(true);
    }
  }, [recording, currentId]);

  const doRender = useCallback(async () => {
    if (!sections.length || render.show) return;
    setRender({ show: true, msg: 'preparing…', pct: 0 });
    try {
      const blob = await renderAlbumOffline(sections, currentId, sectionLen, (msg, pct) =>
        setRender({ show: true, msg, pct })
      );
      if (blob) downloadBlob(blob, `${currentId || 'album'}.wav`);
      if (playing) setStatus('idle'); // render hushes the live transport
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRender({ show: false, msg: '', pct: 0 });
    }
  }, [sections, currentId, sectionLen, render.show, playing]);

  const refreshSections = useCallback(() => {
    if (currentId) fetchSections(currentId).then(setSections).catch(() => {});
  }, [currentId]);

  const replay = useCallback(() => {
    // In arc mode, restart the whole arrangement from the top (don't fall
    // through to jumpToSection, which would exit arc).
    if (arcActive) {
      if (playing) {
        engine.play(transformCps(arcCode, cpsOverride)).catch(() => {});
        playStartedAt.current = performance.now();
        sectionStartedAt.current = performance.now();
      } else void play();
      return;
    }
    if (!sections.length) return;
    if (playing) jumpToSection(0);
    else {
      setViewedIndex(0);
      void play();
    }
  }, [arcActive, arcCode, cpsOverride, sections, playing, jumpToSection, play]);

  const openInStrudel = useCallback(() => {
    try {
      window.open(`https://strudel.cc/#${btoa(unescape(encodeURIComponent(displayedCode)))}`, '_blank', 'noopener');
    } catch {
      window.open('https://strudel.cc', '_blank', 'noopener');
    }
  }, [displayedCode]);

  const startDrag = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    const main = (e.currentTarget as HTMLElement).parentElement;
    if (!main) return;
    document.body.classList.add('dragging');
    let last = splitPct;
    const onMove = (ev: MouseEvent) => {
      const rect = main.getBoundingClientRect();
      last = Math.max(20, Math.min(80, ((ev.clientX - rect.left) / rect.width) * 100));
      setSplitPct(last);
    };
    const onUp = () => {
      document.body.classList.remove('dragging');
      localStorage.setItem('toaster-strudel:split', String(last));
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [splitPct]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.tagName === 'SELECT')) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      switch (e.key) {
        case ' ': e.preventDefault(); playing ? stop() : play(); break;
        case 'ArrowLeft': e.preventDefault(); stepTrack(-1); break;
        case 'ArrowRight': e.preventDefault(); stepTrack(1); break;
        case '1': case '2': case '3': case '4': jumpTrack(parseInt(e.key, 10) - 1); break;
        case ',': stepSection(-1); break;
        case '.': stepSection(1); break;
        case 'r': case 'R': setReloadNonce((n) => n + 1); break;
        case 'a': case 'A': toggleAuto(); break;
        case 'f': case 'F': toggleArc(); break;
        case 'g': case 'G': toggleRadio(); break;
        case 'm': case 'M': toggleMute(); break;
        case 't': case 'T': cycle(); break;
        case 'c': case 'C': window.dispatchEvent(new CustomEvent('strudel:toggle-chat')); break;
        case 'z': case 'Z': toggleReset(); break;
        case 'h': case 'H': setHumOpen((v) => !v); break;
        case 'k': case 'K': refreshSections(); break;
        case '\\': replay(); break;
        case '[': nudge(0.9); break;
        case ']': nudge(1.1); break;
        case '?': setHelpOpen((v) => !v); break;
        case 'Escape': setHelpOpen(false); setHumOpen(false); break;
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [playing, play, stop, stepTrack, jumpTrack, stepSection, toggleAuto, toggleArc, toggleRadio, toggleMute, toggleReset, cycle, nudge, refreshSections, replay]);

  const totalSecs =
    (autoAdvance || arcActive) && sections.length
      ? sections.reduce((s, snap) => s + sectionSeconds(snap), 0)
      : sectionSeconds(sections[viewedIndex < 0 ? 0 : viewedIndex]);
  const elapsed = playing ? performance.now() - playStartedAt.current : 0;
  // Arc plays one continuous pattern, so there's no per-section "next" boundary.
  const nextRemain = !arcActive && autoAdvance && playing ? Math.max(0, sectionStartedAt.current + sectionSeconds(sections[viewedIndex < 0 ? 0 : viewedIndex]) * 1000 - performance.now()) : null;
  const curSecMs = sectionSeconds(sections[viewedIndex < 0 ? 0 : viewedIndex]) * 1000;
  // In arc mode the progress bar tracks the WHOLE arrangement; otherwise the
  // position within the current section.
  const progress = arcActive
    ? playing && totalSecs > 0
      ? Math.min(1, elapsed / (totalSecs * 1000))
      : 0
    : playing && curSecMs > 0
      ? Math.min(1, (performance.now() - sectionStartedAt.current) / curSecMs)
      : 0;

  return (
    <div className="flex h-full flex-col" style={{ overflow: 'hidden' }}>
      <header className="player-head">
        <div className="flex items-center gap-2">
          <span className="brand" style={{ fontFamily: 'var(--sans)' }}>toaster-strudel</span>
          <span className="badge">react</span>
        </div>

        <div className="flex items-center justify-center gap-1.5">
          <select className="cbtn" value={currentId} onChange={(e) => setCurrentId(e.target.value)}>
            {tracks.map((t) => (
              <option key={t.id} value={t.id}>{t.label}</option>
            ))}
          </select>
          <button className="cbtn" onClick={() => stepTrack(-1)} title="Previous track (←)">⏮</button>
          <button className="cbtn primary" onClick={play} disabled={playing} title="Play (space)">▶</button>
          <button className="cbtn" onClick={stop} disabled={!playing} title="Stop (space)">■</button>
          <button className="cbtn" onClick={() => stepTrack(1)} title="Next track (→)">⏭</button>
          <button
            className={`cbtn${arcActive ? ' primary' : ''}`}
            onClick={toggleArc}
            disabled={!arcCode}
            title="Full arrangement — play the whole section arc as one continuous track, as it was meant to be heard (f)"
          >🎼</button>
          <button className={`cbtn${radio ? ' primary' : ''}`} onClick={toggleRadio} title="Radio — play the station continuously, hopping tracks at the end of each arc (g)">📻</button>
          <button className="cbtn" onClick={() => setReloadNonce((n) => n + 1)} title="Reload (r)">↻</button>
          <button className="cbtn" onClick={openInStrudel} title="Open in strudel.cc">↗</button>
          <button className={`cbtn${recording ? ' rec' : ''}`} onClick={toggleRecord} title="Record to WAV">●</button>
          <button className="cbtn" onClick={doRender} title="Download whole track (offline render)">⤓</button>
          <button className={`cbtn${muted ? ' rec' : ''}`} onClick={toggleMute} title="Mute (m)">{muted ? '🔇' : '🔊'}</button>
          <button className="cbtn" onClick={() => setHumOpen(true)} title="Hum → melody (h)">🎤</button>
          <button className="cbtn" onClick={() => setKbdOpen(true)} title="Instrument keyboard">🎹</button>
        </div>

        <div className="flex items-center justify-end gap-1.5">
          <span className="readout" title="BPM">{cpsToBpm(effectiveCps)} bpm</span>
          <span className="readout" title="elapsed / total">{fmtMMSS(elapsed)} / {fmtMMSS(totalSecs * 1000)}</span>
          <span className="readout" title="next section">→ {nextRemain != null ? fmtMMSS(nextRemain) : '—'}</span>
          <span
            className="readout"
            style={{ minWidth: '4.4em', textAlign: 'center', ...(status === 'error' ? { color: 'var(--warm)' } : {}) }}
          >
            {status === 'error' ? error : status === 'loading' ? 'loading' : status === 'playing' ? (muted ? 'muted' : 'playing') : boot.show ? 'booting' : 'ready'}
          </span>
          <button className="cbtn" onClick={cycle} title="Cycle theme (t)" style={{ textTransform: 'lowercase' }}>{theme}</button>
          <button className="cbtn" onClick={() => setHelpOpen(true)} title="Keybindings (?)">?</button>
        </div>
      </header>

      <main className="player-main">
        <div className="code-col" style={{ flex: `0 0 ${splitPct}%` }}>
          <div className="code-header">
            <div className="code-label">
              <span className={`live-dot${playing ? ' live' : ''}`} />
              <span className="track-num">{trackNum}</span>
              <span className="track-title">{trackTitle}</span>
            </div>
            <div className="code-meta">
              {patchFlash && <span className="patch-flash show">● {patchFlash}</span>}
              <span className="code-path">tracks/{currentId}{segment === 'live' ? '.strudel' : `/${segment}`}</span>
            </div>
          </div>
          <Timeline
            sections={sections}
            viewedIndex={viewedIndex}
            autoAdvance={autoAdvance}
            arcActive={arcActive}
            sectionLen={sectionLen}
            progress={progress}
            resetOnSwap={resetOnSwap}
            onJump={jumpToSection}
            onStep={stepSection}
            onToggleAuto={toggleAuto}
            onCycleLen={cycleLen}
            onReplay={replay}
            onRefresh={refreshSections}
            onToggleReset={toggleReset}
          />
          <CodePanel code={displayedCode} trackId={currentId || null} segment={segment} playing={playing} />
        </div>
        <div className="splitter" onMouseDown={startDrag} title="Drag to resize" />
        <Viz playing={playing} />
      </main>

      <Help open={helpOpen} onClose={() => setHelpOpen(false)} />
      <Hum open={humOpen} onClose={() => setHumOpen(false)} />
      <Keyboard open={kbdOpen} onClose={() => setKbdOpen(false)} />
      <Loader show={boot.show} message={boot.msg} pct={boot.pct} />
      <Loader show={render.show} message={render.msg} pct={render.pct} title="rendering" />
      <ChatPanel viewingTrack={currentId || null} />
    </div>
  );
}
