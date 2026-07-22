# Methodology — Source-Grounded Hypothesis Generation for Causal Analysis

**Status:** working methodological note. This document positions the tool within
existing social-science and digital-humanities methods, states precisely what it
does and does not claim, and defines the evidentiary logic behind its confidence
scores. It is the theoretical anchor for the prototype and its public explanation.

---

## 1. The problem this tool addresses

Causal analysis of historical and political processes depends on reconstructing
*chains of connected events* — not isolated occurrences. Two research traditions
each solve half of this problem and leave the other half open:

- **Quantitative event data** (GDELT, ACLED, PHOENIX, and similar) catalogues
  events at scale, but treats each event as an independent unit. The *links*
  between an event at time *t₁* and an event at time *t₂* — the connective tissue
  of any causal account — are not recorded.
- **Qualitative process tracing** builds precisely those links, event by event,
  with careful attention to evidentiary weight — but by hand, on one case at a
  time, and almost always within a single language.

The gap between them is a practical bottleneck: there is no scalable, auditable
way to *generate candidate links between events* across a large, multilingual
corpus. This tool targets that gap.

## 2. What the tool claims — and what it does not

**It does claim:** to generate, from unstructured multilingual sources,
*candidate* relationships and co-presence assertions between entities and events,
each grounded in an exact source quote and carrying an explicit confidence score,
for a human researcher to adjudicate.

**It does not claim:** to establish causality, or even to establish that a
hypothesized meeting or connection actually occurred. In the language of the
project: *"same place + same time" is a hypothesis, not a fact.* The tool produces
material for causal inference; it does not perform the inference.

This distinction is deliberate and load-bearing. The tool sits **upstream** of
causal analysis, as a hypothesis generator, not as a substitute for the
researcher's inferential judgment.

## 3. Where this fits in the existing literature

The tool is **complementary to**, not a competitor of, the established inferential
frameworks. It is best understood as automated, scaled hypothesis generation
feeding into those frameworks:

- **Bayesian process tracing** (Beach & Pedersen; Bennett & Checkel;
  Fairfield & Charman, *Social Inquiry and Bayesian Inference*, 2022) supplies the
  logic for *evaluating* a causal hypothesis from evidence. Each piece of evidence
  updates a posterior; independent, reliable evidence strengthens it. This tool
  produces the source-grounded observations that such an analysis consumes.
- **The factoid model of prosopography** (King's College London; Berkeley
  Prosopography Services) treats each source statement as a first-class,
  attributable claim, with identity as an interpretation *over* claims. Our
  `mention` (with its source quote) is a factoid; our canonical entity is the
  interpretive identity over mentions. See `PRIOR_ART.md §3`.
- **Historical network analysis** (Six Degrees of Francis Bacon;
  Ahnert et al., *The Network Turn*, 2020) is the precedent for presenting
  *inferred, confidence-scored* links honestly — showing uncertainty rather than
  asserting certainty.

## 4. The evidentiary logic of the confidence score

The core intuition — *more reliable sources supporting a link raise its
probability* — is an application of Bayesian evidence accumulation. Two
refinements are essential for the score to be defensible in a social-science
setting:

### 4.1 Two axes of uncertainty, not one

A single confidence number conflates two distinct questions:

1. **Existence / reliability** — did the connection (meeting, relationship,
   co-presence) actually occur, as documented?
2. **Causal directionality** — did the event at *t₁* bear causally on the event
   at *t₂*?

Additional corroborating sources primarily raise the *first*. They do not, on
their own, establish the *second*. The methodology therefore treats these as
separate axes, and the schema should carry them separately (a
`link_confidence` and a distinct, more conservative `causal_confidence`) rather
than collapsing them. Overstating the second axis is the failure mode most likely
to draw methodological objection.

### 4.2 Source independence, not source count

Three documents that all cite one underlying testimony are **not** three
independent pieces of evidence. Naïve corroboration counting overstates
confidence exactly when sources share provenance — a well-known weakness of
event-data pipelines. The methodology requires tracking the *independent
provenance* of each supporting quote, so that corroboration is weighted by the
number of *independent* evidentiary chains, not by raw mention count. This is the
single most important discipline separating this tool from naïve text mining.

## 5. The claimed contribution

Stated conservatively, and in the terms most likely to survive peer review:

> A **cross-lingual, source-grounded pipeline** for the **automated,
> confidence-scored, and human-auditable generation of candidate inter-event
> links** from large multilingual historical corpora — serving as scalable
> infrastructure *for* process tracing, not a replacement for it.

Three elements are genuinely novel in combination:

1. **Bridging quantitative event data and qualitative inference** — producing the
   inter-event links that event-data catalogues omit, at a scale process tracing
   cannot reach by hand.
2. **Cross-language as built-in infrastructure** — surfacing connections that are
   invisible within any single language. (Demonstrated: Orde Wingate as a bridge
   node linking the Israeli SOF lineage in Hebrew sources to the British WWII SOF
   ecosystem in English sources — a link invisible without reading both together.)
3. **Auditable AI** — every assertion carries an exact source quote and a
   confidence score, and every proposed link is approved or rejected by a human
   before it is treated as established, directly addressing the hallucination and
   opacity concerns around LLM use in social-science research.

## 6. Limitations and honest scope

- The tool generates hypotheses; it does not test them. Causal claims remain the
  researcher's responsibility.
- Confidence scores are model-derived estimates, not calibrated probabilities,
  until validated against a benchmark (see the HIPE benchmark in
  `PRIOR_ART.md §4`).
- Extraction and resolution quality on noisy, low-resource, or non-Gregorian-dated
  material is not yet independently audited.
- Absence of a documented link is not evidence of absence of a connection; the
  corpus is always partial.

## 7. Relationship to the design decisions

This methodology motivates several decisions already implemented in the prototype:
a source quote on every item, reversible and human-reviewable merges, no silent
merge at medium confidence, and a review-ready data model from the beginning. The
two-axis confidence (§4.1) and independent-provenance tracking (§4.2) are proposed
**extensions** to the schema and are not yet implemented.
