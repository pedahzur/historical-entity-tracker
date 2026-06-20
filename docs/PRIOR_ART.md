# Prior Art — Existing Tools and What We Can Learn / Reuse

A survey of existing tools in the same space (digital humanities, NER + entity
linking, prosopography, network/timeline/map visualization, transcription), what
each does well, and concretely how it relates to **our** tool. The goal is not to
reinvent these — it's to reuse standards and components where sensible and to be
clear about where our tool is genuinely different.

> **Where we are different.** Most tools below do *one* of: annotate entities in
> one document, *or* store a hand-curated prosopographical database, *or* visualize
> a network someone already built. Our tool's distinct contribution is the
> **automated, cross-lingual, source-grounded pipeline from raw multilingual text →
> resolved entities → confidence-scored co-presence/relationship candidates**, with
> the LLM doing both extraction and match adjudication. The tools below are best
> understood as components we can plug into the ends of that pipeline (ingest,
> authority control, visualization) rather than replacements for its core.

---

## 1. nodegoat — closest conceptual relative

A web-based research environment for the humanities: you model your own data
(objects, persons, events) and their relations, with **built-in temporal and
geospatial dimensions** and diachronic network + map visualization. Explicitly
supports vague dates and historical regions; can publish a dataset as a
self-contained archive (JSON + CSV + HTML).

- **What to learn:** its data model is essentially ours (entities + relations +
  time + place). Its handling of *vague/uncertain dates* and *historical regions*
  is exactly what our `TimeExpression` interval and place handling need.
- **How we can use it:** as the **storage + visualization back end** for our
  pipeline. We do the automated extraction/resolution (which nodegoat does not),
  then export `resolved.json` into nodegoat's import format for mapping, timeline,
  and network analysis.
- Sources: [nodegoat.net](https://nodegoat.net/), [Programming Historian: Designing a Database with nodegoat](https://programminghistorian.org/en/lessons/designing-database-nodegoat), [nodegoat use cases](https://nodegoat.net/usecases).

## 2. Recogito (Pelagios) — annotation + geo-resolution

Collaborative annotation of texts, tables, and images; runs NER to tag **places and
persons**, then helps map place names to a global gazetteer (geo-resolution).
Exports RDF / GeoJSON / CSV. DH Award winner.

- **What to learn:** the **geo-resolution UX** — suggest a gazetteer match, let the
  human confirm. Their two-stage "geotag → georesolve" maps onto our "extract → resolve".
- **How we can use it:** for **place reconciliation** — feed our extracted place
  names through a gazetteer the way Recogito does. A model to learn from more than a
  component to embed (it's single-document/manual).
- Sources: [recogito.pelagios.org](https://recogito.pelagios.org/), [Recogito tutorial](https://recogito.pelagios.org/help/tutorial), [Pelagios annotation](https://pelagios.org/activities/annotation/).

## 3. Prosopography tools (Factoid model; Berkeley Prosopography Services; SPEAR)

The scholarly tradition for exactly our problem. The **factoid model** (King's
College London) records each source statement as a "factoid" attached to a person —
the *source* of a claim is first-class, claims can conflict, identity is an
interpretation over factoids. Berkeley Prosopography Services auto-extracts
prosopographic data from TEI text and models *disambiguation as a probabilistic,
revisable inference*.

- **What to learn (important):** the **factoid model validates our core design** —
  our `mention` (with its source quote) *is* a factoid; our `CanonicalEntity` is the
  interpretive identity over mentions. BPS's revisable, scenario-driven
  disambiguation is precisely our reversible, confidence-scored merge (D6).
- **How we can use it:** align our JSON output with factoid/prosopography
  conventions for interoperability with this community and its tools (Gephi, etc.).
- Sources: [KCL Factoid Prosopography](https://www.kcl.ac.uk/factoid-prosopography/about), [Berkeley: Social Networks from History](https://matrix.berkeley.edu/research-article/social-networks-history/), [DHQ: Graph-based prosopography (Romans 1by1)](https://dhq.digitalhumanities.org/vol/18/2/000710/000710.html).

## 4. HIPE shared task — NER + entity linking in multilingual historical documents

A research benchmark (HIPE-2020/2022) for our hardest sub-problem: NER and entity
**linking** across multiple languages, time periods, and noisy historical text.
Documents the real challenges: domain heterogeneity, input noise, language change,
scarce resources.

- **What to learn:** a realistic expectation-setter and **evaluation methodology**.
- **How we can use it:** use HIPE datasets/metrics as a **benchmark** to validate
  our pipeline against published baselines and to tune thresholds.
- Sources: [HIPE-2022 overview (EPFL)](https://infoscience.epfl.ch/entities/publication/0e143616-31f8-41b1-910b-b6688a456c71), [HIPE-2022 site](https://hipe-eval.github.io/HIPE-2022/).

## 5. Transkribus — transcription (for the future scanned-source path)

AI platform for **handwritten** text recognition (HTR) across 100+ languages, plus
print OCR, with NER tagging and structured export. Character error rate ~5–10%.

- **What to learn / how we can use it:** the **front door** for when the corpus
  includes scans or manuscripts (not needed yet — corpus is digital text).
  Transkribus transcribes → exports text → feeds `extract.py`. Keep ingest
  format-agnostic. (Multimodal LLMs are also closing the gap on OCR+NER in one pass.)
- Sources: [transkribus.org](https://www.transkribus.org/), [Transkribus for researchers](https://www.transkribus.org/for-researchers), [Multimodal LLMs for OCR + NER (arXiv 2504.00414)](https://arxiv.org/html/2504.00414).

## 6. OpenRefine + Wikidata reconciliation — authority control / dedup

OpenRefine reconciles a column of names against an authority (e.g. Wikidata):
propose matches by type, confirm, then pull enrichment data.

- **What to learn:** the **reconciliation interaction** (propose → confirm → enrich)
  is a battle-tested version of our review queue.
- **How we can use it:** anchor confirmed entities to **Wikidata QIDs** where they
  exist — cross-project interoperability, free enrichment (dates, coordinates), and
  a global disambiguation anchor. For obscure local figures, our LLM resolver remains.
- Sources: [OpenRefine reconciling docs](https://openrefine.org/docs/manual/reconciling), [Wikidata OpenRefine tools](https://www.wikidata.org/wiki/Wikidata:Tools/OpenRefine), [wikidata.reconci.link](https://wikidata.reconci.link/).

## 7. Visualization: Palladio & Six Degrees of Francis Bacon

- **Palladio** (Stanford Humanities+Design): browser tool to upload tabular data and
  get **maps, networks, timelines, tables** with no account/install.
- **Six Degrees of Francis Bacon**: a large historical **social-network** project
  (15,824 figures, 171,419 relationships), notable for *statistically inferred*
  links — a precedent for our confidence-scored, inference-based relationships.

- **How we can use them:** Palladio is the fastest way to **visualize our output
  now** — export `resolved.json` to CSV and drop it in. Six Degrees is the design
  reference for our eventual network view and for *presenting inferred links
  honestly* (showing confidence, not asserting certainty).
- Sources: [Palladio (Stanford)](http://hdlab.stanford.edu/projects/palladio/), [DHQ: Networks, Maps, and Time with Palladio](https://www.digitalhumanities.org/dhq/vol/15/1/000534/000534.html), [Six Degrees of Francis Bacon](http://sixdegreesoffrancisbacon.com/), [DHQ: Reconstructing Large Historical Social Networks](https://www.digitalhumanities.org/dhq/vol/10/3/000244/000244.html).

---

## Summary: build vs. reuse

| Pipeline stage | Reuse an existing tool? | Plan |
|----------------|-------------------------|------|
| Transcription (scans/HTR) | **Reuse** Transkribus (when needed) | Keep ingest format-agnostic |
| Extraction (NER) from text | **Build** (our LLM pipeline) | Benchmark against HIPE |
| Entity resolution / linking | **Build** (LLM adjudication) + **anchor** to Wikidata | Romanized blocking + LLM + optional QID |
| Place disambiguation | **Reuse** a gazetteer | Geo-resolve confirmed places |
| Data model & vague dates | **Learn from** nodegoat + factoid model | Align schema/vocabulary |
| Storage + viz | **Reuse** Palladio (now), nodegoat (richer) | Export adapters from `resolved.json` |

**Bottom line:** the novel core — automated cross-lingual extraction *and* LLM-based
match adjudication producing scored, reviewable links — is ours to build. Almost
everything around it (transcription, gazetteers, authority control, visualization,
the factoid data model) is established and should be reused rather than rebuilt.
