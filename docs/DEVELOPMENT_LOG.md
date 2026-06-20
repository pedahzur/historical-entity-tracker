# Development Log — Historical Entity Tracker

A precise, step-by-step record of what was designed and built, why, and how to
continue. Nothing critical is omitted; a new collaborator (human or AI) should be
able to resume from this file alone.

Last updated: 2026-06-16.

---

## 1. Goal

A tool to support **relative causality analysis of historical processes**. Core
research premise: when two people are documented at the same place, date, and time,
we can hypothesize a meeting; aggregating such co-presences and relationships across
a large, **multilingual** corpus lets a historian trace individuals and processes
along a timeline.

The tool scans unstructured documents in any language, extracts named entities
(people, organizations, places, dates) and events, resolves which mentions refer to
the same real-world entity across documents and languages, and surfaces
**source-grounded, confidence-scored** links for the historian to review.

Key methodological stance (drives the whole architecture): *"same place + same
time ⇒ they met"* is a **hypothesis, not a fact**. The tool produces candidate
links with a confidence score and a traceable source quote; the historian
adjudicates. Nothing is asserted as proven causality.

---

## 2. Decisions taken (with rationale)

These were made jointly and should not be silently reversed.

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | **Tier = Workflow, not autonomous Agent.** | The pipeline is well-defined (ingest → extract → resolve → store → infer). Code-orchestrated is cheaper, debuggable, reproducible. |
| D2 | **Model = `claude-opus-4-8`.** | Strongest for hard multilingual historical text. Sonnet 4.6 is the cost fallback for bulk. |
| D3 | **Build extraction prototype FIRST**, before full schema/storage. | Extraction quality is the foundation; the real schema emerges from real output. Cheap to validate. |
| D4 | **Data model is "review-ready" from day one** (confidence + source on every item), but **defer the review UI.** | Provenance/scores are data (mandatory); the approval interface is presentation (deferrable). |
| D5 | **Every extracted item carries an exact source quote (citation).** | Required for scholarly causality claims; enables tracing every fact to its document. |
| D6 | **Entity resolution merges are reversible, scored, and human-reviewable.** Never silent-merge at medium confidence. | A wrong merge would silently corrupt every downstream causality claim. |
| D7 | **`romanized` field on every named entity.** | The cross-language blocking key. Without it, "ישראל שוחט" and "Israel Shochat" never meet. |
| D8 | **Storage: start simple (in-memory / JSON), target PostgreSQL + pgvector.** | pgvector adds embedding similarity as a second blocking signal at scale. |
| D9 | **Review interface: Notion (chosen over Airtable).** | Researcher benefits from entities living beside narrative/notes. Airtable is better for high-volume bulk review; revisit if volume demands it. |
| D10 | **Code lives in a dedicated repo** (`pedahzur/historical-entity-tracker`), not the user's R-skills repo. | It's a Python research tool, separate concern. |

---

## 3. Architecture

```
documents (digital text, any language, continuous stream)
        │
        ▼
[extract.py]  per-document extraction via Claude + structured outputs
        │     → result.json  (entities + events + relationships + presence, each with a source quote)
        ▼
[resolve.py]  cross-document / cross-language entity resolution
        │     blocking (romanized key) → Claude adjudication → tiered decision
        │     → resolved.json  (canonical entities + candidate-link review queue)
        ▼
[notion_sink.py]  write to the Notion review workspace
        │     → Entities DB + Candidate Links DB
        ▼
   historian reviews / approves / rejects in Notion
```

Planned but not yet built: co-presence inference layer (query over presence
assertions), persistence (Postgres+pgvector), visualization (timeline/map/network).

---

## 4. The extraction schema (`schema.py`)

Per document, Claude returns a validated `Extraction` with these record types.
Every record has a `source` quote. Entities carry a document-local id (`p1`, `u2`,
…) so events/relationships reference them within the document; cross-document
identity is decided later by `resolve.py`.

- **Person** — `local_id, name, romanized, titles_roles[], affiliations[], source`
- **Organization** — `local_id, name, romanized, type, aliases[], source`
- **Place** — `local_id, name, romanized, type, source`
- **TimeExpression** — `local_id, raw, normalized_start, normalized_end, precision, source`
- **Event** — `local_id, description, event_type, participant_ids[], place_id, time_id, source`
- **Relationship** — `subject_id, relation, object_id, confidence, source`
- **PresenceAssertion** — `person_id, place_id, time_id, certainty, source` ← the co-presence building block

Design choices baked in: time normalized as an interval (`start`/`end`) to represent
imprecision ("spring 1874" → a range, not a guessed day); roles are time-bound
(captured as stated); presence certainty is high when explicit, lower when inferred.

---

## 5. The pipeline files

```
historical-entity-tracker/
├── schema.py            # Pydantic extraction schema
├── extract.py           # per-document extraction (Claude structured outputs)
├── resolve.py           # cross-document entity resolution (the core)
├── notion_sink.py       # writes resolved.json into Notion
├── examples/
│   └── yom_kippur_excerpt.txt
└── docs/
    ├── DEVELOPMENT_LOG.md   # this file
    ├── PRIOR_ART.md         # survey of existing tools + lessons
    └── UI_PROPOSAL.md       # friendly interface design for historians
```

With uv: `uv add anthropic pydantic notion-client` (replaces requirements.txt).

### `extract.py`
- Model `claude-opus-4-8`, adaptive thinking, `messages.parse()` against the
  `Extraction` Pydantic model (schema-validated output, no brittle JSON parsing).
- `max_tokens=16000`; warns on truncation. Long documents must be split into
  sections and merged (not yet implemented — see §8).

### `resolve.py` (the heart)
- `blocking_key()`: NFKD-normalize → strip diacritics → lowercase → drop
  punctuation → sort tokens. Order-insensitive, cross-script via `romanized`.
- `_adjudicate()`: Claude judges a pair, returns `MatchJudgment {same_entity,
  confidence, reasoning}`. Thinking off for throughput; enable for ambiguous corpora.
- Tiers: `>=0.90` auto-merge · `0.60–0.90` pending entity + queued candidate link
  · `<0.60` (or "not same") new distinct entity.
- Storage isolated to `_candidates` + the in-memory store, so swapping to
  Postgres+pgvector is localized.

### `notion_sink.py`
- Official `notion-client` SDK. Needs `NOTION_TOKEN` with both databases shared.
- **Not idempotent yet**: re-running creates duplicates. Production needs upsert by
  a stable key (romanized name).

---

## 6. The Notion review workspace (already created)

Parent page **Historical Entity Tracker**:
`https://app.notion.com/p/385f7ac7250a81e59b06ec2947e696f4`

| Database | Database ID (for notion-client) | Data source ID |
|----------|---------------------------------|----------------|
| Entities | `49b4012af7cc4cecadcd2921340adbb3` | `collection://54227be9-193b-4c3c-9ee4-47ea22ee04cf` |
| Candidate Links | `a64f139a9e3c4959af37199b24083de9` | `collection://e2d83c63-2ca6-4c29-b1d0-7bf767a2fc1d` |

**Entities** properties: `Name` (title), `Romanized` (text), `Type`
(select: person/organization/place/event), `Aliases` (text), `Source Documents`
(multi-select), `Review Status` (select: confirmed/pending).

**Candidate Links** properties: `Match` (title), `Mention A` (text), `Mention B`
(text), `Confidence` (number), `Reasoning` (text), `Decision`
(select: pending/approved/rejected).

Seeded (manually, as a demo) with: Orde Wingate, Special Night Squads, Israel
Shochat, Manya Shochat, Sayeret Matkal; and three candidate links.

---

## 7. What was validated on real data

Source documents (from the user's Google Drive):
- **Hebrew**: "הרצאה – שורשי ה-SOF הישראלי 1920–1923"
- **English**: "April_2026_Military_Entrepreneurs_WWII_SOF_Draft"

Results demonstrated:
1. **Extraction** on the Hebrew lecture: people/orgs/places/times/events/relationships
   + presence assertions, each with a Hebrew source quote and a `romanized` field.
   Surfaced a co-presence cluster (the secret cave meeting at Kfar Giladi, summer
   1921: Manya Shochat, Israel Shochat, Moshe Levit, ~20 people).
2. **Cross-lingual resolution**: "אורד וינגייט" (Hebrew doc) and "Orde Wingate"
   (English doc) merged via the shared romanized key, adjudicated same-entity at
   0.96. Likewise "פלוגות הלילה המיוחדות" ↔ "Special Night Squads". Wingate became
   a **bridge node** connecting the Israeli SOF lineage to the British WWII SOF
   ecosystem — a connection invisible without reading both documents together.

---

## 8. Known limitations (current prototype)

- **Long documents** exceed one `max_tokens` window — need sectioned extraction + merge.
- **`notion_sink.py` is not idempotent** — re-runs duplicate rows; needs upsert.
- **Blocking is romanized-key only** — add embedding (pgvector) similarity as a second signal.
- **No persistence** — entity store is in-memory; resolution state lost between runs.
- **No co-presence layer yet** — presence assertions extracted but not yet aggregated.
- **Romanization quality** depends on the model; consider a deterministic transliteration backstop.

---

## 9. Next steps (prioritized)

1. **Validate extraction quality** on 5–10 real documents; tune schema + prompt + thresholds.
2. **Idempotency + Postgres+pgvector**: real store, upsert, embedding blocking.
3. **Co-presence layer**: query over presence assertions → "may have met" candidates.
4. **Visualization**: timeline + map + network (see PRIOR_ART.md → Palladio, nodegoat).
5. **Friendly UI** for non-technical historians (see UI_PROPOSAL.md).

---

## 10. Open questions for the historian

- Confidence thresholds: what false-merge rate is acceptable vs. review burden?
- Which gazetteer/authority for places and people? (Wikidata? a project authority?)
- Date handling for non-Gregorian calendars (Hebrew, Islamic, Julian)?
- Will scanned/handwritten sources enter later (→ Transkribus for transcription)?
