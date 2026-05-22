import { useEffect, useRef } from 'react';
import { startViz } from './engine/viz';

// Thin React shell: owns the canvas elements, hands them to the imperative viz
// engine on mount, tears it down on unmount. isPlaying is read through a ref so
// the RAF loop always sees the latest value without re-mounting.
export default function Viz({ playing }: { playing: boolean }) {
  const bc = useRef<HTMLCanvasElement>(null);
  const mandala = useRef<HTMLCanvasElement>(null);
  const spec = useRef<HTMLCanvasElement>(null);
  const wave = useRef<HTMLCanvasElement>(null);
  const voices = useRef<HTMLCanvasElement>(null);
  const beat = useRef<HTMLDivElement>(null);
  const count = useRef<HTMLSpanElement>(null);
  const preset = useRef<HTMLSpanElement>(null);
  const playingRef = useRef(playing);
  playingRef.current = playing;

  useEffect(() => {
    if (!bc.current || !mandala.current || !spec.current || !wave.current || !voices.current) {
      return;
    }
    return startViz({
      butterchurn: bc.current,
      mandala: mandala.current,
      spec: spec.current,
      wave: wave.current,
      voices: voices.current,
      beatRing: beat.current,
      voicesCount: count.current,
      presetLabel: preset.current,
      isPlaying: () => playingRef.current,
    });
  }, []);

  return (
    <section className="viz">
      <canvas ref={bc} className="viz-canvas" />
      <canvas ref={mandala} className="viz-canvas" />
      <canvas ref={spec} className="viz-canvas" />
      <canvas ref={wave} className="viz-canvas" />
      <canvas ref={voices} className="viz-canvas" />
      <div className="center-rune">⊙</div>
      <div ref={beat} className="beat-ring" />
      <div className="viz-hud">
        <span ref={preset} className="viz-hud-line" />
        <span ref={count} className="viz-hud-line" />
      </div>
    </section>
  );
}
