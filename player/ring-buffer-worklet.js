// Always-on ring buffer for the last N seconds of audio output.
// Runs on the audio thread (AudioWorklet) so it doesn't starve Strudel's
// scheduler the way an always-connected ScriptProcessor on the main thread
// would.
//
// Messages:
//   { cmd: 'getBuffer' }          → reply { left, right, sampleRate, writePos }
//   { cmd: 'setSeconds', seconds: N }  → resize ring buffer to N seconds

class RingBufferProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const seconds = (options?.processorOptions?.seconds) ?? 30;
    this.allocate(seconds);
    this.port.onmessage = (e) => {
      if (e.data?.cmd === 'getBuffer') {
        this.port.postMessage({
          left: this.ringL.slice(),
          right: this.ringR.slice(),
          sampleRate,
          writePos: this.writePos,
        });
      } else if (e.data?.cmd === 'setSeconds') {
        this.allocate(e.data.seconds);
      }
    };
  }

  allocate(seconds) {
    const size = Math.floor(sampleRate * seconds);
    this.ringL = new Float32Array(size);
    this.ringR = new Float32Array(size);
    this.writePos = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;
    const l = input[0];
    const r = input[1] || input[0];
    const n = l.length;
    const size = this.ringL.length;
    let w = this.writePos;
    for (let i = 0; i < n; i++) {
      this.ringL[w] = l[i];
      this.ringR[w] = r[i];
      w = (w + 1) % size;
    }
    this.writePos = w;
    return true;
  }
}

registerProcessor('ring-buffer', RingBufferProcessor);
