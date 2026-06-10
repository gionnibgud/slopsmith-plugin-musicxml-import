# Changelog

All notable changes to `slopsmith-plugin-musicxml-import` are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

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

### Known limitations (v0.1.0)

- First part only — multi-part scores import only part 1.
- Grace notes appear in the notation score but are absent from MIDI audio.
- `grace_slash` field recorded but not yet acted on by any renderer.
- No repeat / da capo / segno expansion.
- No `.mxl` (compressed MusicXML) support.
- Compound meter beat emission uses quarter-note resolution only.
