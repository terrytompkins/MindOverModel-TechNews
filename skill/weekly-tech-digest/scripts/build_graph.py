#!/usr/bin/env python3
"""Merge one week's entries into cumulative graph-data.json and regenerate graph.html.

Usage: python3 build_graph.py --week-entries week.json --data graph-data.json \
                              --template ../assets/graph_template.html --out graph.html

week-entries JSON shape (written by Claude after clustering):
{ "week": "YYYY.MM.DD",
  "themes": [{"id":"theme:slug","label":"Display Name"}],   # new AND reused themes
  "entries": [{"id":"entry:slug","label":"...","theme":"theme:slug",
               "url": "https://..." or null, "raindrop_ids":["..."],
               "summary":"one line", "quick_hit": false}] }

Rules enforced here:
- Existing graph-data.json themes are authoritative: matching ids are reused and
  only genuinely new themes are appended. (Claude must read existing themes
  BEFORE clustering — this script only merges.)
- Re-running the same week replaces that week's entries (idempotent).
"""
import argparse, json, os, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week-entries', required=True)
    ap.add_argument('--data', required=True)
    ap.add_argument('--template', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    wk = json.load(open(a.week_entries))
    if os.path.exists(a.data):
        data = json.load(open(a.data))
    else:
        data = {'version': 1, 'weeks': [], 'themes': [], 'entries': []}

    known = {t['id'] for t in data['themes']}
    for t in wk.get('themes', []):
        if t['id'] not in known:
            data['themes'].append(t); known.add(t['id'])

    W = wk['week']
    data['entries'] = [e for e in data['entries'] if e['week'] != W]  # idempotent re-run
    for e in wk['entries']:
        if e['theme'] not in known:
            sys.exit(f"entry {e['id']} references unknown theme {e['theme']}")
        e['week'] = W
        data['entries'].append(e)
    if W not in data['weeks']:
        data['weeks'].append(W); data['weeks'].sort()

    json.dump(data, open(a.data, 'w'), indent=1)
    tpl = open(a.template).read()
    assert '/*__GRAPH_DATA__*/' in tpl, 'template missing data placeholder'
    open(a.out, 'w').write(tpl.replace('/*__GRAPH_DATA__*/', json.dumps(data)))
    print(f'weeks={len(data["weeks"])} themes={len(data["themes"])} '
          f'entries={len(data["entries"])} -> {a.data}, {a.out}', file=sys.stderr)

if __name__ == '__main__':
    main()
