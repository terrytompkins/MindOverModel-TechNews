#!/usr/bin/env python3
"""Merge one week's entries into cumulative graph-data.json and regenerate graph.html.

Usage: python3 build_graph.py --week-entries week.json --data graph-data.json \
                              --template ../assets/graph_template.html --out graph.html

week-entries JSON shape (written by Claude after clustering):
{ "week": "YYYY.MM.DD",
  "themes": [{"id":"theme:slug","label":"Display Name"}],   # new AND reused themes
  "tags":   [{"id":"tag:slug","label":"Display Name","aliases":[]}],  # NEW tags only is fine; reused ids are also accepted
  "entries": [{"id":"entry:slug","label":"...","theme":"theme:slug",
               "url": "https://..." or null, "raindrop_ids":["..."],
               "summary":"one line", "quick_hit": false,
               "tags": ["tag:slug", ...]}] }   # 0-4 per entry

Rules enforced here:
- Existing graph-data.json themes and tags are authoritative: matching ids are
  reused and only genuinely new ones are appended. (Claude must read existing
  themes AND the tag vocabulary BEFORE clustering — this script only merges.)
- Entry tag ids must exist in the merged vocabulary — a typo'd tag id fails
  hard rather than silently minting a near-duplicate.
- Max 4 tags per entry; a missing "tags" key is treated as [].
- Theme and tag ids are immutable once minted: never rename, split, or merge
  an id without a migration that rewrites history.
- Re-running the same week replaces that week's entries (idempotent).
- Version-1 data files are migrated in place to version 2 (adds empty "tags"
  vocabulary and "tags": [] on every entry).
"""
import argparse, json, os, sys

def migrate(data):
    if data.get('version', 1) < 2:
        data['version'] = 2
        data.setdefault('tags', [])
        for e in data['entries']:
            e.setdefault('tags', [])
    return data

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week-entries', required=True)
    ap.add_argument('--data', required=True)
    ap.add_argument('--template', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    wk = json.load(open(a.week_entries))
    if os.path.exists(a.data):
        data = migrate(json.load(open(a.data)))
    else:
        data = {'version': 2, 'weeks': [], 'themes': [], 'tags': [], 'entries': []}

    known = {t['id'] for t in data['themes']}
    for t in wk.get('themes', []):
        if t['id'] not in known:
            data['themes'].append(t); known.add(t['id'])

    known_tags = {t['id'] for t in data['tags']}
    for t in wk.get('tags', []):
        if not t['id'].startswith('tag:'):
            sys.exit(f"tag id {t['id']} must start with 'tag:'")
        if t['id'] not in known_tags:
            t.setdefault('aliases', [])
            data['tags'].append(t); known_tags.add(t['id'])

    W = wk['week']
    data['entries'] = [e for e in data['entries'] if e['week'] != W]  # idempotent re-run
    for e in wk['entries']:
        if e['theme'] not in known:
            sys.exit(f"entry {e['id']} references unknown theme {e['theme']}")
        e.setdefault('tags', [])
        if len(e['tags']) > 4:
            sys.exit(f"entry {e['id']} has {len(e['tags'])} tags (max 4)")
        for tg in e['tags']:
            if tg not in known_tags:
                sys.exit(f"entry {e['id']} references unknown tag {tg} "
                         f"(mint it in week-entries \"tags\" or fix the typo)")
        e['week'] = W
        data['entries'].append(e)
    if W not in data['weeks']:
        data['weeks'].append(W); data['weeks'].sort()

    json.dump(data, open(a.data, 'w'), indent=1)
    tpl = open(a.template).read()
    assert '/*__GRAPH_DATA__*/' in tpl, 'template missing data placeholder'
    open(a.out, 'w').write(tpl.replace('/*__GRAPH_DATA__*/', json.dumps(data)))
    print(f'weeks={len(data["weeks"])} themes={len(data["themes"])} '
          f'tags={len(data["tags"])} entries={len(data["entries"])} '
          f'-> {a.data}, {a.out}', file=sys.stderr)

if __name__ == '__main__':
    main()
