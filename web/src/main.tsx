// audio-patch MUST be the first import: it subclasses window.AudioContext to
// tap the analyser, and that has to be in place before the Strudel engine
// ever calls initStrudel() (which creates the context). ES module imports run
// top-to-bottom, so listing it first guarantees the order.
import './audio-patch';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import { boot } from './engine/strudel';
import { fetchSections } from './engine/tracks';
import { renderAlbumOffline } from './engine/render';

// Headless render hook — lets an external driver (puppeteer, no interactive
// browser) render any track to WAV offline. renderAlbumOffline POSTs the result
// to /save-wav, so it lands at /tmp/strudel-renders/<id>.wav for the agent to
// measure (the "ears" loop). Not used by the UI; harmless for normal users.
declare global {
  interface Window {
    __renderTrack?: (id: string, sectionLen?: number) => Promise<{ ok: boolean; sections: number }>;
  }
}
window.__renderTrack = async (id: string, sectionLen = 32) => {
  await boot();
  const sections = await fetchSections(id);
  const blob = await renderAlbumOffline(sections, id, sectionLen);
  return { ok: !!blob, sections: sections.length };
};

// No StrictMode: it double-invokes effects in dev, which would double-init the
// imperative audio engine. We can revisit once the engine guards are solid.
createRoot(document.getElementById('root')!).render(<App />);
