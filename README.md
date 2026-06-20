# Historical Entity Tracker

A tool for tracing people, organizations, places, and events across a **multilingual**
historical corpus, to support relative causality analysis of historical processes.

It scans unstructured documents in any language, extracts named entities and events
(each grounded in an exact source quote), resolves which mentions refer to the same
real-world entity across documents and languages, and surfaces **source-grounded,
confidence-scored** links (relationships and co-presence) for a historian to review.

> Methodological stance: "same place + same time" is a **hypothesis, not a fact**.
> The tool proposes candidate links with a confidence score and a traceable quote;
> the historian adjudicates. Nothing is asserted as proven causality.

## Pipeline

```
documents (digital text, any language)
   → extract.py    per-document extraction (Claude structured outputs)  → result.json
   → resolve.py    cross-document / cross-language entity resolution     → resolved.json
   → notion_sink.py  write to the Notion review workspace
   → historian reviews / approves / rejects in Notion
```

## Files

- `schema.py` — Pydantic extraction schema (entities, events, relationships, presence)
- `extract.py` — per-document extraction via `claude-opus-4-8` + structured outputs
- `resolve.py` — cross-document entity resolution (blocking → LLM adjudication → tiered decision)
- `notion_sink.py` — pushes resolved output into the Notion review databases
- `examples/` — sample document
- `docs/` — development log, prior-art survey, UI proposal

## Setup (with uv)

```bash
uv add anthropic pydantic notion-client
export ANTHROPIC_API_KEY=...
export NOTION_TOKEN=...        # for notion_sink.py
```

## Run (end to end)

```bash
python extract.py doc_he.txt --out r1.json
python extract.py doc_en.txt --out r2.json
python resolve.py r1.json r2.json --out resolved.json
python notion_sink.py resolved.json
```

See `docs/DEVELOPMENT_LOG.md` for the full design record, decisions, and next steps.
