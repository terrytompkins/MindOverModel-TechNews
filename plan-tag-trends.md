# Plan: Granular topic tags + trends view

Status: draft for Terry's review — nothing implemented yet.
Scope agreed 2026-07-25: controlled-vocabulary tags assigned at digest time, retro-tagging of the three processed weeks (2026.06.28, 2026.07.05, 2026.07.12 — 96 entries), and a v1 trends view in `graph.html` containing theme stacked bars and a tag heatmap. Movers panel and tag co-occurrence network are explicitly deferred.

## 1. Data model (graph-data.json → version 2)

Add a top-level `tags` list — the controlled vocabulary — and a `tags` array on each entry:

```json
{
  "version": 2,
  "weeks": [...],
  "themes": [...],
  "tags": [
    {"id": "tag:mcp", "label": "MCP", "aliases": ["model context protocol"]},
    {"id": "tag:agent-memory", "label": "Agent memory", "aliases": []}
  ],
  "entries": [
    {"id": "entry:kimi-code", "...": "...", "tags": ["tag:coding-cli", "tag:oss-clones"]}
  ]
}
```

Rules:

- Tag ids are kebab-case `tag:slug`, and **immutable once minted**. A label may be reworded; an id is never renamed, split, or merged without a migration that rewrites history. Same rule applies retroactively to theme ids (make this explicit in SKILL.md — it is currently only implied).
- 0–4 tags per entry. Zero is legitimate for thin quick hits; forcing tags on everything degrades counts.
- Themes stay exactly as they are: one per entry, curated, driving the atlas. Tags are the many-to-many granular layer.
- `aliases` exist so future matching can catch phrasing variants without minting duplicates.
- Version bumps 1 → 2. The viewer must tolerate `tags` being absent on old data (defensive `?? []`), so a stale `graph-data.json` never breaks rendering.

## 2. Tagging policy (new section in SKILL.md)

What deserves a tag — one line each in the skill:

- Named technologies, products, protocols: MCP, Obsidian, Claude Code, Ollama, DSPy.
- Named models and model families when the model itself is the story: Kimi, Qwen, Llama.
- Techniques and patterns: RAG, agent memory, quantization, fine-tuning, harness loops, evals.
- Recurring debates and market dynamics: open-weights licensing, pricing wars, benchmark skepticism.

What does not: adjectives, sentiment, one-off details, company names that are merely the author's employer, anything unlikely to ever recur.

Process rules, mirroring the existing theme discipline:

1. **Read the existing `tags` vocabulary before tagging anything.** Match against ids, labels, and aliases first; mint only when nothing fits.
2. Tag during step 3 (clustering), while full article text is in context — never from titles alone.
3. Cap at 4 tags per entry; prefer 2–3.
4. End every run with a **"New tags minted this week"** report in chat so Terry can veto or rename-before-first-publish. This is the vocabulary's editorial gate, parallel to the manual git push.
5. Target vocabulary size ~30–60 tags. If a proposed tag would be the only entry ever likely to carry it, don't mint it. If the vocabulary passes ~80, flag for consolidation review rather than silently continuing.

## 3. Script changes

`scripts/build_graph.py`:

- Accept `tags` (vocabulary additions) and per-entry `tags` in `week-entries.json`, same pattern as themes: existing vocabulary ids are authoritative, new tags appended, entries referencing unknown tag ids fail hard (this is the drift guard — a typo'd tag id must not silently mint a near-duplicate).
- Migrate on load: if `version` is 1, add empty `tags` list and `"tags": []` to entries, set version 2. Keeps idempotent re-runs working across the boundary.

`week-entries.json` shape (documented in the build_graph.py docstring) gains:

```json
{ "tags": [{"id":"tag:slug","label":"...","aliases":[]}],
  "entries": [{ "...": "...", "tags": ["tag:slug"] }] }
```

No changes to `fetch_week.py`.

## 4. Retro-tagging the three processed weeks

Source material: the three digest files (full entry paragraphs) plus `graph-data.json` summaries. No Raindrop re-fetch needed; no token required.

Procedure, one session:

1. Read all 96 entries across the three digests.
2. Draft the **seed vocabulary** from the full set at once — designing tags against three weeks of real data at a time, rather than incrementally, is the whole point of doing this before the backlog ingest.
3. Present the proposed vocabulary to Terry for review **before** applying it (labels, granularity, anything missing).
4. Apply approved tags to all 96 entries, write updated `graph-data.json` (version 2), regenerate `graph.html`.
5. Deliver the new-tags report as the record of the initial mint.

A one-off `scripts/retro_tag.py` is not needed — this is three `week-entries`-shaped patch files run through the (updated) `build_graph.py` merge, which is already idempotent per week. Reuse the machinery; don't build parallel machinery.

## 5. Trends view v1 (graph_template.html)

A mode toggle in the existing controls area: **Atlas | Trends**. Same single file, same `/*__GRAPH_DATA__*/` data, no new artifacts to publish. Trends mode hides the network canvas and shows:

- **Theme stacked bars** — entries per theme per week, with a raw-counts / 100%-share toggle. Share view is the honest one when weekly capture volume varies (28/33/35 so far). Theme colors reuse the existing 4-color cycle so atlas and trends agree.
- **Tag heatmap** — tags × weeks grid, cell shade = count, tags ordered by total frequency, zero-count cells at ground color. Scales to dozens of tags where lines would be spaghetti. Clicking a cell filters the atlas to that tag+week (nice-to-have; ship without if fiddly).

Both render with plain SVG/canvas in the template's existing style — no charting library, keeping the file self-contained and the aesthetic consistent. The week-rail deep link convention (`graph.html#YYYY.MM.DD`) keeps working; add `#trends` as a mode anchor so digests can link straight to the charts.

Deferred to a later phase: movers panel (needs ~6+ weeks to have a trailing average worth comparing against) and tag co-occurrence network (most work; revisit once the vocabulary is stable).

## 6. Sequencing

| Phase | Work | Gate |
|---|---|---|
| 1 | Schema v2 + build_graph.py changes + SKILL.md tagging policy | Terry reviews skill diff |
| 2 | Retro-tag: seed vocabulary from 96 entries | Terry approves vocabulary before it's applied |
| 3 | Apply tags, regenerate data + graph; build trends view | Terry reviews rendered graph.html locally |
| 4 | Ingest backlog weeks with tagging live | Normal per-run new-tags report |

Phases 1–3 fit in one working session. Phase 4 is the existing digest workflow, unchanged except tags ride along. Ordering matters: vocabulary must exist before backlog ingest, or early backlog weeks get tagged against an immature vocabulary and drift from day one.

## 7. Risks and mitigations

- **Tag drift across runs** — the core risk. Mitigated by: read-before-mint rule, aliases, hard failure on unknown ids in the merge, per-run mint report, immutable ids.
- **Vocabulary bloat** — soft cap with consolidation trigger at ~80 (§2.5).
- **Retro-tag quality** — digest paragraphs are condensed; a few entries may under-tag versus what full article text would support. Acceptable: digests preserve the substance, and the honesty policy already tolerates "less than perfect, plainly labeled."
- **Template growth** — trends adds code to a 192-line template. Keep trends JS in a clearly-fenced section; if the file passes ~500 lines, consider splitting the template into sections concatenated at build time (not needed yet).

## 8. Out of scope (recorded for later)

Movers panel; tag co-occurrence network; entity extraction across themes; quick-hit-ratio and buzz-index charts; link-domain mix over time. All become cheap once `tags` exists and the trends view has a home.
