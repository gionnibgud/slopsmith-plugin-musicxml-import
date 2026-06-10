# Changelog

All notable changes to `slopsmith-plugin-musicxml-import` are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Fixed

- Compound and irregular meter beat emission. Beat ticks in `song_timeline.json`
  now use the primary beat unit (dotted quarter for 6/8, 9/8, 12/8) rather than
  the quarter note. `beat_groups` is written onto compound/irregular measure dicts;
  `beat_pos` is written onto every non-downbeat notation beat.
- `beat_pos` resolution raised to 16th-note granularity (`ts_beat_type * 4`)
  so notes at 8th and 16th positions within a measure have distinct values.
  Previously the quarter-note denominator caused collisions for sub-beat notes.
- Output filename no longer doubles the `_mxml` suffix when the title extracted
  from the MusicXML already ends with the word "mxml".

---

## [0.1.0]

### Added

- `mxml2notation.py` — MusicXML to notation wire format conversion library.
  Produces `notation_<id>.json` (notation format v1) and `song_timeline.json`
  per the sloppak spec §5.3 (requires `feat/notation-format` branch or later).
- `routes.py` — FastAPI backend: `POST /api/plugins/musicxml_import/upload`
  and `WS /ws/plugins/musicxml_import/build`.
- `screen.html` / `screen.js` — drag-and-drop import UI with progress reporting.
- `plugin.json` — plugin manifest (`private: true`, nav entry).
- `CONTEXT.md` — pipeline description, limitations, dependency map.
- `LICENSE` — MIT.
- `README.md` — install instructions and compatibility note.

### Known limitations

- First part only — multi-part scores import only part 1.
- Grace notes appear in the notation score but are absent from MIDI audio.
- `grace_slash` field recorded but not yet acted on by any renderer.
- No repeat / da capo / segno expansion.
- No `.mxl` (compressed MusicXML) support.
