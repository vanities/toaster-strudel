---
name: strudel-harmony
description: The craft of harmony and chord progressions for modern electronic and cinematic music — which progressions work and WHY, voice leading, borrowed chords, modal interchange, extended voicings (7ths, 9ths, sus), cadence and resolution, emotional function, key/mode choice. Use when someone asks "what chords", "a progression for", "make it sound sad/hopeful/epic/dark/dreamy", "what key or mode should I use", "voicing", "how to borrow a chord", "why does this feel off", or wants to move beyond basic triads.
---

The harmonic layer tells the listener *how to feel*. These are the non-obvious working rules — what producers actually reach for, and why the moves land.

## Key / mode choice (the first decision)

Pick the mode *before* writing notes. The mode dictates which borrowed chords are available and what every melody note implies.

| Mode | Character | Signature sound | Use for |
|---|---|---|---|
| Aeolian (natural minor) | Dark, heavy, conclusive | i–bVI–bVII / i–bVI–bIII–bVII | grief, weight, cinematic dread |
| Dorian | Minor + lift | i–IV (major IV!) | soul, deep house, Bonobo warmth |
| Phrygian | Dark + foreign | i–bII | tension, psytrance, unsettling |
| Lydian | Bright + floating | I–II (raised #4) | wonder, sci-fi shimmer |
| Mixolydian | Major + earthed | I–bVII | folk, rock, not saccharine |
| Major (Ionian) | Resolved, bright | I–IV–V | rarely what electronic needs alone |

**Dorian vs. natural minor rule of thumb:** does your minor progression have a major IV (e.g. D in Am)? That's Dorian — darker modes only if you want no lift at all. The ♮6 of Dorian is the single note that separates soulful from bleak.

## The progressions that always work (and why)

**i–bVI–bIII–bVII** (Aeolian loop)  
The backbone of electronic minor: Am–F–C–G. Never resolves — circles forever. Works because the bass descends by 3rds (A→F→C→G), each root a major 3rd or 5th from the last = chromatic-mediant smoothness. The most-used loop in trance, progressive house, ambient.

**i–bVII–bVI–V** (Andalusian cadence)  
Descending bass line A–G–F–E. The V is *major* even in minor (borrowed from harmonic minor), creating a gravitational pull back to i. Moody, Spanish, cinematic urgency. The descent IS the hook.

**i–iv** (minor to minor subdominant)  
The simplest emotional trigger. Am → Dm. The iv chord is borrowed from the parallel minor when you're in major; in natural minor it's diatonic but still hits hard. "Creep" (Radiohead) pivots on this.

**I–IV–V–I** (diatonic major)  
Statistically the most common pop loop. Avoid in isolation — too resolved. Add extensions (I^7–IV^9–V sus4) or borrow from parallel minor to inject weight.

**I–V–vi–IV** ("4 chords" / axis progression)  
C–G–Am–F. Warm, cyclical, harmonic momentum without darkness. Ubiquitous in pop. To de-genericize: (1) add 7ths, (2) borrow the vi→IV move in minor (i–bVI) instead, (3) change the bass against the chord.

**i–IV–V (Dorian)** e.g. Am–D–E  
The major IV (D from D Dorian/D major) is the upgrade over natural minor. Same tonic, brighter colour. Deep house signature.

**I–bVII–IV (Mixolydian)** e.g. C–Bb–F  
The "rock" loop, but works in electronic as a grounded, not-quite-major feel. The bVII is the borrowed chord; no minor 3rd so it never goes dark — just earthy.

## Borrowed chords (modal interchange)

These are the moves that make diatonic progressions feel *cinematic* without changing key.

- **iv in major** (Cm in C major / Fm in F major): instantly darkens. The IV→iv move is one of the most reliable emotional triggers in any genre.
- **bVI in major** (Ab in C major): warm, sweeping, "epic" lift. Used in every Zimmer cue. Puts you briefly in C minor without committing.
- **bVII in major** (Bb in C major): folk/rock openness, slightly unresolved. Borrowed from Mixolydian.
- **bIII in major** (Eb in C major): brightness from an unexpected direction. Often follows bVI.
- **II in major (Lydian borrow)** (D in C major): otherworldly, floating — the #4 implies Lydian even if you don't spell it out.
- **bII (Neapolitan / Phrygian)** (Db in C): dark, menacing, Spanish — use sparingly.

**The rule:** move the melody to a note *inside* the borrowed chord when it lands. The borrowed chord gains power when the melody occupies its chromatic note. Don't borrow harmonically while ignoring the lead melodically.

## Extended voicings — what they actually do

Triads are the skeleton. Extensions add emotional texture *without* changing function.

| Extension | Effect | Use when |
|---|---|---|
| maj7 | Warm, open, not resolved | pads, ambient; avoids "finished" feel |
| min7 | Melancholy, smooth | almost always better than bare minor |
| dom7 (x7) | Tension → wants resolution | V chord before a big I return |
| add9 / 9 | Colour + space, no extra tension | pop/soul flavour without full jazz |
| sus2 | Open, ambiguous, floaty | intros, breakdowns, non-committing |
| sus4 | Tension before resolving to 3rd | pre-resolution gesture; ratchets up arrival |
| min9 | Moody sophistication | deep house, neo-soul, Floating Points |
| maj9 | Dreamy, Lydian-adjacent | cinematic highs, shimmer |

**Key rule: sus resolves.** A sus4 chord demands its 3rd back — if it never gets it, the listener stays suspended (useful for drones). A sus2 is gentler: can sit indefinitely. Use `chord("Csus2").voicing()` or `chord("Fsus4").voicing()` in Strudel.

**Extended voicings muddy mixes when stacked dense.** The fix: spread voicings (open voicing across 2+ octaves), drop the 5th, don't double root + extension simultaneously in the bass. Strudel's `.voicing()` does this automatically — trust it.

## Voice leading — the invisible glue

Voice leading is why one progression *flows* and another feels choppy. Rules:

1. **Keep common tones stationary.** C major → Am: C and E are shared — don't move them.
2. **Stepwise motion in inner voices.** When you *must* move, move by step (semitone or tone), not leaps.
3. **Bass can leap; upper voices should crawl.** The root-position bass provides the harmonic anchor; the inner voices create the smoothness.
4. **Avoid parallel 5ths / octaves** between any two voices moving together — creates a hollow, medieval sound (unless that's intentional).
5. **Inversions are your shortcut.** Am/E → F/C means the bass descends stepwise (E→C) instead of leaping. The chord change stays audible; the *seam* disappears.

In Strudel, `chord("<Am F C G>").voicing()` applies automatic voice leading — it minimizes jumps by default (anchor defaults to c5). Force register: `.voicing().mode("above:c3")` for low-register pads.

## Cadence and resolution

**Authentic cadence (V→I):** strongest closure. Use it at a section END, not mid-loop.  
**Plagal cadence (IV→I):** softer, "amen". Church warmth or ambiguous close.  
**Half cadence (→V, stop):** leaves the listener hanging — perfect for build endings.  
**Deceptive cadence (V→vi):** V resolves to vi instead of I; surprise, continuation. Great for avoiding predictable drops.  
**Modal cadence (bVII→I):** no leading tone, open feeling. The Mixolydian/Dorian signature; never fully closes.

**Mistake to avoid:** ending a loop on I every four bars. The loop becomes a series of cadences and sounds like it restarts rather than flows. Favour progressions that end on a non-tonic chord or on a chord that implies the loop re-entering (bVII→back to i, etc.).

## Emotional function quick-reference

| Feeling | Goto move |
|---|---|
| Grief / weight | i–bVI–bIII–bVII (Aeolian); add iv |
| Hope within darkness | Dorian i–IV; add maj7 to the i |
| Cinematic epic | bVI–bVII–I in major; chromatic mediant jumps (I→bIII) |
| Tension / unease | bII (Neapolitan); V7 unresolved; sus4 held |
| Dreamy / floating | Lydian I–II; maj7/add9 voicings; sus2 drone |
| Soul / warmth | Dorian i–IV–bVII; minor 9ths |
| Bittersweet | Major key + borrowed iv; i + major IV (Dorian) |

## Common mistakes

- **Using only root-position triads:** the voicing IS part of the emotion. First inversion alone changes the weight of a chord.
- **Borrowing a chord but ignoring melody:** the melodic line must acknowledge the borrowed note or it sounds accidental.
- **Modal ambiguity without intent:** Dorian and natural minor share the same tonic triad — if your progression never reaches the IV or bVI, the listener can't tell which you're in. Commit.
- **Over-extension:** stacking 7–9–11–13 on every chord blurs harmonic identity. One or two extensions per chord reads cleaner.
- **The key-change trap:** transposing a loop up a minor 3rd for a "big moment" only works if the original section established a strong tonic. Move without gravity = confusion.

## In Strudel

```javascript
// Chord symbols + auto voicing (voice-leads by default, min-jumps to anchor c5)
chord("<Am F C G>").voicing()

// Set register
chord("<Am F C G>").voicing().mode("above:c3")

// Extended chords
chord("<Am7 Fmaj7 C9 Gsus4>").voicing()

// Scale-degree melody (never hits a wrong note)
n("0 2 4 3 1").scale("A:dorian")

// Arpeggiate a borrowed chord
chord("<Am Dm F E>").arp("up")
```

See [[strudel-pro-tips]] for `chord().arp()`, `.off()` harmonics, and scale-index details. See [[strudel-modifiers]] for the full `.voicing()` parameter list. See [[strudel-melody]] for melodic construction over these progressions.

Related: [[strudel-arrangement]] [[strudel-melody]] [[strudel-groove]] [[strudel-mixing]] [[strudel-sound-design]] [[strudel-genres]] · mechanics: [[strudel-compose]] [[strudel-pro-tips]] [[strudel-modifiers]]

Sources: [Strudel Tonal Docs](https://strudel.cc/learn/tonal/) · [Strudel Voicings](https://strudel.cc/understand/voicings/) · [LANDR: Cinematic Chord Progressions](https://blog.landr.com/cinematic-chord-progressions/) · [ComposerDeck: Modal Interchange](https://composerdeck.com/modal-interchange.html) · [Native Instruments: Voice Leading](https://blog.native-instruments.com/voice-leading/) · [Signals Music Studio: Sus Chords Advanced](https://signalsmusic.studio/lessons/sus-chords-advanced) · [Scaled Guitar: Dorian vs Natural Minor](https://www.scaledguitar.com/theory/dorian-vs-natural-minor) · [Abducted Android: Ambient Chord Progressions](https://abductedandroid.vuilniszak.be/insights/the-art-of-chord-progressions-in-ambient-music) · [WeMakeDanceMusic: EDM Progressions](https://www.wemakedancemusic.com/en/news/chord-progressions-that-work-for-every-edm-genre) · [ProductionMusicLive: Voice Leading](https://www.productionmusiclive.com/blogs/news/these-notes-make-chord-progressions-flow-voice-leading)
