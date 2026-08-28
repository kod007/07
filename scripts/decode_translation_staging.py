#!/usr/bin/env python3
import base64
import json
import pathlib
import re
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
pattern = re.compile(r'^(?P<name>.+\.json)\.zlib\.part(?P<part>\d+)\.b64$')
groups = {}
for src in ROOT.glob('02_cevriliyor/*/staging/*.json.zlib.part*.b64'):
    m = pattern.match(src.name)
    if not m:
        continue
    lang = src.parents[1].name
    key = (lang, m.group('name'))
    groups.setdefault(key, []).append((int(m.group('part')), src))

for (lang, name), parts in sorted(groups.items()):
    parts.sort()
    nums = [n for n, _ in parts]
    if nums != list(range(1, len(nums) + 1)):
        raise SystemExit(f'{name}: staging parts are not contiguous: {nums}')
    text = ''.join(''.join(p.read_text(encoding='ascii').split()) for _, p in parts)
    text += '=' * (-len(text) % 4)
    raw = zlib.decompress(base64.b64decode(text, validate=False))
    obj = json.loads(raw.decode('utf-8'))
    if not isinstance(obj, list):
        raise SystemExit(f'{name}: root is not array')
    out = ROOT / '02_cevriliyor' / lang / 'output' / name
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.read_bytes() != raw:
        raise SystemExit(f'{out}: conflict')
    out.write_bytes(raw)
    for _, p in parts:
        p.unlink()
    print(f'materialized {out.relative_to(ROOT)} from {len(parts)} part(s)')
