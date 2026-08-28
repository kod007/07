#!/usr/bin/env python3
import hashlib
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
requests = sorted(ROOT.glob('02_cevriliyor/*/finalize/*.request.json'))
for req_path in requests:
    req = json.loads(req_path.read_text(encoding='utf-8'))
    lang = req['target_lang']
    batch = req['batch']
    agent = req['agent_id']
    post_ids = req['post_ids']
    expected_sha = req['output_blob_sha']

    output = ROOT / '02_cevriliyor' / lang / 'output' / batch
    source = ROOT / '02_cevriliyor' / lang / 'source' / batch
    claim = ROOT / '02_cevriliyor' / lang / 'claims' / f'{batch.removesuffix(".json")}.claim.json'
    final = ROOT / '03_cevrilen' / lang / batch
    qa = ROOT / '04_qa' / lang / f'{batch.removesuffix(".json")}.qa.json'
    completed = ROOT / '07_log' / lang / 'completed' / batch

    raw = output.read_bytes()
    actual_sha = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
    if actual_sha != expected_sha:
        raise SystemExit(f'{batch}: output SHA mismatch {actual_sha} != {expected_sha}')
    obj = json.loads(raw.decode('utf-8'))
    if not isinstance(obj, list) or [x.get('post_id') for x in obj] != post_ids:
        raise SystemExit(f'{batch}: post_id mismatch')
    for x in obj:
        if set(x) != {'post_id','slug_id','translations'} or set(x['translations']) != {lang}:
            raise SystemExit(f'{batch}: schema mismatch')
        tr = x['translations'][lang]
        if set(tr) != {'name','description','slug','content'} or any(not tr[k] for k in tr):
            raise SystemExit(f'{batch}: translation fields invalid')
        if len(tr['description']) > 800:
            raise SystemExit(f'{batch}: description exceeds 800 chars')

    final.parent.mkdir(parents=True, exist_ok=True)
    if final.exists() and final.read_bytes() != raw:
        raise SystemExit(f'{batch}: final conflict')
    shutil.copyfile(output, final)

    qa.parent.mkdir(parents=True, exist_ok=True)
    qa.write_text(json.dumps({
        'batch': batch,
        'target_lang': lang,
        'agent_id': agent,
        'post_ids': post_ids,
        'status': 'PASS',
        'checks': req['checks'],
        'output_blob_sha': actual_sha
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    completed.parent.mkdir(parents=True, exist_ok=True)
    completed.write_text(json.dumps({
        'batch': batch,
        'target_lang': lang,
        'agent_id': agent,
        'post_ids': post_ids,
        'status': 'completed',
        'qa': 'PASS',
        'output_blob_sha': actual_sha
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    for p in (source, output, claim, req_path):
        if p.exists():
            p.unlink()
    print(f'finalized {lang}/{batch}')
