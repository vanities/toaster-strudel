import type { Section } from './engine/tracks';

interface Props {
  sections: Section[];
  viewedIndex: number;
  autoAdvance: boolean;
  arcActive?: boolean;
  sectionLen: number;
  progress: number; // 0..1 position within the current section
  resetOnSwap: boolean;
  onJump: (i: number) => void;
  onStep: (d: number) => void;
  onToggleAuto: () => void;
  onCycleLen: (d: number) => void;
  onReplay: () => void;
  onRefresh: () => void;
  onToggleReset: () => void;
}

export default function Timeline({
  sections,
  viewedIndex,
  autoAdvance,
  arcActive = false,
  sectionLen,
  progress,
  resetOnSwap,
  onJump,
  onStep,
  onToggleAuto,
  onCycleLen,
  onReplay,
  onRefresh,
  onToggleReset,
}: Props) {
  const active = viewedIndex < 0 ? -1 : viewedIndex;
  const curCycles = sections[active < 0 ? 0 : active]?.cycles ?? sectionLen;
  const info =
    sections.length === 0
      ? 'no sections'
      : arcActive
        ? `full arrangement · ${sections.length} sections`
        : autoAdvance
          ? `auto · ${active < 0 ? '–' : active + 1}/${sections.length}`
          : viewedIndex < 0
            ? `live · ${sections.length} sections`
            : sections[active]?.file ?? `${active + 1}/${sections.length}`;

  return (
    <div className="timeline">
      <div className="tl-nav">
        <button className="cbtn" onClick={() => onStep(-1)} title="Previous section (,)">◂</button>
        <button className="cbtn" onClick={() => onStep(1)} title="Next section (.)">▸</button>
      </div>
      <div className="tl-strip">
        {sections.map((s, i) => (
          <div
            key={s.file}
            className={`tl-dot${arcActive || i === active ? ' active' : ''}${!arcActive && autoAdvance && i === active ? ' advancing' : ''}`}
            title={`${s.file} · ${s.label} · ${s.cycles ?? sectionLen}c`}
            onClick={() => onJump(i)}
          />
        ))}
      </div>
      <button className={`cbtn${autoAdvance ? ' primary' : ''}`} onClick={onToggleAuto} title="Auto-advance (a)">⟳</button>
      <button className="cbtn" onClick={(e) => onCycleLen(e.shiftKey ? -1 : 1)} title="Section length — click to cycle">{curCycles}c</button>
      <button className={`cbtn${resetOnSwap ? ' primary' : ''}`} onClick={onToggleReset} title="Reset timer on section swap (z)">↺</button>
      <button className="cbtn" onClick={onReplay} title="Replay all sections (\\)">⏵⏵</button>
      <span className={`tl-info${arcActive ? ' live' : autoAdvance ? '' : viewedIndex < 0 ? ' live' : ' frozen'}`}>{info}</span>
      <button className="cbtn" onClick={onRefresh} title="Refresh sections from disk (k)">↻</button>
      <div className="tl-progress" style={{ width: `${Math.min(100, Math.max(0, progress * 100))}%` }} />
    </div>
  );
}
