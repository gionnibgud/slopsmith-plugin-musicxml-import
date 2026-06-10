"""MusicXML Import plugin — backend routes.

Endpoints:
  POST /api/plugins/musicxml_import/upload
    Receives a MusicXML file as base64. Parses it and returns metadata
    for the UI to display (title, composer, measure count, duration).
    Saves the raw bytes to a temp file for the build step.

  WS   /ws/plugins/musicxml_import/build
    Builds a .sloppak from the uploaded MusicXML file, streaming progress
    messages. Produces notation_keys.json + song_timeline.json in the zip.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import re
import tempfile
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect

_get_dlc_dir = None
_extract_meta = None
_meta_db = None
_config_dir = None
_log = None


def setup(app, context):
    global _get_dlc_dir, _extract_meta, _meta_db, _config_dir, _log
    _get_dlc_dir = context['get_dlc_dir']
    _extract_meta = context['extract_meta']
    _meta_db = context['meta_db']
    _config_dir = context['config_dir']
    _log = context['log']

    @app.post('/api/plugins/musicxml_import/upload')
    async def upload_mxml(data: dict):
        """Receive a MusicXML file as base64, parse metadata, return summary."""
        filename = data.get('filename', '')
        b64 = data.get('data', '')
        if not filename or not b64:
            return {'error': 'No file data'}

        ext = Path(filename).suffix.lower()
        if ext not in ('.xml', '.musicxml'):
            return {'error': f'Unsupported format ({ext}). Only .xml / .musicxml files are supported.'}

        try:
            xml_bytes = base64.b64decode(b64)
        except Exception:
            return {'error': 'Invalid base64 data'}

        # Save to temp for the build step
        tmp_dir = Path(tempfile.mkdtemp())
        tmp_path = tmp_dir / filename
        tmp_path.write_bytes(xml_bytes)

        try:
            mxml = context['load_sibling']('mxml2notation')
            result = mxml.parse_musicxml(xml_bytes)
            return {
                'title': result['title'],
                'composer': result['composer'],
                'duration': result['duration'],
                'part_names': result['part_names'],
                'measure_count': result['measure_count'],
                'tmp_path': str(tmp_path),
            }
        except Exception as e:
            _log.exception('MusicXML parse error')
            return {'error': f'Failed to parse: {e}'}

    @app.websocket('/ws/plugins/musicxml_import/build')
    async def ws_build_mxml(
        websocket: WebSocket,
        tmp_path: str,
        title: str = '',
        composer: str = '',
    ):
        """Build a .sloppak from the uploaded MusicXML, stream progress."""
        await websocket.accept()

        dlc = _get_dlc_dir()
        if not dlc:
            await websocket.send_json({'error': 'DLC folder not configured'})
            await websocket.close()
            return

        if not Path(tmp_path).exists():
            await websocket.send_json({'error': 'File expired — please upload again'})
            await websocket.close()
            return

        progress_queue: asyncio.Queue = asyncio.Queue()

        def _do_build():
            def report(stage: str, pct: int) -> None:
                progress_queue.put_nowait({'stage': stage, 'progress': pct})

            try:
                mxml = context['load_sibling']('mxml2notation')

                report('Parsing MusicXML…', 10)
                xml_bytes = Path(tmp_path).read_bytes()
                result = mxml.parse_musicxml(xml_bytes)

                use_title = title.strip() or result['title']
                use_composer = composer.strip() or result['composer']

                report(
                    f'Parsed {result["measure_count"]} measures'
                    f' — generating MIDI…',
                    25,
                )

                tmp_midi = Path(tempfile.mkdtemp()) / 'score.mid'
                tmp_midi.write_bytes(result['midi_bytes'])

                audio_path = None
                audio_error = None
                try:
                    from gp2midi import render_midi_to_audio
                    report('Rendering audio with FluidSynth…', 40)
                    tmp_ogg_base = str(tmp_midi.parent / 'audio')
                    audio_path = render_midi_to_audio(str(tmp_midi), tmp_ogg_base)
                    report('Audio rendered.', 65)
                except Exception as e:
                    audio_error = str(e)
                    report(f'Audio skipped: {audio_error}', 65)

                report('Assembling sloppak…', 75)
                sloppak_bytes = mxml.build_sloppak_zip(
                    result, audio_path, use_title, use_composer
                )

                safe_t = re.sub(r'[<>:"/\\|?*\s]', '_', use_title)[:60]
                safe_a = re.sub(r'[<>:"/\\|?*\s]', '_', use_composer)[:40]
                out_name = (
                    f'{safe_t}_{safe_a}_mxml.sloppak'
                    if safe_a else f'{safe_t}_mxml.sloppak'
                )

                out_dir = Path(dlc) / 'sloppack'
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / out_name

                report('Writing to DLC folder…', 88)
                out_path.write_bytes(sloppak_bytes)

                try:
                    rel_name = str(Path('sloppack') / out_name)
                    meta = _extract_meta(out_path)
                    stat = out_path.stat()
                    _meta_db.put(rel_name, stat.st_mtime, stat.st_size, meta)
                except Exception:
                    pass  # non-fatal

                msg = {
                    'done': True,
                    'progress': 100,
                    'stage': 'Complete!',
                    'filename': out_name,
                    'measure_count': result['measure_count'],
                    'duration': result['duration'],
                }
                if audio_error:
                    msg['audio_warning'] = audio_error
                progress_queue.put_nowait(msg)

            except Exception as e:
                import traceback
                traceback.print_exc()
                progress_queue.put_nowait({'error': str(e)})

        loop = asyncio.get_event_loop()
        build_task = loop.run_in_executor(None, _do_build)

        try:
            while True:
                try:
                    msg = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                    await websocket.send_json(msg)
                    if msg.get('done') or msg.get('error'):
                        break
                except asyncio.TimeoutError:
                    if build_task.done():
                        break
        except WebSocketDisconnect:
            pass

        await websocket.close()
