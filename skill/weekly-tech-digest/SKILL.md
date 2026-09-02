---
name: weekly-tech-digest
description: Turn one week of Terry's Raindrop.io captures (tagged YYYY.MM.DD) into a polished tech-news digest markdown file plus a cumulative interactive knowledge graph. Use this skill whenever Terry asks to run the weekly digest, build the weekly tech news post, process a week's Raindrop bookmarks/captures, update the knowledge graph, or mentions a week tag like 2026.07.12 in the context of the digest pipeline — even if they just say "run this week" or "do the digest".
---

# Weekly Tech Digest

Transforms one week's Raindrop.io captures into two artifacts:
1. `digest-YYYY.MM.DD.md` — a curated, self-contained digest post (GitHub-flavored markdown, embedded Mermaid mindmap). New file each week.
2. `graph.html` + `graph-data.json` — ONE cumulative interactive knowledge graph across all weeks. The JSON is the durable source of truth; the HTML is regenerated from it every run.

## Inputs per run

- **Raindrop API token**: Terry pastes it into chat at run start. Never store it in any file that persists.
- **Week tag**: `YYYY.MM.DD`, the Sunday starting the week. One shared tag per week — filter on tag membership, no date-range logic.
- **Browser**: needed at step 2b to recover paywalled articles. The built-in browser (`Claude_Browser__*`) is preferred — it has a persistent profile, so a Medium login done once survives every later run on that computer. Claude in Chrome works too. Neither is required for the run to complete; without one, paywalled entries are simply labeled.
- **Prior state**: the current `graph-data.json`. Fetch it directly from the repo (verified working from the container):
  `curl -s https://raw.githubusercontent.com/terrytompkins/MindOverModel-TechNews/main/graph-data.json`
  If Terry uploaded a copy in this conversation, prefer the uploaded one (it may be newer than the last push). If the repo fetch fails AND nothing was uploaded, ask Terry — do not initialize a fresh graph without explicit confirmation, since that would silently discard the cumulative archive.

## Workflow

### 1. Fetch and extract

```bash
pip install beautifulsoup4 readability-lxml lxml_html_clean --break-system-packages
python3 scripts/fetch_week.py --token TOKEN --tag YYYY.MM.DD --outdir run
```

This queries the week's bookmarks, downloads every `ready` permanent copy (gzip → text), harvests resource links, runs the content sanity check, and writes `run/corpus.json`. See `references/raindrop-facts.md` for every verified API behavior the script relies on — read it if anything fails or looks unfamiliar.

Each entry carries two bodies, and you need both:

- **`article_text`** (readability-extracted, ≤12k chars) — use this for articles. Raw page text on a news site is ~90% nav boilerplate, and the old 3k cap landed before the article even started; that is what produced "the capture recovered only site navigation" entries in past weeks. `readability-lxml` is therefore a hard dependency, not an optional one — if the script warns it is missing, install it and re-run before reading anything.
- **`text`** (raw page text, ≤8k chars) — use this for X captures, where the reply threads are the value and readability sometimes trims them.

Read whichever is richer per entry; for X posts that is usually `text`, for articles almost always `article_text`.

The script also sets **`paywalled`** (the snapshot is real but truncated at a free preview) and **`friend_links`** (author-published `?sk=` bypass links found in the snapshot). `paywalled` is independent of `sane`: a paywalled capture is genuine, just cut short. Both drive step 2b.

### 2. Read and verify the corpus

Read `run/corpus.json` in full. For each entry, confirm the pipeline's judgment rather than trusting it blindly:

- Entries flagged not-sane get the fallback chain: Terry's `note` → `excerpt` + resolved t.co links → targeted web search → honest labeling. Never fabricate a summary from a title alone.
- `inferred_links` are github.com URL guesses built from path-like text (`/user/repo`) in posts with no anchors. Treat as candidates; label "(URL inferred from capture)" in the digest.
- **Detect duplicate stories**: different accounts often post the same tool/news in the same week. Merge them into one entry citing all raindrop ids; a same-week duplicate is itself signal worth one line ("hit the feed from multiple accounts").
- **Mine the replies**: snapshots include reply threads, which frequently contain corrections, debunkings, caveats, and extra links. Reflect substantive corrections in the entry — hype-plus-correction is often the real story.

### 2b. Recover paywalled articles before writing about them

`fetch_week.py` prints a `PAYWALLED` list splitting into two groups. Work it before drafting — a paywalled entry summarized from its preview is the single most common source of a thin, hedge-heavy digest entry.

**Group 1 — has a `friend_links` entry.** The author deliberately published a share link ("read this for free here") and it is the sanctioned way in. **Always redeem these.** A friend link only works in a real browser session — a server-side fetch (`WebFetch`, `curl`) still hits the paywall, so this step needs a browser:

1. `Claude_Browser__preview_start` with the friend-link URL (call `Claude_Browser__request_access` for the host first if asked — Medium articles are served from many hosts: `medium.com`, `*.medium.com`, and custom publication domains like `pub.towardsai.net`, so expect several approvals the first time).
2. `Claude_Browser__get_page_text` to read the body. Confirm it worked: the page opens with "You're reading via <author>'s Friend Link". Set `max_chars` generously (~20000) — a 10-minute article overruns the default and you will silently lose the conclusion, which is usually the part worth quoting.
3. Write the entry from that text, and cite the **canonical** article URL, not the `?sk=` link — friend links are personal share tokens and do not belong in a published digest.

**Group 2 — no friend link.** Try the browser anyway: if Terry is signed into Medium in the built-in browser's persistent profile, member-only stories open normally. If that fails, keep the preview-based summary and label it honestly — say what was recovered and where it stopped, per the entry's paywall note convention.

**Do not** route around a paywall with archive mirrors, cache viewers, or paywall-stripping services. Friend links and a real login are the two sanctioned paths; if neither is available, an honest label is the answer.

**Then re-check your own labels.** Trust `paywalled` over your impression: if the flag is False, do not write "member-only story" — a short body there means your extraction truncated it, so re-read the full `article_text` before concluding anything was cut off. If the flag is True, the entry must carry a paywall note. Getting this backwards mislabels the source in a published post.

### 3. Cluster into themes and assign topic tags — READ EXISTING THEMES AND TAGS FIRST

Open the current `graph-data.json` and read its `themes` list AND its `tags` vocabulary **before** clustering. Match this week's content to existing themes wherever a reasonable fit exists — but don't force a fit just to avoid minting. Mint a new theme when a recurring subject keeps landing in an existing theme only because of a surface-level resemblance (e.g. "it's open source" or "it's a listicle") rather than real topical kinship with that theme's other entries. Avoid near-duplicate themes ("Coding Agents" vs "Agentic Coding") — check the existing list for a genuine synonym before minting — but do not let that caution collapse into never minting at all. The theme list is a curated taxonomy, not a fixed one; it should grow deliberately, not slowly for its own sake.

**Theme-balance check, every run:** after assigning this week's entries, glance at how entries are distributed across all themes in `graph-data.json` (a quick count per `theme` id). If one theme is holding a disproportionate share of all entries (as a rule of thumb, notably more than the others combined, or over ~35% of the cumulative total), that is itself a signal it's become a catch-all hiding distinct sub-clusters — call this out to Terry with the likely sub-clusters (e.g. by cross-tabbing that theme's entries against their topic tags) rather than silently continuing to feed it. Splitting an overloaded theme, minting a new one, or reclassifying past entries into a better-fitting existing theme is a deliberate migration — propose it and get Terry's go-ahead before rewriting historical entries' `theme` field, but do propose it; this is a standing, expected part of the taxonomy's upkeep, not a rare exception.

Sort entries: substantial (has a resource link OR ≥ ~400 chars of real post text) vs **Quick Hits** (thin, link-only, or announcement-only items — one or two lines each).

**Topic tags** (distinct from the Raindrop week tag): each entry also gets 0–4 granular topic tags from the controlled vocabulary in `graph-data.json` → `tags`. Themes are single and curated; topic tags are many-to-many and power trend tracking, so vocabulary consistency matters more than coverage.

- Assign tags now, while full article text is in context — never from titles alone. Prefer 2–3 per entry; 0 is fine for thin quick hits. Never exceed 4.
- Match against existing ids, labels, AND `aliases` first. Mint a new tag only when nothing fits, id form `tag:kebab-slug`.
- Tag-worthy: named technologies/products/protocols (MCP, Obsidian, Claude Code, Ollama); models or model families when the model is the story (Qwen, Kimi, Llama); techniques and patterns (RAG, agent memory, quantization, evals); recurring debates and market dynamics (open-weights licensing, pricing wars, benchmark skepticism).
- Not tag-worthy: adjectives, sentiment, one-off details, an author's employer, anything unlikely to recur. If a tag would probably only ever apply to this one entry, don't mint it.
- Target vocabulary size is ~30–60. If it passes ~80, tell Terry it needs a consolidation review instead of silently continuing.

### 4. Write the digest

Structure, in order:
- Title: `# Weekly Tech Digest — Week of YYYY.MM.DD`, then a one-line stats/date bar linking to `./graph.html#YYYY.MM.DD`.
- **"This week's through-lines"**: an editorial intro naming the 2–4 currents connecting the week. This is the value-add — write it after reading everything, not before.
- **Mermaid mindmap** in a ```` ```mermaid ```` fence (renders natively on GitHub): root = week, branches = themes, leaves = short entry labels. **Follow this convention exactly — verified rendering on GitHub 2026-07-22:**
  - Root: `root((Week of YYYY.MM.DD))` on a single line — nothing else in it, no HTML tags.
  - Every other line (themes and leaves): plain **unquoted** text using only letters, digits, spaces, hyphens, dots, and plus signs. Write `and`, never `&`. No quotes, HTML tags, colons, parentheses, brackets, or hash marks.
  - **Do NOT quote labels.** Mindmap grammar (unlike flowcharts) treats the whole line as the label, so quote marks render as literal visible characters on GitHub. This was tested both ways; quoting bought no compatibility (renderers lacking mindmap support fail on the diagram type itself, not the syntax) and disfigured the output.
  - Spaces for indentation, never tabs.
  - Lint before delivering: every non-root line must match `^[A-Za-z0-9 .+-]+$` after stripping indentation.
- **Theme sections**, each entry as: `### Name — hook`, then a paragraph giving the genuine gist (a reader should get the story without clicking through), an italicized *Why it matters* sentence, and a `**Resources:**` line with real outbound links. Annotate honestly: "(second-hop shortener; final destination not verified)", "(no link captured in post)", "(URL inferred from capture)".
- **Quick hits**: bulleted one-liners with links.
- Footer noting capture count, tag, and the honesty policy.

The digest must be self-contained and render well on GitHub, Obsidian, and common blog platforms. No fabricated content, ever — captured text and Terry's notes are the only sources for claims about a post.

### 5. Update the cumulative graph

Write `run/week-entries.json` (shape documented at the top of `scripts/build_graph.py`): the week's themes (reused ids + any new), any newly minted topic tags (id, label, aliases), and one record per digest entry — short label, theme id, best single URL (or null), raindrop ids, one-line summary, `quick_hit` flag, and its topic tag ids. Then:

```bash
python3 scripts/build_graph.py --week-entries run/week-entries.json \
    --data graph-data.json --template assets/graph_template.html --out graph.html
```

Entry ids must be **unique across the whole archive**, not just within the week — the viewer builds one node set from every week, so a repeated id breaks the graph at load time. Before minting an entry id, check `graph-data.json` for it; when a subject genuinely re-appears in a later week (a tool captured again, a project with fresh news), that is a separate entry and gets the week as a suffix — `entry:some-tool-2026-08-23`. The build script fails hard on a collision.

The merge is idempotent per week (safe to re-run) and appends the week to the viewer's week rail. The script fails hard on unknown theme or tag ids — that's the drift guard, not an inconvenience; fix the typo or mint the tag properly, never work around it. Never edit `graph.html` directly; change the template or the data.

### 6. Deliver

**If running in Cowork with the MindOverModel-TechNews repo clone connected as the working folder:** write `digest-YYYY.MM.DD.md`, the updated `graph-data.json`, and the regenerated `graph.html` directly into the repo folder (root level, matching the existing layout), and add the new week's row to the README's "All digests" table (digest link + graph deep link, newest first). Do NOT run git commands; tell Terry the files are in place and ready for review, commit, and push — the manual push is the editorial review gate before publishing.

**If running in Chat (no folder access):** present the three files as downloads and remind Terry to copy them into the clone, add the README table row, commit, and push.

In both cases, remind Terry that `graph-data.json` is the cumulative archive and must reach the repo — it is the state the next run fetches.

**New-tags-and-themes report**: end every run by listing in chat any topic tags minted this week (id + label + which entries carry them) AND any new themes minted (id + label + rough entry count + why an existing theme didn't fit), so Terry can veto or reword before pushing. If none were minted, say so — a zero-mint week is not itself a problem, but if it's been many consecutive weeks with no new theme while one theme keeps growing disproportionately, flag that explicitly rather than staying quiet about it.

## Standing rules

- **Ids are immutable**: theme and topic-tag ids, once minted, are never renamed, split, or merged in place — the trend history keys on them. Labels may be reworded; an id change requires an explicit migration that rewrites every entry referencing it, done deliberately with Terry, never as a side effect of a weekly run.
- **Reclassifying entries between existing themes, or splitting a theme into two, is welcome and expected as the corpus grows** — unlike an id rename, this only changes which theme id an entry points to, not the ids themselves. Still propose it and get Terry's go-ahead before rewriting historical entries in bulk, since it changes past weeks' data, not just this week's.
- **Honesty over completeness**: label unreadable or partially-recovered entries plainly. An honest "(no link captured)" beats a plausible guess presented as fact.
- **Second-hop shorteners** (`osp.fyi` is the known recurring one): cite as-is with an annotation, and tell Terry which new shortener domains appeared so they can be added to the network allowlist (changes require a new chat).
- **A paywall is a recoverable problem, not a labeling problem.** Redeem every `friend_links` entry via the browser before writing (step 2b). Label only what genuinely could not be recovered, and never cite the `?sk=` link itself.
- **Suspension losses are acceptable**: if a capture's snapshot is a suspension/unavailable page, say so in the digest entry and move on.
- **Token hygiene**: the token lives only in the chat and in the ephemeral run command. Never write it into corpus.json, the digest, project knowledge, or this skill.
