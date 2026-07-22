#!/usr/bin/env python3
"""Fetch one week's Raindrop captures and build corpus.json for digest writing.

Usage: python3 fetch_week.py --token TOKEN --tag YYYY.MM.DD --outdir DIR
Requires: beautifulsoup4 (pip install beautifulsoup4 --break-system-packages)
"""
import argparse, json, subprocess, os, gzip, re, sys, urllib.parse

SUSPECT = ['account suspended', 'this post is unavailable',
           "page doesn\u2019t exist", "page doesn't exist", 'something went wrong']

def curl(args):
    r = subprocess.run(['curl', '-s'] + args, capture_output=True)
    return r.stdout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--token', required=True)
    ap.add_argument('--tag', required=True)
    ap.add_argument('--outdir', default='run')
    a = ap.parse_args()
    os.makedirs(f'{a.outdir}/caches', exist_ok=True)
    auth = f'Authorization: Bearer {a.token}'

    # 1. Query by tag membership (search=#"tag"), paginating past 50 if needed
    items, page = [], 0
    while True:
        q = urllib.parse.quote(f'#"{a.tag}"')
        raw = curl(['-H', auth,
            f'https://api.raindrop.io/rest/v1/raindrops/0?search={q}&perpage=50&page={page}'])
        d = json.loads(raw)
        items += d.get('items', [])
        if len(items) >= d.get('count', 0) or not d.get('items'): break
        page += 1
    print(f'{len(items)} bookmarks for tag {a.tag}', file=sys.stderr)

    from bs4 import BeautifulSoup
    corpus = []
    for it in items:
        id = str(it['_id'])
        dest = f'{a.outdir}/caches/cache_{id}.html'
        entry = {'id': id, 'title': (it.get('title') or '')[:100],
                 'link': it.get('link', ''), 'created': it.get('created', '')[:10],
                 'note': it.get('note', ''), 'excerpt': it.get('excerpt', ''),
                 'cache_status': it.get('cache', {}).get('status')}
        # 2. Download permanent copy (303 -> signed URL; body is gzip)
        if entry['cache_status'] == 'ready':
            if not os.path.exists(dest):
                open(dest, 'wb').write(curl(['-L', '-H', auth,
                    f'https://api.raindrop.io/rest/v1/raindrop/{id}/cache']))
            try:
                html = gzip.open(dest, 'rt', encoding='utf-8', errors='replace').read()
            except (gzip.BadGzipFile, OSError):
                html = open(dest, encoding='utf-8', errors='replace').read()
            soup = BeautifulSoup(html, 'html.parser')
            for t in soup(['script', 'style', 'noscript']): t.decompose()
            text = re.sub(r'\n{3,}', '\n\n', soup.get_text('\n', strip=True))
            hrefs, seen = [], set()
            for aa in soup.find_all('a', href=True):
                h = aa['href']
                if h.startswith('http') and 'x.com' not in h and 'twitter.com' not in h and h not in seen:
                    seen.add(h); hrefs.append(h)
            lower = text.lower()
            entry['sane'] = len(text) > 80 and not any(m in lower for m in SUSPECT)
            entry['hrefs'] = hrefs
            entry['text'] = text[:3000]
            # 3. Path-like tokens with no href -> inferred github candidates
            if not hrefs:
                paths = re.findall(r'(?<!\S)(/[\w.-]+/[\w./-]+)', text)
                entry['inferred_links'] = [f'https://github.com{p}' for p in paths[:3]]
        else:
            entry['sane'] = False
            entry['text'] = ''
            entry['hrefs'] = []
        # 4. t.co in excerpt/note -> resolve via HEAD (secondary path)
        tco = re.findall(r'https?://t\.co/\w+', entry['excerpt'] + ' ' + entry['note'])
        resolved = {}
        for u in tco:
            head = subprocess.run(['curl', '-sI', u], capture_output=True, text=True).stdout
            m = re.search(r'(?im)^location:\s*(\S+)', head)
            if m: resolved[u] = m.group(1)
        if resolved: entry['tco_resolved'] = resolved
        corpus.append(entry)

    out = f'{a.outdir}/corpus.json'
    json.dump(corpus, open(out, 'w'), indent=1)
    flagged = [c['id'] for c in corpus if not c['sane']]
    print(f'wrote {out} | sane {len(corpus)-len(flagged)}/{len(corpus)}'
          + (f' | FLAGGED for fallback chain: {flagged}' if flagged else ''), file=sys.stderr)

if __name__ == '__main__':
    main()
