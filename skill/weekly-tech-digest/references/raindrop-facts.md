# Raindrop API — Verified Facts (Tests 1–3, Jul 2026)

Every behavior below was verified against Terry's live account. Rely on these; re-verify only if something breaks.

## Auth & query
- Bearer token: `Authorization: Bearer <token>`. Provided per-run in chat; never persisted.
- Week query: `GET https://api.raindrop.io/rest/v1/raindrops/0?search=%23%22YYYY.MM.DD%22&perpage=50&page=N`
  (collection 0 = all; `search=#"tag"` URL-encoded). Match tags by membership — bookmarks carry extra tags.
- Tag = the Sunday starting the week; all of Sun–Sat shares it. No date-range logic.
- Rate limit: 120 req/min. A 36-item week ≈ 18 MB of cache downloads — no batching needed.

## Permanent copies (primary read path)
- `GET /rest/v1/raindrop/{id}/cache` → HTTP 303 to a signed 30-min URL on s3.eu-central-1.wasabisys.com. Use `curl -L` with auth on the first request.
- **Body is gzip-compressed HTML regardless of headers**; `cache.size` is compressed size.
- Snapshots are cleaned article-style captures (author / date / post text / replies), not raw X DOM. `BeautifulSoup.get_text()` yields near-zero boilerplate.
- Reply threads ARE included — they carry corrections and extra links.
- Small snapshots are not stubs (verified down to 58 KB); size is not a quality signal.
- `cache.status: ready` is necessary but NOT sufficient: sanity-check extracted text (length > ~80 chars, no "account suspended" / "unavailable" markers) since Raindrop's crawler can lose the race against deletion.

## Links
- Snapshot anchors hold already-expanded URLs (Raindrop resolves the t.co hop at capture time). t.co resolution is only needed for excerpts/notes: `curl -sI <t.co url>` → `Location` header.
- Second-hop shorteners exist (`osp.fyi`, from the "GitHub Projects Community" account). Not allowlisted → cite as-is, annotate, report to Terry.
- Worst case: a link as plain path text with no anchor (e.g. `Repo: /karpathy/...`). Recovery: prepend `https://github.com` as an inferred candidate; fall back to Terry's note or web search; always label inferred URLs.
- Domains in resource links (huggingface.co etc.) need NOT be allowlisted — the allowlist constrains fetching, not citing.

## Paywalls and friend links (verified 2026.08.31, week 2026.08.16)
- Raindrop's crawler is **server-side and unauthenticated**. Logging into Medium in your own browser does not change what the snapshot contains — member-only stories are always captured as the free preview. Do not expect a login to fix the capture; it can only fix the *recovery* step.
- Paywall markers in the snapshot: `member-only story`, `become a member to access`, `upgrade to access the best of medium`. `fetch_week.py` sets `paywalled` from these. It is independent of `sane`.
- **Authors routinely publish friend links in the article itself** ("Read the article for free here", "Not a Medium member? use this link"). They appear as `...?sk=<hex>` and Raindrop *does* capture them in the snapshot anchors. In week 2026.08.16, 4 of 15 paywalled captures carried one and all 4 redeemed successfully to the full article.
- A friend link **must be redeemed in a real browser session**. Verified: `WebFetch` on a `?sk=` URL still returns the paywalled preview; the same URL in the built-in browser returns the full article and shows "You're reading via <author>'s Friend Link". No login or membership needed.
- Medium serves publications from many hosts (`medium.com`, `<user>.medium.com`, and custom domains like `pub.towardsai.net`, `towardsdeeplearning.com`, `ai.plainenglish.io`). Browser site approvals are per-host, so expect several the first time. `medium.com/<user>/<id>?sk=` often 302s to the publication's own domain, which needs its own approval.
- Cite the canonical article URL in the digest, never the `?sk=` token.

## Extraction
- Raw `soup.get_text()` on a news site (ZDNET especially) is ~90% nav menu; a 3,000-char cap lands entirely inside the boilerplate. This produced several "capture recovered only site navigation" entries in weeks up to 2026.08.09 that were actually fully recoverable.
- `readability-lxml` fixes it: the same ZDNET captures yield 4.6k–11k chars of real article body. It is a required dependency.
- Keep both bodies. readability is right for articles; raw text is right for X captures, where reply threads carry the corrections and readability sometimes trims them.

## Environment
- The container network allowlist governs ALL outbound traffic. Currently needed: api.raindrop.io, s3.eu-central-1.wasabisys.com, t.co (+ pypi for beautifulsoup4).
- Allowlist changes only apply to NEW chats.
- Claude's built-in web fetch cannot pass X.com's login wall — cache-first is not optional.

## Editorial facts from the first full run (2026.07.12)
- ~36 captures/week, all x.com. Duplicate stories from different accounts occur (Kimi Code appeared twice) — merge them.
- Reply threads did real fact-checking (e.g. debunked a "distilled Fable 5" claim) — mine them.
- Founding themes: Coding Agents & CLI Wars · Local LLMs & Inference · Open Source vs Paid SaaS · Memory & Knowledge Systems.
