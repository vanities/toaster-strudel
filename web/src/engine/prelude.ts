// Custom Strudel pattern methods + REPL-viz shims for toaster-strudel.
// Evaluated ONCE at boot (see strudel.ts). register(name, fn) adds a chainable
// method to the Pattern class (fn's last arg is the pattern).
//
// VIZ SHIMS: strudel.cc songs often chain .scope()/._scope()/.pianoroll()/etc. —
// REPL oscilloscope/visualizers that draw to the REPL canvas. Our embed has no such
// canvas, so we stub them to no-op passthrough (return the pattern unchanged). This
// is what lets a song copy-pasted straight from strudel.cc RUN here unmodified.
//
// OUR PRESETS (chainable, no-arg — the proven `(pat) => …` shape; tune by editing):
//   .bowed()   — detune (vibrato) + legato → "played bowed string" life
//   .pad()     — attack + release          → slow sustained swell
//   .pluck()   — attack + release          → short percussive hit
//   .space()   — room + delay              → cavernous reverb/delay
//   .wide()    — pan                       → gentle auto-pan stereo width
//   .breathe() — lpf                       → slow filter sweep (movement)

export const PRELUDE = [
  // --- REPL-only visualizers → no-op passthrough (ignore args, return the pattern) ---
  "Pattern.prototype._scope = Pattern.prototype.scope = function () { return this; };",
  "Pattern.prototype.pianoroll = Pattern.prototype._pianoroll = function () { return this; };",
  "Pattern.prototype.punchcard = Pattern.prototype._punchcard = function () { return this; };",
  "Pattern.prototype.spiral = Pattern.prototype._spiral = function () { return this; };",
  // --- our custom presets ---
  "register('bowed',   (pat) => pat.detune(sine.range(-0.18, 0.18).fast(9)).legato(1.4));",
  "register('pad',     (pat) => pat.attack(1).release(3));",
  "register('pluck',   (pat) => pat.attack(0.002).release(0.25));",
  "register('space',   (pat) => pat.room(0.85).delay(0.3).delaytime(0.5).delayfeedback(0.4));",
  "register('wide',    (pat) => pat.pan(sine.slow(7).range(0.3, 0.7)));",
  "register('breathe', (pat) => pat.lpf(sine.range(400, 1200).slow(16)));",
  "silence",
].join("\n");
