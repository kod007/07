#!/usr/bin/env python3
import base64
import json
import pathlib
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
staged = sorted(ROOT.glob('02_cevriliyor/*/staging/*.json.zlib.b64'))
for src in staged:
    lang = src.parents[1].name
    name = src.name.removesuffix('.zlib.b64')
    raw = zlib.decompress(base64.b64decode(src.read_text(encoding='ascii')))
    obj = json.loads(raw.decode('utf-8'))
    if not isinstance(obj, list):
        raise SystemExit(f'{src}: root is not array')
    out = ROOT / '02_cevriliyor' / lang / 'output' / name
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.read_bytes() != raw:
        raise SystemExit(f'{out}: conflict')
    out.write_bytes(raw)
    src.unlink()
    print(f'materialized {out.relative_to(ROOT)}')
