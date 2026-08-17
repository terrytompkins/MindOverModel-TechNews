# MindOverModel — Tech News

A weekly, curated digest of technology news — primarily AI, developer tooling, and open source — distilled from a week of captured posts and articles. Each digest is a self-contained read: every entry summarizes its source well enough to get the story without clicking through, and surfaces the valuable outbound links (repos, papers, demos) explicitly.

Alongside the weekly posts, a single **cumulative knowledge graph** grows week over week, mapping every entry to its theme across the whole archive.

## Latest digest

**[Week of 2026.08.02](./digest-2026.08.02.md)** — the "compile a knowledge base once" pattern (Karpathy, Graphify, Google's Open Knowledge Format) keeps multiplying, a wave of unnamed-product "AI memory system" posts shares a suspiciously overlapping cast of reply accounts, Kimi K3's full 2.8T parameters run on a 4GB GPU via per-expert streaming, and open source keeps beating paid SaaS across categories that have nothing to do with coding.

## The knowledge graph

**[Open the interactive atlas](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html)** *(requires GitHub Pages — see below)*

Filter by theme, filter by week on the rail along the bottom, search entries, and click any node for a summary and source link. Deep links like `graph.html#2026.07.12` pre-select a single week. The graph is regenerated from [`graph-data.json`](./graph-data.json) every week — that JSON is the archive's source of truth.

## All digests

| Week | Digest | Graph slice |
|---|---|---|
| 2026.08.02 | [digest-2026.08.02.md](./digest-2026.08.02.md) | [view](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html#2026.08.02) |
| 2026.07.26 | [digest-2026.07.26.md](./digest-2026.07.26.md) | [view](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html#2026.07.26) |
| 2026.07.19 | [digest-2026.07.19.md](./digest-2026.07.19.md) | [view](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html#2026.07.19) |
| 2026.07.12 | [digest-2026.07.12.md](./digest-2026.07.12.md) | [view](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html#2026.07.12) |
| 2026.07.05 | [digest-2026.07.05.md](./digest-2026.07.05.md) | [view](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html#2026.07.05) |
| 2026.06.28 | [digest-2026.06.28.md](./digest-2026.06.28.md) | [view](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html#2026.06.28) |
| 2026.06.21 | [digest-2026.06.21.md](./digest-2026.06.21.md) | [view](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html#2026.06.21) |
| 2026.06.14 | [digest-2026.06.14.md](./digest-2026.06.14.md) | [view](https://terrytompkins.github.io/MindOverModel-TechNews/graph.html#2026.06.14) |

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


## Running the weekly digest

The pipeline runs as a Claude skill. One-time setup: download [`weekly-tech-digest.skill`](./weekly-tech-digest.skill) (or re-zip [`skill/weekly-tech-digest/`](./skill/weekly-tech-digest/)) and upload it to Claude under **Settings → Capabilities → Skills** (or attach it to the project).

Each week:

1. In Raindrop, make sure the week's captures all carry the week tag — the **Sunday** date that starts the week, formatted `YYYY.MM.DD`.
2. Start a **new** Claude conversation (Chat or Cowork) and prompt:

   > Run the weekly-tech-digest skill for tag `YYYY.MM.DD`. Token: `<paste Raindrop API token>`

   Parameters: the **week tag** and the **Raindrop token** (a personal "test token" from Raindrop's Settings → Integrations; it is never stored anywhere). Claude fetches the current `graph-data.json` from this repo automatically, so no other inputs are needed.
3. Claude delivers three files: `digest-YYYY.MM.DD.md`, an updated `graph-data.json`, and a regenerated `graph.html`.
4. Copy them into a clone of this repo, add a row to the digest table above, commit, and push. GitHub Pages redeploys the graph automatically.

**Note on `graph-data.json`:** it is the cumulative archive — every past week's entries live in it. Never delete it; the weekly merge is additive (and idempotent, so re-running a week is safe).

---

*Curated by Terry Tompkins. Digest and graph generated with Claude.*
