// Audio tap — ported from the vanilla player's patchAudio IIFE.
//
// Must run before any AudioContext is created (i.e. before the Strudel engine
// calls initStrudel). Three patches:
//   1. Subclass AudioContext to grab the first context Strudel makes + hang an
//      AnalyserNode off it.
//   2. Patch AudioNode.connect so anything wired to a destination ALSO fans
//      into the analyser — this is what feeds the visualisers (without it the
//      analyser sees silence and every viz layer draws nothing).
//   3. Track AudioWorklet.addModule URLs so the offline renderer can replay
//      them into a fresh OfflineAudioContext (superdough's worklets need them).

let analyser: AnalyserNode | null = null;
let strudelCtx: AudioContext | null = null;
let masterGain: GainNode | null = null;
let masterGainValue = 1;
export const registeredWorkletURLs = new Set<string>();

(function patchAudio() {
  const w = window as unknown as { webkitAudioContext?: typeof AudioContext };
  const OrigCtx = window.AudioContext || w.webkitAudioContext;
  if (!OrigCtx) return;

  class TappedAudioContext extends OrigCtx {
    constructor(options?: AudioContextOptions) {
      super(options);
      if (!strudelCtx) {
        strudelCtx = this;
        analyser = this.createAnalyser();
        analyser.fftSize = 4096;
        analyser.smoothingTimeConstant = 0.82;
      }
    }
  }
  window.AudioContext = TappedAudioContext as unknown as typeof AudioContext;
  if (w.webkitAudioContext) w.webkitAudioContext = TappedAudioContext as unknown as typeof AudioContext;

  // 2. Master tap + master gain. Any node → destination also fans into the
  //    analyser, and live-context connects to the destination detour through a
  //    master GainNode — the per-track loudness-normalization stage (set from
  //    the track manifest's "playbackGain", written by tools/loudness.py).
  //    The analyser tap stays PRE-gain: viz amplitude and recordings reflect
  //    the un-normalized signal, so renders stay raw for (re-)measurement.
  //    Offline render contexts bypass all of this (masterGain lives in the
  //    live context only).
  const origConnect = AudioNode.prototype.connect;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  AudioNode.prototype.connect = function (this: AudioNode, target: any, ...rest: any[]): any {
    if (
      strudelCtx &&
      target instanceof AudioDestinationNode &&
      target === strudelCtx.destination &&
      this.context === strudelCtx &&
      this !== analyser &&
      this !== masterGain
    ) {
      if (!masterGain) {
        masterGain = strudelCtx.createGain();
        masterGain.gain.value = masterGainValue;
        (origConnect as (this: AudioNode, n: AudioNode) => unknown).call(masterGain, strudelCtx.destination);
      }
      const result = (origConnect as (this: AudioNode, n: AudioNode) => AudioNode).call(this, masterGain);
      if (analyser) {
        try {
          (origConnect as (this: AudioNode, n: AudioNode) => unknown).call(this, analyser);
        } catch {
          /* already tapped */
        }
      }
      return result;
    }
    const result = origConnect.call(this, target, ...rest);
    if (analyser && this !== analyser && target instanceof AudioDestinationNode) {
      try {
        (origConnect as (this: AudioNode, n: AudioNode) => unknown).call(this, analyser);
      } catch {
        /* already tapped */
      }
    }
    return result;
  };

  // 3. Remember worklet module URLs for offline rendering.
  if (window.AudioWorklet) {
    const origAdd = AudioWorklet.prototype.addModule;
    AudioWorklet.prototype.addModule = function (
      this: AudioWorklet,
      url: string | URL,
      options?: WorkletOptions
    ): Promise<void> {
      try {
        registeredWorkletURLs.add(String(url));
      } catch {
        /* ignore */
      }
      return origAdd.call(this, url, options);
    };
  }
})();

export function getAnalyser(): AnalyserNode | null {
  return analyser;
}
export function getStrudelCtx(): AudioContext | null {
  return strudelCtx;
}

// Per-track playback gain (loudness normalization). Short ramp to avoid
// clicks on track hops; the value sticks and is applied when masterGain is
// first created, so it's safe to call before audio boots.
export function setMasterGain(value: number, rampSec = 0.08): void {
  const v = Number.isFinite(value) && value > 0 ? Math.min(4, Math.max(0.05, value)) : 1;
  masterGainValue = v;
  if (!masterGain || !strudelCtx) return;
  const t = strudelCtx.currentTime;
  masterGain.gain.cancelScheduledValues(t);
  masterGain.gain.setTargetAtTime(v, t, rampSec);
}
export function getMasterGain(): number {
  return masterGainValue;
}
