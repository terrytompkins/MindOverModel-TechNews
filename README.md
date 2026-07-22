# MindOverModel — Tech News

A weekly, curated digest of technology news — primarily AI, developer tooling, and open source — distilled from a week of captured posts and articles. Each digest is a self-contained read: every entry summarizes its source well enough to get the story without clicking through, and surfaces the valuable outbound links (repos, papers, demos) explicitly.

Alongside the weekly posts, a single **cumulative knowledge graph** grows week over week, mapping every entry to its theme across the whole archive.

## Latest digest

**[Week of 2026.07.12](./digest-2026.07.12.md)** — the coding-agent CLI wars boil over, local inference eats the frontier's lunch from below, and open source claims another round of paid-SaaS casualties.

## The knowledge graph

**[Open the interactive atlas](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html)** *(requires GitHub Pages — see below)*

Filter by theme, filter by week on the rail along the bottom, search entries, and click any node for a summary and source link. Deep links like `graph.html#2026.07.12` pre-select a single week. The graph is regenerated from [`graph-data.json`](./graph-data.json) every week — that JSON is the archive's source of truth.

## All digests

| Week | Digest | Graph slice |
|---|---|---|
| 2026.07.12 | [digest-2026.07.12.md](./digest-2026.07.12.md) | [view](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html#2026.07.12) |

## How it's made

Posts are captured to [Raindrop.io](https://raindrop.io) throughout the week and tagged with the week's date. A Claude skill (source in [`skill/weekly-tech-digest/`](./skill/weekly-tech-digest/)) reads each capture's permanent-copy snapshot, extracts the full text and outbound links, clusters entries into a slowly-growing theme taxonomy, writes the digest, and merges the week into the cumulative graph.

**Honesty policy:** summaries are drawn only from captured content and curator notes — never fabricated. Entries whose sources or links couldn't be fully recovered say so plainly: *(no link captured)*, *(URL inferred from capture)*, *(second-hop shortener; final destination not verified)*.

## Repository layout

```
digest-YYYY.MM.DD.md         one per week — the shareable posts
graph.html                   the cumulative interactive atlas (regenerated weekly)
graph-data.json              cumulative graph state — the file that must never be lost
skill/weekly-tech-digest/    the pipeline: SKILL.md, scripts, graph template, API notes
```

## One-time setup: enable GitHub Pages

The digest markdown renders directly on github.com (including the Mermaid mindmaps), but `graph.html` needs Pages to be viewable:

1. Repo **Settings → Pages**
2. Source: **Deploy from a branch** · Branch: **main** · Folder: **/ (root)** · Save
3. After ~1 minute the site is live at `https://terrytompkins.github.io/MindOverModel-TechNews/`
4. Replace `terrytompkins` throughout this README with your GitHub username

---

*Curated by Terry Tompkins. Digest and graph generated with Claude.*
