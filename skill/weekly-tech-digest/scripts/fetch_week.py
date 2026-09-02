#!/usr/bin/env python3
"""Fetch one week's Raindrop captures and build corpus.json for digest writing.

Usage: python3 fetch_week.py --token TOKEN --tag YYYY.MM.DD --outdir DIR
Requires: beautifulsoup4 (pip install beautifulsoup4 --break-system-packages)
"""
import argparse, json, subprocess, os, gzip, re, sys, urllib.parse

SUSPECT = ['account suspended', 'this post is unavailable',
           "page doesn\u2019t exist", "page doesn't exist", 'something went wrong']

# Markers that a snapshot captured only the free preview of a gated article.
PAYWALL = ['member-only story', 'become a member to access',
           'upgrade to access the best of medium', 'this story is free to read',
           'read the full story', 'members-only']

# Author-supplied share links that bypass the paywall for anyone.
# Medium/Substack style: ...?sk=<hex token>.  These are deliberately published
# by the author ("read this for free here") and are the sanctioned way in.
FRIEND_RE = re.compile(r'https?://[^\s"\'<>]+[?&]sk=[0-9a-fA-F]{8,}[^\s"\'<>]*')

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
    try:
        from readability import Document
    except ImportError:
        Document = None
        print('WARN: readability-lxml missing -> article_text will be empty and '
              'news-site captures will be mostly nav boilerplate. '
              'pip install readability-lxml lxml_html_clean --break-system-packages',
              file=sys.stderr)
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
            entry['text'] = text[:8000]
            # Raw get_text() on a news site is ~90% nav boilerplate and the cap
            # lands before the article starts. readability isolates the article
            # body; keep BOTH, since raw text preserves X reply threads verbatim.
            entry['article_text'] = ''
            if Document is not None:
                try:
                    art = BeautifulSoup(Document(html).summary(), 'html.parser')
                    for t in art(['script', 'style', 'noscript']): t.decompose()
                    entry['article_text'] = re.sub(
                        r'\n{3,}', '\n\n', art.get_text('\n', strip=True))[:12000]
                    entry['article_links'] = list(dict.fromkeys(
                        x['href'] for x in art.find_all('a', href=True)
                        if x['href'].startswith('http')))[:20]
                except Exception as ex:
                    entry['article_text_error'] = str(ex)[:200]
            # 3. Paywall detection + author friend links (see step 2b in SKILL.md).
            #    'sane' means the snapshot is real; 'paywalled' means it is real
            #    but TRUNCATED at the free preview. The two are independent.
            entry['paywalled'] = any(m in lower for m in PAYWALL)
            fl, fseen = [], set()
            for cand in FRIEND_RE.findall(html) + [h for h in hrefs if FRIEND_RE.match(h)]:
                cand = cand.rstrip('\\"\'&')
                if cand not in fseen:
                    fseen.add(cand); fl.append(cand)
            if fl: entry['friend_links'] = fl[:3]
            # 4. Path-like tokens with no href -> inferred github candidates
            if not hrefs:
                paths = re.findall(r'(?<!\S)(/[\w.-]+/[\w./-]+)', text)
                entry['inferred_links'] = [f'https://github.com{p}' for p in paths[:3]]
        else:
            entry['sane'] = False
            entry['paywalled'] = False
            entry['text'] = ''
            entry['article_text'] = ''
            entry['hrefs'] = []
        # 5. t.co in excerpt/note -> resolve via HEAD (secondary path)
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
    walled = [c['id'] for c in corpus if c.get('paywalled')]
    withfl = [c['id'] for c in corpus if c.get('friend_links')]
    print(f'wrote {out} | sane {len(corpus)-len(flagged)}/{len(corpus)}'
          + (f' | FLAGGED for fallback chain: {flagged}' if flagged else ''), file=sys.stderr)
    thin = [c['id'] for c in corpus
            if c['sane'] and not c.get('paywalled')
            and max(len(c.get('article_text') or ''), len(c.get('text') or '')) < 400]
    if thin:
        print(f'THIN BODY (<400 chars, likely quick hits or lost captures): {thin}', file=sys.stderr)
    if walled:
        print(f'PAYWALLED (free preview only) {len(walled)}: {walled}', file=sys.stderr)
        print(f'  -> of those, {len(withfl)} carry an author friend link and MUST be '
              f'recovered via the browser (SKILL.md step 2b): {withfl}', file=sys.stderr)
        rest = [i for i in walled if i not in withfl]
        if rest:
            print(f'  -> {len(rest)} have no friend link; recover via a logged-in '
                  f'browser if available, else label the paywall honestly: {rest}', file=sys.stderr)

if __name__ == '__main__':
    main()
