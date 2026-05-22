import { useEffect, useState } from 'react';
import { playNote, listSounds } from './engine/strudel';
import { isSynth, noteOn, noteOff, allNotesOff } from './engine/synth';

// Instrument test keyboard: click / computer-key / MIDI-in. Synth waveforms
// sustain while held (raw oscillators); sample instruments one-shot. Searchable
// picker over every loaded Strudel sound.

const NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const FALLBACK = ['sawtooth', 'square', 'triangle', 'sine', 'piano', 'kalimba', 'marimba', 'vibraphone'];
const KEYMAP: Record<string, number> = {
  a: 0, w: 1, s: 2, e: 3, d: 4, f: 5, t: 6, g: 7, y: 8, h: 9, u: 10, j: 11,
  k: 12, o: 13, l: 14, p: 15, ';': 16,
};

const isBlack = (s: number) => [1, 3, 6, 8, 10].includes(((s % 12) + 12) % 12);
interface WhiteKey { semi: number }
interface BlackKey { semi: number; leftIdx: number }
const whiteKeys: WhiteKey[] = [];
const blackKeys: BlackKey[] = [];
{
  let whiteCount = 0;
  for (let s = 0; s <= 24; s++) {
    if (isBlack(s)) blackKeys.push({ semi: s, leftIdx: whiteCount - 1 });
    else {
      whiteKeys.push({ semi: s });
      whiteCount++;
    }
  }
}
const whiteW = 100 / whiteKeys.length;

const noteName = (semi: number, baseOctave: number) =>
  NOTES[((semi % 12) + 12) % 12] + (baseOctave + Math.floor(semi / 12));
const midiToName = (n: number) => NOTES[((n % 12) + 12) % 12] + (Math.floor(n / 12) - 1);
const freqOf = (midi: number) => 440 * Math.pow(2, (midi - 69) / 12);

export default function Keyboard({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [instrument, setInstrument] = useState('sawtooth');
  const [baseOctave, setBaseOctave] = useState(3);
  const [gain, setGain] = useState(0.7);
  const [active, setActive] = useState<Set<number>>(new Set());
  const [midiOn, setMidiOn] = useState(false);
  const [sounds, setSounds] = useState<string[]>(FALLBACK);
  const [status, setStatus] = useState('click keys, use your keyboard (a w s e d…), or connect MIDI');

  useEffect(() => {
    if (!open) return;
    listSounds()
      .then((list) => list.length && setSounds(list))
      .catch(() => {});
    return () => {
      allNotesOff();
      setActive(new Set());
    };
  }, [open]);

  function hit(semi: number) {
    const midi = (baseOctave + 1) * 12 + semi;
    if (isSynth(instrument)) noteOn(`k${semi}`, freqOf(midi), instrument as OscillatorType, gain);
    else void playNote({ note: noteName(semi, baseOctave), s: instrument, gain }, 0.9);
    setActive((prev) => new Set(prev).add(semi));
  }
  function release(semi: number) {
    if (isSynth(instrument)) noteOff(`k${semi}`);
    setActive((prev) => {
      const n = new Set(prev);
      n.delete(semi);
      return n;
    });
  }

  // computer keyboard (capture phase so player shortcuts don't fire)
  useEffect(() => {
    if (!open) return;
    const down = (e: KeyboardEvent) => {
      const k = e.key.toLowerCase();
      if (k === 'escape') {
        onClose();
        return;
      }
      const ae = document.activeElement;
      if (ae instanceof HTMLElement && ae.tagName === 'INPUT') return; // typing in search
      if (e.repeat || !(k in KEYMAP)) return;
      e.preventDefault();
      e.stopPropagation();
      hit(KEYMAP[k]);
    };
    const up = (e: KeyboardEvent) => {
      const k = e.key.toLowerCase();
      if (k in KEYMAP) {
        e.stopPropagation();
        release(KEYMAP[k]);
      }
    };
    window.addEventListener('keydown', down, true);
    window.addEventListener('keyup', up, true);
    return () => {
      window.removeEventListener('keydown', down, true);
      window.removeEventListener('keyup', up, true);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, instrument, baseOctave, gain, onClose]);

  async function connectMidi() {
    const nav = navigator as unknown as {
      requestMIDIAccess?: () => Promise<{ inputs: { forEach: (cb: (i: unknown) => void) => void; size?: number } }>;
    };
    if (!nav.requestMIDIAccess) {
      setStatus('Web MIDI not supported in this browser');
      return;
    }
    try {
      const access = await nav.requestMIDIAccess();
      access.inputs.forEach((input) => {
        (input as { onmidimessage: (msg: { data?: Uint8Array | null }) => void }).onmidimessage = (msg) => {
          const data = msg.data;
          if (!data) return;
          const st = data[0] & 0xf0;
          const note = data[1];
          const vel = data[2];
          const key = `m${note}`;
          if (st === 0x90 && vel > 0) {
            if (isSynth(instrument)) noteOn(key, freqOf(note), instrument as OscillatorType, (vel / 127) * gain);
            else void playNote({ note: midiToName(note), s: instrument, gain: (vel / 127) * gain }, 0.9);
          } else if (st === 0x80 || (st === 0x90 && vel === 0)) {
            if (isSynth(instrument)) noteOff(key);
          }
        };
      });
      setMidiOn(true);
      setStatus(`MIDI connected · ${access.inputs.size ?? '?'} input(s)`);
    } catch (e) {
      setStatus(`MIDI failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  }

  if (!open) return null;
  return (
    <div className="kbd-overlay">
      <div className="kbd-card">
        <header className="kbd-head">
          <span>instrument keyboard</span>
          <button className="cbtn" onClick={onClose}>×</button>
        </header>

        <div className="kbd-row">
          <label className="kbd-lab">sound
            <input
              className="kbd-search"
              list="kbd-sounds"
              value={instrument}
              placeholder="search sounds…"
              onChange={(e) => {
                const v = e.target.value;
                setInstrument(v);
                allNotesOff();
                if (sounds.includes(v)) e.currentTarget.blur();
              }}
            />
            <datalist id="kbd-sounds">
              {sounds.map((s) => (
                <option key={s} value={s} />
              ))}
            </datalist>
          </label>
          <span className="kbd-count">{sounds.length} sounds</span>
          <label className="kbd-lab">octave
            <button className="cbtn" onClick={() => setBaseOctave((o) => Math.max(0, o - 1))}>−</button>
            <span className="kbd-oct">{baseOctave}</span>
            <button className="cbtn" onClick={() => setBaseOctave((o) => Math.min(7, o + 1))}>+</button>
          </label>
          <label className="kbd-lab">gain
            <input type="range" min={0} max={1} step={0.05} value={gain} onChange={(e) => setGain(+e.target.value)} />
          </label>
          <button className={`cbtn${midiOn ? ' primary' : ''}`} onClick={connectMidi}>{midiOn ? 'MIDI ✓' : 'connect MIDI'}</button>
        </div>

        <div className="kbd-status">
          {status}
          {!isSynth(instrument) && ' · (sample — plays as a one-shot, no sustain)'}
        </div>

        <div className="kbd-piano">
          {whiteKeys.map((w) => (
            <div
              key={w.semi}
              className={`kbd-white${active.has(w.semi) ? ' on' : ''}`}
              style={{ width: `${whiteW}%` }}
              onMouseDown={() => hit(w.semi)}
              onMouseUp={() => release(w.semi)}
              onMouseLeave={() => release(w.semi)}
            >
              <span className="kbd-keyname">{noteName(w.semi, baseOctave)}</span>
            </div>
          ))}
          {blackKeys.map((b) => (
            <div
              key={b.semi}
              className={`kbd-black${active.has(b.semi) ? ' on' : ''}`}
              style={{ left: `${(b.leftIdx + 1) * whiteW - whiteW * 0.31}%`, width: `${whiteW * 0.62}%` }}
              onMouseDown={() => hit(b.semi)}
              onMouseUp={() => release(b.semi)}
              onMouseLeave={() => release(b.semi)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
