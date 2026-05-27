---
name: strudel-mixing
description: The craft of making a mix sound pro and clear — frequency carving so each voice owns a band, low-end (kick vs. bass pocket, mono sub, sub vs. mid-bass), gain-staging and headroom, sidechain/ducking, panning and stereo width, depth via reverb/delay (front-to-back layers), and why amateur mixes sound muddy or flat. Use when the mix is muddy, things are fighting, gain-staging, EQ, low end, sidechain, it sounds flat, it sounds cluttered, too much reverb, nothing has space, or voices are masking each other.
---

> See [[strudel-sample-library]] § "Mixing pitfalls that read as not playing" for gain floors, VCSL amplitude ratios, and hpf over-cutting — this skill does NOT repeat those. It covers the broader craft of WHY a mix sounds pro.

## The core principle: every voice owns a band

A professional mix is a frequency map. Each element claims a region; nothing fights for the same turf. The mix sounds clear not because everything is turned up, but because nothing is in anyone else's way.

- **Full-range voices are the #1 culprit.** A pad running 40 Hz–15 kHz competes with kick, bass, melody, and air simultaneously. That is four fights at once.
- **Subtractive EQ beats additive.** Cut the frequencies a voice *doesn't need* before boosting the ones it does. A hi-hat has no reason to exist below 800 Hz — high-pass it. A pad doesn't need 40–80 Hz — high-pass it. Each HPF frees headroom the kick and bass need.
- **The mud zone is 200–500 Hz.** Every instrument has *some* energy here. It accumulates fast. The fix: cut non-bass instruments in this range rather than boosting your way out of it.

## Low end: the kick–bass relationship

The kick and bass together form the rhythmic and tonal spine. They must *complement*, not stack:

- **Give each its pocket.** Kick fundamental typically 50–65 Hz; bass fundamental 80–120 Hz. Boost the kick slightly at its fundamental, cut the bass there. Reverse on the bass. Neither should dominate the *same* Hz.
- **Tune them to each other.** A kick tuned to A and a bass root of D# will fight harmonically regardless of EQ. Tune the kick to the track's root (or the bass root note) so the two lock as one object.
- **Sub (20–80 Hz) vs. mid-bass (80–200 Hz).** Sub is felt, not heard on small speakers. Mid-bass is what gives weight on phones/laptops. A good mix has *both*: sub for the room, mid-bass for translation. A sine-wave sub alone vanishes on laptops — use `triangle` or `sawtooth` with `lpf` ~600–800 to get harmonics into the mid-bass band.
- **Keep kick transient distinct.** The kick's *click* lives at 2–5 kHz — that's what punches through a mix. The sub thud alone doesn't cut; the high-mid transient does. Don't low-pass the kick so hard it loses its attack (see [[strudel-sample-library]]).
- **Mono bass below ~150–200 Hz is law.** Our ears can't localize bass; a panned sub just causes phase cancellation when summed to mono. Keep kick and bass `.pan(.5)` (center). Width lives in mids and highs.

## Gain-staging and headroom

- **Target individual voices at −18 to −12 dBFS average.** Leave peaks no hotter than −6 dBFS per track before summing. Stacking 8 voices at −6 dBFS each clips the mix bus.
- **The stack accumulates.** Ten voices at `.gain(0.5)` adds up. Work the summed level — if the overall mix is clipping or squashing, the fix is gain on individual voices, not just pulling the master down.
- **Loudness target for streaming: −14 LUFS integrated.** Don't chase loudness in the mix; leave headroom for mastering. A mix peaking at −3 dBFS going in has nowhere to go.
- **Velocity / gain variation is dynamics.** A flat `.gain(0.5)` on every hit is metronomic. Use `.gain(".8 .4 .6 .4")` or `gain(perlin.range(.3,.6))` for natural dynamics that preserve headroom by breathing.

## Sidechain / ducking (the pump and the pocket)

Sidechain is not just a stylistic pump — it's a mixing tool that prevents kick and bass from arriving simultaneously at full volume:

- **Strudel's method:** `duckorbit(N)` on the kick triggers an envelope that ducks whatever is on `.orbit(N)`. Pair with `.duckattack(0.01)` (fast, transparent) or `.duckattack(0.2)` (slow, audible pump). `.duckdepth(1)` = full duck.

```javascript
// Kick ducks the bass on orbit 2
stack(
  s("bd!4").bank("RolandTR909").duckorbit(2).duckattack(0.01),
  note("C2 ~ Eb2 ~").s("sawtooth").lpf(400).orbit(2).gain(0.7)
)
```

- **Audible pump** (house/techno) → slow attack (~0.1–0.3s), deep depth → the bass visibly ducks on every kick. This IS the groove in much dance music.
- **Transparent pocket** (jazz, ambient) → fast attack (<10ms), shallow depth (~0.3–0.5) → just creates space, imperceptible as an effect.
- **`.compressor()`** in Strudel (syntax: `compressor("threshold:ratio:knee:attack:release")`) compresses a voice's own dynamics but does NOT do cross-signal sidechain — use `duckorbit` for kick→bass ducking.

## Panning and stereo width

- **The center is sacred: kick, bass, lead.** These anchor the mix. Spreading them wide = phase issues and lost punch.
- **Width lives in the mids and highs.** Hats, shakers, pads, reverb returns, secondary percussion → spread these. They're what makes a mix *wide*.
- **Avoid the "everything hard-panned" trap.** Extreme L/R with nothing in the mid feels hollow. Pan in graduated steps: `.pan(.3)` / `.pan(.7)` creates width without emptying the center.
- **Stereo width from detune, not pan.** `.add(note("0,.07"))` or layering a voice slightly detuned fills width without phase risk. This is the Kiasmos/Rone pad-fattening technique — see [[strudel-pro-tips]].
- **Check in mono.** If a wide element collapses or disappears in mono, it has phase cancellation. Mono compatibility is non-negotiable for streaming/club.

## Depth: front-to-back layering with reverb and delay

A flat mix has everything at the same perceived distance. A pro mix has a **z-axis**:

| Layer | Treatment | Perceived depth |
|---|---|---|
| Kick, bass, snare | Dry or very short (<20ms) | Front, immediate |
| Lead melody | Short room or plate, pre-delay 15–25ms | Near-front |
| Counter-melody, call-response | Medium reverb, some delay | Mid-field |
| Pad, ambient texture | Long reverb (rsize 4–8), high delay feedback | Background |
| Risers, field recording | Saturated reverb + delayfeedback ~0.8 | Distant |

- **Pre-delay is the trick professionals use.** Adding ~15–20ms pre-delay before the reverb keeps the dry signal *present* while the tail floats behind it. Without pre-delay, reverb sits on top of the dry signal and muddies the attack.
- **Reverb on the low end = mud.** High-pass the reverb send at 200–300 Hz. Don't reverb the kick or bass — it blooms in the mud zone and destroys punch.
- **Delay as width, not clutter.** A short (1/8th or 1/16th) stereo delay panned L/R on a melody fills width and depth without adding frequency content. See [[strudel-effects]] for `.delay()` / `.delaytime()` / `.delayfeedback()` mechanics.

## Strudel's EQ toolkit and its limits

Strudel has **no per-band parametric EQ** (no surgical 3 dB cut at 340 Hz). The workarounds:

- **`.lpf(N)`** — removes everything above N. Use to keep voices band-limited and out of the highs.
- **`.hpf(N)`** — removes everything below N. The most powerful mud-fighting tool. Apply to pads, melody, shakers — anything that doesn't *need* low-end.
- **`.bpf(N).bpq(Q)`** — bandpass; useful for telephone/lo-fi textures or targeting a vocal formant.
- **Stacking lpf + hpf = a crude bandpass.** `.hpf(300).lpf(3000)` limits a pad to the mid band only.
- **Resonance (`.lpq()`, `.hpq()`) = emphasis at the cutoff.** Useful for filter sweep character; dangerous if it pushes an already-crowded band higher.
- Full syntax for all filter/effect parameters → [[strudel-effects]].

## The five things that make amateur mixes sound muddy

1. **Full-range pads.** A sustained synth pad with no HPF occupies the entire spectrum. It's not a pad — it's a wall. HPF at 200–400 Hz and it becomes a pad.
2. **Low-mid accumulation.** Kick + bass + piano + guitar + pad all have energy at 200–400 Hz. None of them need all of it. Cut each slightly in this zone.
3. **Reverb without pre-delay (or on the bass).** Reverb on bass = boom in the mud zone. Reverb without pre-delay = smear on the attack.
4. **No gain variation across voices.** Every voice at equal loudness = no hierarchy. The ear doesn't know what to listen to, so it hears noise.
5. **Center-only mixing with no z-axis.** Everything panned center and equally close = flat wall. Spread panning + reverb depth = three-dimensional mix.

## Loudness & master level (Strudel does NOT auto-normalize)

Per-voice `.gain()` values ARE the master level — nothing fills the headroom for you. Conservative gains (a pad at 0.08, a mix peaking ~0.4) sound *soft* because the top half of the range sits unused. To make a track louder:

- **Scale per-voice — that's the reliable lever.** Multiply each voice's `.gain()` up. It multiplies linearly and preserves balance. Render and check `peak` < ~0.9 (1.0 = clip).
- **A master `.gain()` on the outer `stack(...)` is NOT a clean trim** — in this engine it behaved pathologically (clipping + harsh flatness at 1.3 *and* 2.0, identical; it blasts even near-silent voices like hats to the ceiling instead of scaling the summed bus). Don't reach for `stack(...).gain(x)` as a master fader. Scale voices, or use a real limiter (`.compressor()`).
- **The loudest voice (usually the kick) caps the global boost.** Pushing a kick past ~1.0 gain distorts it. If a uniform scale sends the kick over, cap it (~0.8) and let the other voices come up around it.
- **"Harsh" flatness on a *louder* mix is usually the [[silence artifact]], not real distortion.** Flatness is scale-invariant, so a uniform level change can't truly raise it — check `peak` first: if `peak` < 1.0 nothing's clipping, and the high flatness is the near-silent reverb-tail frames (amplified when louder loud-sections widen the dynamic gap). Fix by narrowing dynamics (lift the quiet-section floors), not by darkening. (tarn: per-voice ×1.6 read flatness 0.09 / dyn 1408× with peak 0.56 — lifting the intro/breakdown/outro floors snapped it back to 0.0001 / dyn 3.6, same loudness.)

## Measure it: warm vs harsh vs dull (the ears)

Don't trust a mix you can't hear cleanly — **measure** it. Render the track headlessly (`node tools/render-wav.mjs <id>` → WAV) and read its spectral profile (`tools/measure-wav.py`), then compare to the reference card. Two numbers diagnose most problems:

- **Spectral flatness = noise / harshness.** Clean, tonal mixes sit ~0.001–0.02. Above ~0.05 the mix is noise-like — almost always too many bright voices stacked in one band (or open hi-hats). This is the single clearest harsh-vs-clean signal.
- **Spectral centroid = bright vs dull.** Aim for the artist's card zone. Too high → harsh/brittle; too low → dull/muffled.

Worked example — this project's own cranks, all measured:

| track | centroid | flatness | verdict |
|---|---|---|---|
| gyre (Kiasmos) — loved | 872 | 0.0037 | warm **+ pristine** |
| glade (Mitsuda) — loved | ~1176 | 0.0007 | warm **+ pristine** |
| cobalt (scrapped) | 2191 | **0.068** | bright **+ noisy** (3 stacked squares + busy hats) |
| grotto v1 | 593 | 0.0001 | clean but **dull** (bare triangles) |
| tarn (Skee Mask) | 469 | 0.0001 | warm-dark **+ pristine** (raised centroid tonally — see below) |

The lesson: **warmth ≠ dullness, and brightness ≠ harshness — they're different axes.**
- **Harsh = high flatness** (noise). Fix by THINNING — fewer bright voices, carve them into separate bands — *not* by darkening. (tarn: pushing 808 hi-hats up for "presence" spiked flatness 0.0001 → **0.07**, cobalt-harsh range. Hats are *noise* — they buy centroid and harshness together. Pulling them to near-silent texture restored 0.0001.)
- **Dull = low centroid from harmonically-poor waveforms** (bare `triangle`/`sine`). Fix by reaching for **rich REAL instruments** — `gm_string_ensemble`, `piano`, `gm_cello`, `gm_koto`, `gm_flute` — which carry presence in the low-mids while staying warm. *Not* by adding raw-synth brightness (→ harsh) or a noisy sparkle layer (→ flatness spike; a high `triangle` arp once pushed grotto from 0.0001 to 0.18).
  - **A FILTERED saw/square is also a valid tonal centroid-lifter** (the "raw-synth brightness → harsh" warning is about *unfiltered / high-cutoff* synths). tarn's dull triangle hook (centroid 318) → `sawtooth` under `lpf(960)` lifted centroid to **465 with flatness still 0.0001**: a low-passed saw adds warm *mid*-harmonics (centroid up) with no high-freq noise (flatness flat). Put the brightness on a LOUD tonal voice (the bass hook/pad), since loud dark voices are what pin the centroid down.
- **Gotcha when measuring a whole dynamic ARC (not a steady loop):** near-silent + heavily-reverbed sections inflate the *average* flatness — diffuse reverb tails are broadband, so silence-drenched-in-reverb reads as "noise." If flatness is high but no single section sounds noisy, suspect **reverb-wash-in-silence** (tarn hit 0.09 at 477× dynamics this way). Fix: keep quiet sections quiet but **DRY/tonal** (cut room+delay-feedback in the dip), not washed.
- The pro recipe (gyre/glade, both loved): **real warm instruments + ruthless tonal discipline (no noise layers) + every voice carved into its own band + filter movement + a big dynamic arc.**

## Related skills

Compositional structure → [[strudel-arrangement]]; the dynamic arc across sections → [[strudel-transitions]]; effects syntax → [[strudel-effects]]; sample gain floors and VCSL levels → [[strudel-sample-library]]; pro technique shortcuts → [[strudel-pro-tips]]; sound design (synth timbres to layer) → [[strudel-sound-design]]; genre-specific treatment → [[strudel-genres]].

Sources: [Production Music Live — EQ Kick & Bass](https://www.productionmusiclive.com/blogs/news/how-to-eq-kick-and-bass-for-powerful-low-end) · [LANDR — EQ Kick and Bass](https://blog.landr.com/eq-kick-and-bass/) · [Sonarworks — Eliminate Competition Between Kick and Bass](https://www.sonarworks.com/blog/learn/eliminate-competition-between-the-kick-and-bass) · [Sonarworks — Sidechain Compression](https://www.sonarworks.com/blog/learn/sidechain-compression) · [iZotope — What is Sidechain Compression](https://www.izotope.com/en/learn/what-is-sidechain-compression) · [LANDR — Headroom in Audio](https://blog.landr.com/headroom-audio/) · [Flotown Mastering — Center That Sub](https://flotownmastering.com/blog/center-that-sub) · [Dead Set Live — Why Your Mix Is Muddy](https://deadsetlive.com/home-studio-acoustics/why-mixes-sound-muddy/) · [DemoMentor — 13 Mixing Mistakes](https://www.demomentor.com/production/mixing-mistakes) · [Strudel — Audio Effects](https://strudel.cc/learn/effects/) · [Strudel forum — Sidechain in Strudel](https://uzu.lurk.org/t/sidechain-in-strudel/5792) · [Strudel PR #1470 — duck/duckorbit](https://codeberg.org/uzu/strudel/pulls/1470)
