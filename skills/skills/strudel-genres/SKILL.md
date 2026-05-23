---
name: strudel-genres
description: Genre blueprints for electronic music — tempo ranges, drum-pattern signatures, bass character, structure, key sounds, and the one defining rule for each genre. Use when writing a techno/house/dnb/ambient/trance/IDM/dubstep/synthwave/lo-fi/downtempo/trip-hop track, asking "what BPM for X", "make it sound like [genre]", or needing genre conventions before composing. Distinct from the style-* skills (individual producers); this is the shared construction grammar every producer in that genre follows.
---

**How to read these blueprints:** each entry is a composing checklist. Hit the BPM, lock the drum pattern, then layer the rest. One wrong element (e.g., four-on-the-floor kick in DnB) instantly breaks genre plausibility.

**setcps reference:** `setcps(bpm / 60 / 4)` maps BPM to Strudel's cycle clock (one cycle ≈ one 4/4 bar). Examples: `setcps(0.5)` = 120 bpm · `setcps(0.533)` ≈ 128 bpm · `setcps(0.583)` ≈ 140 bpm · `setcps(0.708)` ≈ 170 bpm. For mechanics (swing, syncopation, sidechain) see [[strudel-groove]]; for sounds see [[strudel-sample-library]]; for arrangement arcs see [[strudel-arrangement]].

---

## House (Classic / Chicago / NY)

| | |
|---|---|
| **BPM** | 120–130 (sweet spot 124–126) |
| **setcps** | `setcps(0.517)` @ 124 bpm |
| **Drum signature** | Four-on-the-floor kick, clap/snare on 2+4, steady off-beat hi-hats (16ths with occasional open hat) |
| **Bass** | Sub-bass or organ bassline; root-note, slightly bouncy; shares low-end with kick via sidechain |
| **Structure** | 8-bar loops; 4-bar intro percussion → add bass/stab → add vocal chop → breakdown → rebuild; DJ-friendly with 16-bar intro/outro |
| **Key sounds** | Soulful vocal chops, Rhodes/piano stab, TB-303 acid line (acid house), clap with room reverb |
| **The one rule** | **That kick never skips.** Remove any element except the four-on-the-floor; that's still house. Drop the kick and it isn't. |

---

## Techno (Berlin / Industrial)

| | |
|---|---|
| **BPM** | 128–145 (classic 130–138; peak-time 140+) |
| **setcps** | `setcps(0.558)` @ 134 bpm |
| **Drum signature** | Four-on-the-floor but kick is long, punchy, engineered — NOT the warm house thump. Dense metallic hi-hats, ride-heavy percussion, no melodic clap (or a very dry snare) |
| **Bass** | Minimal, looping sub; often a pulsing sine or distorted low-mid growl; avoids melodic basslines |
| **Structure** | Long arcs 8–10 min; elements added/removed in 8–16 bar blocks; breakdowns strip to hi-hats/ride then slowly re-introduce; no verse/chorus |
| **Key sounds** | Processed 909 kick, metallic ride, acid TB-303 loop, industrial noise sweeps, sparse dark pad |
| **The one rule** | **Repetition IS the content.** A two-bar loop running for 4 minutes with one filter slowly opening is more techno than a busy track that goes somewhere every 8 bars. |

---

## Deep House

| | |
|---|---|
| **BPM** | 110–125 (typical 118–122) |
| **setcps** | `setcps(0.492)` @ 118 bpm |
| **Drum signature** | Softer four-on-the-floor (often 808-style), muted hi-hats with swing, minimal percussion; snare/clap pushed back in the mix |
| **Bass** | Warm sub-bass, slightly filtered; often follows simple 2-bar chord riff; never aggressive |
| **Structure** | Slow builds; a lot of space; pads/chords introduced gradually; spoken-word or soulful vocal fragments; long breakdown |
| **Key sounds** | Muted gospel piano, jazz-chord Rhodes, warm Juno pad, filtered soulful vocal, sparse rim shot |
| **The one rule** | **Warmth and space above density.** If the mix is crowded, it's not deep house. Every element should breathe. |

---

## Melodic House & Techno (Afterlife / Innervisions sound)

| | |
|---|---|
| **BPM** | 120–128 (typically 122–125) |
| **setcps** | `setcps(0.508)` @ 122 bpm |
| **Drum signature** | Four-on-the-floor with warm kick; snappy clap on 2+4; rolling closed hats with open hat lifts every 2 bars; sidechain pumping on pads/bass |
| **Bass** | Moog-style root-note sub, pulsing 8th/16th rhythm; minimal but present; never a wobble |
| **Structure** | 32-bar macro blocks: intro (drums+atmo) → build (add bass+arp) → drop (full arrangement+lead) → breakdown (pad-only) → climax |
| **Key sounds** | Arpeggiated minor synth (heavy reverb+delay), layered pads (bright/mid/low), evolving filter automation, cinematic swells |
| **The one rule** | **The arp IS the hook.** One looping arpeggio through heavy reverb/delay does what a 16-bar melody does in pop. Let it hypnotize; don't add more notes to "develop" it. |

---

## Drum & Bass (Liquid / Neurofunk / Standard)

| | |
|---|---|
| **BPM** | 160–180 (classic 174) |
| **setcps** | `setcps(0.725)` @ 174 bpm |
| **Drum signature** | **Syncopated breakbeat — NOT four-on-the-floor.** Amen break chop is the template: kick off the one, snare on the 2.5, ghost notes and rapid 16ths. Pattern changes every 1–2 bars |
| **Bass** | Two-register split: sub-bass weight (low) + Reese mid-range texture (growling detuned saw). Liquid DnB: smooth rolling sub. Neurofunk: designed/distorted mid-bass |
| **Structure** | 8-bar sections; intro builds tension (no bass drop yet) → bass drops at 32 bars → breakdown → second drop harder; 5–6 min |
| **Key sounds** | Chopped Amen break, Reese bass, atmospheric pads, vocal samples, snare roll fills |
| **The one rule** | **The break is not a loop — it's a conversation.** Every 1–2 bars it mutates: ghost note in, snare displaced, kick added. Static break = not DnB. |

---

## Jungle

| | |
|---|---|
| **BPM** | 160–175 (raw jungle often 170–175) |
| **setcps** | `setcps(0.708)` @ 170 bpm |
| **Drum signature** | Heavier sampled break chops (Amen, Apache, Think); raw, less surgical than DnB — swing and funk preserved; layered with sub-hits and percussion samples |
| **Bass** | Dub/reggae bassline character — rolling, pitched, melodic sub; also sampled upright bass chops; reggae-ragga vocal samples over the top |
| **Structure** | Similar 8-bar blocks to DnB; more sampling-dense; vocal snippets from ragga/dancehall signal section changes |
| **Key sounds** | Amen break (raw, not over-processed), ragga/dancehall vocal samples, sub-bass from dub tradition, reggae organ |
| **The one rule** | **Dub in the roots.** The bass should feel like it came off a Lee Perry dub plate before it came off a rave floor. Reggae DNA is non-negotiable — without it, it's just fast DnB. |

---

## Dubstep / UK Bass

| | |
|---|---|
| **BPM** | 138–142 (felt at 69–71 bpm half-time); UK bass spans 120–140 |
| **setcps** | `setcps(0.583)` @ 140 bpm |
| **Drum signature** | **Half-time feel**: kick NOT on every beat — often on 1 and 3 with offset hits; snare/clap on beat 3 (not 2+4); syncopated shuffled hats; triplet feel common |
| **Bass** | The wobble: LFO-modulated low-pass filter on a sine/saw bass (rate = groove tempo); or heavy sub-bass drops with silence around them. UK bass is darker, more minimal; brostep is distorted and maximalist |
| **Structure** | Intro → verse (sparse, atmospheric) → drop (wobble/bass enters) → break → second drop; emphasis on the contrast between sparse and dense |
| **Key sounds** | Wobbly LFO bass, pitched sub-bass stab, spacious reverb on snare, dark atmospheric pad, sparse percussion |
| **The one rule** | **Dubstep lives in the gaps.** The silence between notes, the space around the bass hit — that's where the genre breathes. A continuous wall of sound is wrong. |

---

## Ambient

| | |
|---|---|
| **BPM** | 60–90 or none (free-floating) |
| **setcps** | `setcps(0.25)` @ 60 bpm; or use very slow cycles as texture time, not beat time |
| **Drum signature** | Usually absent; if present: sporadic, processed into texture (reverb-washed hit = a sound event, not a beat) |
| **Bass** | Long-sustained low tones; not a bassline — a drone or harmonic foundation. Changes rarely (once per 30–60 sec) |
| **Structure** | No traditional structure. Evolution: elements introduced, held, transformed, dissolved. Silence is compositional. Eno's rule: any element should be able to drop out without the piece "ending." |
| **Key sounds** | Heavily reverbed/delayed pads, field recordings, granular textures, sustained string or choir tones, sine drones |
| **The one rule** | **Stillness is the content.** Nothing should demand attention; everything should reward it. If an element is "catchy," filter it back or add reverb until it dissolves into the texture. |

---

## Downtempo / Trip-Hop

| | |
|---|---|
| **BPM** | Trip-hop: 70–90 (max 90) · Downtempo: 80–110 |
| **setcps** | `setcps(0.333)` @ 80 bpm |
| **Drum signature** | Slow sampled breakbeat with heavy swing; hip-hop-style (not four-on-the-floor); kick on 1 (+3 sometimes), snare on 2+4; dusty, compressed, slightly lo-fi |
| **Bass** | Hip-hop-style bass: root-note driven, bouncy, prominent but not complex; dub pressure on the low end; often live bass feel via sampling |
| **Structure** | Song-ish: intro/verse/hook/bridge; 3–5 min; vocals (often noir, female, haunted) anchor structure; instrumental sections between |
| **Key sounds** | Dusty vinyl-sampled break, Portishead theremin-style lead, jazz brass/vibes sample, noir Rhodes, sparse string pad, distant reverb |
| **The one rule** | **Melancholy + groove simultaneously.** The beat must feel good to move to AND feel sad at the same time. If it's just sad, it's ambient. If it's just groovy, it's hip-hop. The Bristol tension is both at once. |

---

## Lo-Fi Hip-Hop

| | |
|---|---|
| **BPM** | 70–90 (sweet spot 75–85) |
| **setcps** | `setcps(0.333)` @ 80 bpm |
| **Drum signature** | Sampled breakbeat, heavily swung; sidechain pumping; kick on 1+3, snare on 2+4; hi-hats with velocity variation; intentional imprecision (slightly behind the beat) |
| **Bass** | Simple, melodic; follows chord roots; warm, rounded; often electric bass or bass guitar sample |
| **Structure** | Loops dominate (often 2–4 bar repeating phrase); minimal structural change; the whole track IS the vibe, not a journey |
| **Key sounds** | Vinyl crackle/noise layer, tape saturation, jazz 7th/9th chords (Rhodes or piano), detuned guitar lick, muffled bass, rain/café ambience |
| **The one rule** | **The imperfection is the perfection.** Add vinyl crackle, pitch the sample slightly flat, add subtle wow/flutter. Clean and polished is the wrong direction — grit is the genre marker. |

---

## Trance (Progressive / Uplifting / Psytrance)

| | |
|---|---|
| **BPM** | Progressive: 128–135 · Uplifting: 136–145 · Psytrance: 145–150 |
| **setcps** | `setcps(0.567)` @ 136 bpm |
| **Drum signature** | Four-on-the-floor kick (crisp, punchy); sharp clap/snare on 2+4; 16th-note closed hats; often a ride for drive; reverb on clap for size |
| **Bass** | Driving 16th-note bassline on root note (the "pumping trance bass"); sidechained to kick; disappears in breakdowns |
| **Structure** | Strict 8-bar blocks: 16-bar intro (kicks only) → build (hats+bass, 32 bars) → breakdown (everything drops except pads, 16–32 bars) → buildup (noise sweep, filter rise) → drop (full arrangement); 7–9 min total |
| **Key sounds** | Supersaw lead (chord stabs or melody), sweeping LPF filter ramp into the drop, reverse cymbal before drop, arpeggiated pluck, long sustained pad in breakdown |
| **The one rule** | **The breakdown earns the drop.** Strip every drum and bass element. Let the melodic hook float alone over a pad. Then the sweep, then the snare roll, then the drop. The emotional payoff only works if the silence before it is real. |

---

## IDM / Breakbeat Electronica

| | |
|---|---|
| **BPM** | 100–140 (highly variable; often unstated or irregular) |
| **setcps** | `setcps(0.5)` @ 120 bpm as a starting point; patterns create perceived tempo |
| **Drum signature** | Deliberately irregular: unconventional time signatures (5/4, 7/8), polyrhythms, glitch edits, breakbeat fragments that skip/stutter; the beat is a texture not a grid |
| **Bass** | Ranges from absent (ambient IDM) to complex designed mid-bass; often sine or softsynth bass that changes role bar-to-bar |
| **Structure** | Anti-structural: long evolving pieces; no drop/breakdown convention; tension/release created through texture density shifts and rhythmic unpredictability |
| **Key sounds** | Glitched breakbeat, granular texture, processed natural sounds, complex FM synthesis, Aphex Twin-style polyrhythm, Autechre-style quantize-free percussion, Boards of Canada detuned nostalgia |
| **The one rule** | **Break the grid intentionally, not accidentally.** IDM sounds designed — every skip and stutter was chosen. Randomness that sounds random = lo-fi. Randomness that sounds inevitable = IDM. |

---

## Synthwave / Outrun

| | |
|---|---|
| **BPM** | 80–118 (most common 90–105; Outrun subgenre can push 128–140) |
| **setcps** | `setcps(0.408)` @ 98 bpm |
| **Drum signature** | Four-on-the-floor kick OR kick on 1+3 only; big reverb-washed snare on 2+4; gated snare effect; analog drum machine sounds (LinnDrum, TR-808/909 adjacent); closed hats start sparse, build with track |
| **Bass** | 8th-note root-note bass following chord progression; clean, round; sometimes sequenced arpeggio doubling the bass |
| **Structure** | Song-like: intro/verse/chorus/bridge/outro; 3–5 min; cinematic swells signal section changes; instrumental or sparse vocals |
| **Key sounds** | Detuned supersaw / Juno-106 pad, bright arpeggio lead, gated reverb snare, 80s chorus/phaser on synths, slow LFO filter sweep on pad |
| **The one rule** | **80s nostalgia is the instrument.** Every sound should feel like it came from a 1984 synthesizer: warm, slightly detuned, chorus-washed, reverb-heavy. Clinical modern digital tones break the spell immediately. |

---

## Quick-reference BPM table

| Genre | BPM range | setcps (midpoint) |
|---|---|---|
| Lo-fi hip-hop | 70–90 | `setcps(0.333)` (80) |
| Trip-hop / Downtempo | 70–110 | `setcps(0.354)` (85) |
| Ambient | 60–90 or none | `setcps(0.292)` (70) |
| Synthwave | 80–118 | `setcps(0.408)` (98) |
| Deep House | 110–125 | `setcps(0.492)` (118) |
| House | 120–130 | `setcps(0.517)` (124) |
| Melodic House/Techno | 120–128 | `setcps(0.508)` (122) |
| Dubstep / UK Bass | 138–142 | `setcps(0.583)` (140) |
| Techno | 128–145 | `setcps(0.558)` (134) |
| Trance (Progressive) | 128–135 | `setcps(0.554)` (133) |
| Trance (Uplifting) | 136–145 | `setcps(0.567)` (136) |
| IDM / Breakbeat | 100–140 | `setcps(0.500)` (120) |
| Jungle | 160–175 | `setcps(0.708)` (170) |
| Drum & Bass | 160–180 | `setcps(0.725)` (174) |

---

## Cross-genre notes for composing agents

- **Tempo alone does not make genre.** 130 bpm + four-on-the-floor + metallic hats = techno. Same BPM + soulful vocal chop + Rhodes = house. Same BPM + rising supersaw stabs = trance. The drum pattern + bass character lock the genre.
- **Four-on-the-floor is the dividing line:** house/techno/trance/melodic-house all use it. DnB/jungle/IDM/dubstep/trip-hop/lo-fi all break it.
- **Sub-bass treatment:** genres split into "sub carries the groove" (dubstep, DnB) vs "sub supports the harmony" (house, deep house, melodic) vs "sub is absent or dronal" (ambient, IDM).
- For Strudel drum pattern mechanics → [[strudel-groove]]. For sound selection → [[strudel-sample-library]]. For arrangement arcs → [[strudel-arrangement]]. For melodic/harmonic choices within genre → [[strudel-melody]] and [[strudel-harmony]]. For mix decisions → [[strudel-mixing]]. For synth/sound design → [[strudel-sound-design]]. For high-leverage techniques → [[strudel-pro-tips]]. For section timing and transitions → [[strudel-conduct]] and [[strudel-transitions]]. For Strudel mechanics → [[strudel-compose]].
- Individual producer styles that exemplify these genres → the `style-*` skills (Bonobo = melodic downtempo/deep house; Kiasmos = melodic techno/ambient; Skee Mask = IDM/techno; DJRUM = techno/jungle; Floating Points = deep house/IDM).

---

Sources: [Ableton Learning Music — Tempo and Genre](https://learningmusic.ableton.com/make-beats/tempo-and-genre.html) · [Beat Kitchen — Genre Landscape](https://beatkitchen.io/guides/electronic-music/01-genre-landscape/) · [London Sound Academy — EDM Genres List](https://www.londonsoundacademy.com/blog/list-of-electronic-dance-music-genres) · [Beatportal — Melodic House & Techno Step-by-Step](https://www.beatportal.com/articles/899368-step-by-step-guide-to-creating-a-melodic-house-techno-track-anyma-miss-monique-artbat-stephan-bodzin) · [Sound On Sound — Dubstep Basics](https://www.soundonsound.com/techniques/dubstep-basics) · [EDMProd — How to Make Jungle](https://www.edmprod.com/how-to-make-jungle-music/) · [MusicRadar — Trip-Hop Sound](https://www.musicradar.com/tutorials/the-core-thing-to-remember-is-that-your-beats-are-slow-90-bpm-maximum-and-they-are-filthy-unpacking-the-dark-sample-based-sound-of-trip-hop) · [House of Tracks — Synthwave BPM](https://houseoftracks.com/faq/what-is-the-typical-tempo-range-for-synthwave-music) · [Myloops — Trance Song Structure](https://www.myloops.net/trance-song-structure-breakdown-basics) · [Vision3Deep — Jungle vs DnB](https://vision3deep.com/jungle-drum-and-bass/jungle-vs-drum-and-bass-key-differences-in-style-tempo-and-culture/)
