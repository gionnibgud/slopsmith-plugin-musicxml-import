# musicxml_import — Context

Slopsmith plugin. Imports MusicXML (`.xml` / `.musicxml`) files and produces
a `.sloppak` with notation format data (`notation_keys.json` +
`song_timeline.json`) and synthesized piano audio via FluidSynth.

**Requires:** Slopsmith `feat/notation-format` branch or later.

---

## Files

| File | Purpose |
|---|---|
| `plugin.json` | Plugin manifest (`private: true`, nav entry) |
| `screen.html` | Drag-and-drop import UI |
| `screen.js` | Frontend: file upload → `/upload`, build progress via WebSocket |
| `routes.py` | Backend: `/upload` POST + `/build` WebSocket |
| `mxml2notation.py` | Conversion library (MusicXML parse → notation wire format + MIDI) |

---

## Pipeline

```
.xml file
  → mxml2notation.parse_musicxml()
      → tempo map from <sound tempo> / <metronome>
      → beats: one per quarter note, downbeat measure≥1 / inner beats -1
      → notation: measure-structured (measure → staff → voice → beat → note)
          → staves: rh (G2 treble), lh (F4 bass), from <clef> elements
          → MIDI pitch from <pitch><step><alter><octave>
          → duration from <type> element → {1,2,4,8,16,32}
          → dots from <dot/> children
          → grace notes: grace:true beat, grace_slash:true when slash="yes"
          → ties: tied:true on continuation note
          → dynamics: direction-level + note-level (Option C, note wins)
          → articulations: stc, ten, ac, hac from <notations><articulations>
          → slurs: slr/slre from <notations><slur type="start/stop">
          → technical: ho, po, harm, fng from <notations><technical>
          → ornaments: txt="tr" from <trill-mark>, vib from <wavy-line>
          → accidentals: acc from <accidental> element
          → fermata: txt="fermata" from <notations><fermata>
          → hairpins: cre/dec from <wedge type="crescendo/diminuendo">
          → key sig: ks from <key><fifths>
          → time sig: ts from <time><beats><beat-type>
      → song_timeline: beats + rehearsal-mark sections
  → gp2midi.render_midi_to_audio() via bundled FluidSynth + GeneralUser-GS.sf2
  → mxml2notation.build_sloppak_zip()
  → dlc/sloppack/<title>_mxml.sloppak
```

---

## Sloppak output

```
<title>_mxml.sloppak/
├── manifest.yaml          arrangements[0]: id=keys, type=piano, notation=notation_keys.json
│                          song_timeline: song_timeline.json
│                          stems: [full.ogg] when audio succeeds
├── notation_keys.json     notation wire format (version=1, instrument=piano)
├── song_timeline.json     beats + sections (version=1)
└── stems/
    └── full.ogg           FluidSynth GM program 0 (Grand Piano)
```

`file:` is intentionally absent from the arrangement entry — the loader
on `feat/notation-format` supports this when `notation:` is present.

---

## Known limitations

| Limitation | Notes |
|---|---|
| **First part only** | Multi-part scores (piano + violin) import only part 1. A future version may produce one notation file per part. |
| **score-partwise only** | `score-timewise` not supported. |
| **No repeats** | Da capo, segno, repeat barlines not expanded — each measure plays once. |
| **Grace notes in audio** | Grace notes appear in the notation score (`grace: true` beat) but are absent from FluidSynth MIDI. Principal note timing is unaffected. |
| **grace_slash unrendered** | Slashed vs unslashed grace notes are recorded (`grace_slash: true`) but no renderer acts on the distinction yet — alphaTab has no separate alphaTex property. |
| **No .mxl** | Compressed MusicXML not supported — unzip before importing. |
| **Compound meter beats** | Beat emission uses quarter-note resolution throughout. In 6/8 etc. the dotted-quarter beat unit is not expressible in notation schema v1. |

---

## Dependencies

- `midiutil` — MIDI file generation (bundled in slopsmith environment)
- `pyyaml` — manifest serialisation (bundled in slopsmith environment)
- FluidSynth binary + `GeneralUser-GS.sf2` — available in the slopsmith-src
  Docker/OrbStack container environment via `gp2midi.render_midi_to_audio`
- `gp2midi.render_midi_to_audio` — imported from slopsmith core at build time
- stdlib `xml.etree.ElementTree` — XML parsing (no third-party XML dependency)

---

## Relationship to staffview

`staffview` reads the notation wire format delivered via the `notation_info` /
`notation_measures` WebSocket messages. Sloppaks produced by this plugin feed
directly into staffview's rendering pipeline without the `stf` wire key or
`staff_compat` shim used by the old musicxml_import prototype.

---

## Changelog

See `CHANGELOG.md`.
