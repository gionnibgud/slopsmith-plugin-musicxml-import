# slopsmith-plugin-musicxml-import

Slopsmith plugin. Imports MusicXML (`.xml` / `.musicxml`) scores and produces
a `.sloppak` using the **notation format** — ready for playback and staff
rendering via the `staffview` plugin.

## Compatibility

Requires Slopsmith with the notation format support:
**`feat/notation-format` branch or any release that includes it.**

The sloppak produced by this plugin uses `notation_keys.json` and
`song_timeline.json` per sloppak-spec §5.3. It will not load on older
Slopsmith builds that predate the notation format.

## What gets imported

- Pitch, duration, dots, rests, ties
- Grace notes (slashed and unslashed distinguished via `grace_slash` field)
- Key signature, time signature, tempo changes
- Dynamics (direction-level and note-level)
- Articulations: staccato, tenuto, accent, strong accent
- Slurs, hairpins (crescendo / diminuendo)
- Hammer-on, pull-off, harmonics (natural/artificial), fingering
- Ornaments: trill mark (as text annotation), vibrato (wavy-line)
- Fermata (as text annotation)
- Accidental overrides (force natural, flat, sharp, double-flat, double-sharp)
- Rehearsal marks → sections

## Limitations

- **First part only** — multi-part scores (e.g. piano + violin) import only
  part 1.
- **score-partwise only** — `score-timewise` MusicXML not supported.
- **No repeats** — da capo, segno, repeat barlines are not expanded.
- **Grace notes in audio** — appear in the notation score but not in the
  FluidSynth MIDI audio; principal note timing is unaffected.
- **No .mxl** — compressed MusicXML not supported; unzip before importing.

## Installation

### Development (slopsmith-src + OrbStack/Docker)

Copy this directory into the `plugins/` folder of your slopsmith-src checkout
and name it `musicxml_import`:

```
slopsmith-src/plugins/musicxml_import/
```

The bind-mount in `docker-compose.yml` picks it up immediately — no rebuild
needed.

### Slopsmith Desktop

Copy into the user plugin folder:

```
<slopsmith-desktop-data>/plugins/musicxml_import/
```

## Dependencies

All available in the slopsmith-src container environment:

| Dependency | Purpose |
|---|---|
| `midiutil` | MIDI file generation |
| `pyyaml` | Manifest serialisation |
| FluidSynth + GeneralUser-GS.sf2 | Piano audio rendering (via `gp2midi`) |

No third-party XML library required — uses stdlib `xml.etree.ElementTree`.

## License

MIT — see `LICENSE`.
