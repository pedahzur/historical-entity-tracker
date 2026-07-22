# Historical Entity Tracker

**Project page:** https://pedahzur.github.io/historical-entity-tracker/

Historical sources rarely tell a complete story in one place. A person appears under
different spellings, an organization changes names, a location is described in
another language, and the connection between two events may be scattered across
documents written decades apart.

**Historical Entity Tracker is a research prototype for finding that connective
tissue without hiding the evidence.** It turns multilingual source text into
structured, reviewable hypotheses about people, organizations, places, events, and
their relationships. Every extracted claim retains an exact source quote, and every
proposed cross-document link is scored and left open to human judgment.

> Same place + same time is a hypothesis, not a fact.

The project sits between large-scale event data and close qualitative process
tracing: it helps researchers discover candidate links at corpus scale, but it does
not claim to prove that people met or that one event caused another.

## What it does

```text
multilingual documents
  -> extract entities, events, dates, relationships, and presence
  -> preserve the exact quote supporting every item
  -> reconcile names and identities across documents and languages
  -> send uncertain matches to a historian for review
  -> produce a traceable foundation for timelines, maps, and network analysis
```

The current prototype has four parts:

- `schema.py` defines the source-grounded extraction model.
- `extract.py` extracts structured records from one document.
- `resolve.py` proposes cross-document and cross-language identity matches.
- `notion_sink.py` sends entities and candidate links to a Notion review workspace.

## Why it matters

Event databases are good at cataloguing what happened. Process tracing is good at
reasoning carefully about how events may be connected. The gap is the expensive,
manual work of discovering possible connections across a large and multilingual
archive.

This project explores a careful middle layer: automated hypothesis generation with
provenance, uncertainty, and human review built into the data model. The machine
widens the search; the historian remains responsible for interpretation.

## Prototype evidence

The pipeline has been exercised on Hebrew and English source material. In that test,
it reconciled the Hebrew and English mentions of Orde Wingate and the Special Night
Squads, surfacing a cross-language bridge between two bodies of historical material.
This is a demonstration of the workflow, not an independent accuracy evaluation.

## Current limitations

- Extraction quality has not yet been independently benchmarked across languages.
- Long documents still need sectioned extraction and merge logic.
- Entity matching currently uses a romanized name key before model adjudication.
- Resolution state is in memory; there is no durable graph store yet.
- Presence is extracted, but candidate co-presence links are not yet aggregated.
- The Notion writer creates duplicate rows when run more than once.
- Confidence scores are model estimates, not calibrated probabilities.

## Run the prototype

Requires Python 3.10+ and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
export ANTHROPIC_API_KEY=...
export NOTION_TOKEN=...  # only needed for the optional Notion export

uv run python extract.py examples/yom_kippur_excerpt.txt --out result.json
uv run python resolve.py result.json --out resolved.json
uv run python notion_sink.py resolved.json
```

To preview the public-facing project page, open `index.html` or serve the repository
directory with any static web server.

## Documentation

- [Methodology](docs/METHODOLOGY.md) — claims, evidentiary logic, and limits
- [Prior art](docs/PRIOR_ART.md) — related digital-humanities tools and methods
- [Interface proposal](docs/UI_PROPOSAL.md) — a historian-friendly review workflow

## AI-assisted workflow

The prototype uses Claude (`claude-opus-4-8`) with structured outputs for extraction
and pairwise entity adjudication. Prompts require verbatim source quotes and
conservative date handling. Proposed links are designed for approval or rejection by
a researcher before they are treated as established. The software and its
multilingual accuracy remain experimental.

## License and citation

Released under the [MIT License](LICENSE). Citation metadata is available in
[`CITATION.cff`](CITATION.cff).
