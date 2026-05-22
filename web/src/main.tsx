// audio-patch MUST be the first import: it subclasses window.AudioContext to
// tap the analyser, and that has to be in place before the Strudel engine
// ever calls initStrudel() (which creates the context). ES module imports run
// top-to-bottom, so listing it first guarantees the order.
import './audio-patch';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

// No StrictMode: it double-invokes effects in dev, which would double-init the
// imperative audio engine. We can revisit once the engine guards are solid.
createRoot(document.getElementById('root')!).render(<App />);
