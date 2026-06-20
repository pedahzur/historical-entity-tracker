# UI Proposal — A Friendly Interface for Historians

Goal: let a historian with **no technical or mathematical background** use the tool
end to end — add documents, review the machine's suggestions, explore people and
events across time and place — without ever seeing code, JSON, a database, or a raw
probability.

---

## Design principles

1. **No jargon, no math on screen.** Never show "confidence 0.87", "entity
   resolution", or "blocking key". Show **plain language and color**:
   - *Very likely the same person* (green) · *Possibly the same — please check*
     (amber) · *Probably different* (grey). One number stays hidden behind the words.
2. **The historian is the judge; the machine is the assistant.** Every machine
   inference is a **suggestion with a source quote**, presented for approval. The
   tool never asserts "they met" — it says *"Both were in Naffakh on 8 Oct 1973 —
   did they meet?"* with the quotes, and offers **Yes / No / Not sure**.
3. **Always show the source.** Every fact, every suggestion, links to the exact
   sentence in the original document. Trust comes from traceability.
4. **One task per screen.** Add documents; review suggestions; explore. Never mix.
5. **Reversible.** Any decision can be undone. Nothing is destructive.
6. **Works in the historian's languages.** Names shown in original script; the
   romanized form is internal plumbing, not foregrounded.

---

## The five screens

### 1. Library (add & manage documents)
- Drag-and-drop or "Add from Google Drive". A document appears with a status:
  *Reading… → Done*. (Behind the scenes: `extract.py` → `resolve.py`.)
- No settings to configure. Sensible defaults; an "Advanced" drawer hides anything technical.

### 2. Review queue (the core human-in-the-loop)
The single most important screen — a clean, swipeable card stack.
- **One suggestion per card**, e.g.:
  > **Are these the same person?**
  > • "אורד וינגייט" — *SOF Roots 1920–1923* — "פלוגות הלילה המיוחדות של אורד וינגייט"
  > • "Orde Wingate" — *WWII Military Entrepreneurs* — "organizing irregular forces in Palestine (the Special Night Squads)"
  > _Our take: **Very likely the same.**_   **[ Yes ]  [ No ]  [ Not sure ]**
- Both source quotes shown inline. Optional "see in document" opens the full context.
- Same pattern for **co-presence**: *"Did X and Y meet?"* with the shared place/date and quotes.
- Progress shown as "12 suggestions left", not a percentage of a model score.

### 3. Person / Entity page
- A profile: name (all language variants), a one-line summary, and:
  - **Timeline** — every dated mention, as a horizontal time ribbon.
  - **Map** — every place the person is documented, pinned.
  - **Connections** — people they met / served with / commanded (confirmed = solid
    line, suggested = dashed line awaiting review).
  - **Sources** — every quote that mentions them, each linking back to its document.

### 4. Explore (timeline + map + network, together)
- A linked view: a **timeline scrubber** filters a **map** and a **network graph**.
  Drag the time window from 1920 to 1973 and watch who appears, where, and who
  connects to whom.
- The payoff for the causality research: *see* clusters of co-presence and how
  lineages (HaShomer → SNS → Palmach → Sayeret Matkal) thread through time.
- (Reuse, don't build from scratch — see PRIOR_ART.md → Palladio / nodegoat.)

### 5. Ask (natural-language question box)
- A search/question bar: *"Who was in Naffakh in October 1973?"* Answers are built
  from the confirmed graph, **with sources attached** — never an ungrounded guess.

---

## Phased build (so the historian gets value early)

| Phase | Interface | Effort | What the historian gets |
|-------|-----------|--------|--------------------------|
| **Now** | **Notion** (already built) | done | Review queue + entity pages with sources. Usable today. |
| **1** | Notion + a simple **Palladio export** button | low | Timeline/map/network exploration via Palladio. |
| **2** | A thin **web app**: Library + Review queue screens | medium | One-click document add and the swipeable review card stack. |
| **3** | Full web app: Entity pages + Explore + Ask | higher | The complete experience. Consider nodegoat as the back end. |

**Recommendation:** stay on **Notion (Phase 0–1)** until extraction quality and
thresholds are validated and the review workflow feels right with real documents.
Notion already delivers Screens 1–2 in spirit (Library = Entities DB, Review =
Candidate Links). Graduate to a web app only when the Notion flow is proven.

---

## What to decide with the historian before building Phase 2+

- Single-user or collaborative (multiple historians reviewing together)?
- Web app vs. desktop app (offline archives, sensitive material)?
- Preferred display language(s) for the interface chrome.
- How much of "Explore" is essential vs. nice-to-have (drives embed vs. build).
