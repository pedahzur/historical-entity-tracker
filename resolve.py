"""Cross-document entity resolution (the heart of the system).

Takes the per-document extractions produced by `extract.py` and decides, across
documents and languages, which mentions refer to the same real-world entity. It
produces canonical entities plus a queue of candidate links for human review —
exactly the two tables in the Notion workspace (Entities + Candidate Links).

Pipeline per incoming mention:
    1. Blocking  — cheap candidate generation via a normalized romanized key.
    2. Adjudication — Claude judges each candidate pair with full context.
    3. Decision  — tiered by confidence: auto-link / pending (human review) / new.

This prototype keeps the entity store in memory and blocks on the romanized key
only. The production path swaps the store for PostgreSQL + pgvector and adds
embedding similarity as a second blocking signal (see README) — the interfaces
here are written so that swap is localized to `_candidates` and the store.

Usage:
    export ANTHROPIC_API_KEY=...
    # result1.json / result2.json are outputs of: python extract.py <doc> --out resultN.json
    python resolve.py result1.json result2.json --out resolved.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field

import anthropic
from pydantic import BaseModel, Field

from schema import Extraction

MODEL = "claude-opus-4-8"

# Confidence tiers. Tune against your own corpus.
AUTO_LINK_THRESHOLD = 0.90   # >= this: merge automatically
REVIEW_THRESHOLD = 0.60      # [REVIEW, AUTO_LINK): keep as a pending candidate for a human
# < REVIEW_THRESHOLD (or "not the same"): treat as a new, distinct entity


class MatchJudgment(BaseModel):
    """Claude's verdict on whether an incoming mention is the same entity as a candidate."""

    same_entity: bool = Field(description="True if the two refer to the same real-world entity.")
    confidence: float = Field(description="0.0-1.0 confidence in the same_entity verdict.")
    reasoning: str = Field(description="One or two sentences citing the evidence that decided it.")


@dataclass
class Mention:
    """One occurrence of an entity in one document."""

    doc_id: str
    entity_type: str          # person | organization | place
    name: str                 # surface form, original script
    romanized: str            # Latin-script form (blocking key source)
    context: str              # roles/affiliations/type — disambiguating context
    source_quote: str         # exact supporting quote


@dataclass
class CanonicalEntity:
    id: str
    entity_type: str
    canonical_name: str
    romanized: str
    aliases: set[str] = field(default_factory=set)
    mentions: list[Mention] = field(default_factory=list)
    status: str = "confirmed"  # confirmed | pending


@dataclass
class CandidateLink:
    """A proposed match, mirroring the Notion 'Candidate Links' review queue."""

    incoming_quote: str
    matched_entity_id: str
    matched_entity_name: str
    confidence: float
    reasoning: str
    decision: str  # auto_link | pending | rejected


def blocking_key(text: str) -> str:
    """Normalize a (romanized) name into a coarse, order-insensitive matching key.

    Strips diacritics, lowercases, drops punctuation, and sorts tokens so that
    'Orde Wingate' and 'Wingate, Orde' collide. Because extraction populates
    `romanized` for every entity, this is what lets Hebrew and English mentions
    of the same name land in the same block.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    cleaned = re.sub(r"[^a-z0-9 ]", " ", stripped.lower())
    return " ".join(sorted(t for t in cleaned.split() if t))


class EntityResolver:
    def __init__(self, client: anthropic.Anthropic):
        self.client = client
        self.entities: dict[str, CanonicalEntity] = {}
        self.candidate_links: list[CandidateLink] = []
        self._by_key: dict[tuple[str, str], list[str]] = {}
        self._counter = 0

    # --- store ---------------------------------------------------------------

    def _new_entity(self, m: Mention, status: str = "confirmed") -> CanonicalEntity:
        self._counter += 1
        ent = CanonicalEntity(
            id=f"E{self._counter}",
            entity_type=m.entity_type,
            canonical_name=m.name,
            romanized=m.romanized or m.name,
            aliases={m.name, m.romanized} - {""},
            mentions=[m],
            status=status,
        )
        self.entities[ent.id] = ent
        self._by_key.setdefault((m.entity_type, blocking_key(ent.romanized)), []).append(ent.id)
        return ent

    def _attach(self, ent: CanonicalEntity, m: Mention) -> None:
        ent.mentions.append(m)
        ent.aliases.update({m.name, m.romanized} - {""})

    def _candidates(self, m: Mention) -> list[CanonicalEntity]:
        """Blocking: existing entities of the same type sharing the romanized key.

        Production: also union in the top-k nearest entities by embedding of
        `context` (pgvector), to catch matches the surface key misses.
        """
        key = (m.entity_type, blocking_key(m.romanized or m.name))
        return [self.entities[i] for i in self._by_key.get(key, [])]

    # --- adjudication --------------------------------------------------------

    def _adjudicate(self, m: Mention, ent: CanonicalEntity) -> MatchJudgment:
        prior = ent.mentions[0]
        prompt = (
            "Decide whether these two mentions refer to the SAME real-world "
            f"{m.entity_type}.\n\n"
            f"Mention A (existing entity '{ent.canonical_name}'):\n"
            f"  name: {prior.name}\n  context: {prior.context}\n  quote: {prior.source_quote}\n\n"
            f"Mention B (incoming):\n"
            f"  name: {m.name}\n  context: {m.context}\n  quote: {m.source_quote}\n\n"
            "Names may be in different languages/scripts. Weigh roles, dates, places, "
            "and affiliations — not just name similarity. Two different people can share "
            "a name; the same person can be written differently across languages."
        )
        resp = self.client.messages.parse(
            model=MODEL,
            max_tokens=1024,
            # Thinking is off for throughput (many small pairwise calls). For an
            # ambiguous corpus, enable adaptive thinking + raise effort here.
            messages=[{"role": "user", "content": prompt}],
            output_format=MatchJudgment,
        )
        if resp.parsed_output is None:
            return MatchJudgment(same_entity=False, confidence=0.0, reasoning="no parseable judgment")
        return resp.parsed_output

    # --- main entry points ---------------------------------------------------

    def ingest_mention(self, m: Mention) -> None:
        candidates = self._candidates(m)
        if not candidates:
            self._new_entity(m, status="confirmed")
            return

        best: tuple[CanonicalEntity, MatchJudgment] | None = None
        for ent in candidates:
            j = self._adjudicate(m, ent)
            if j.same_entity and (best is None or j.confidence > best[1].confidence):
                best = (ent, j)

        if best is None:
            self._new_entity(m, status="confirmed")
            return

        ent, j = best
        if j.confidence >= AUTO_LINK_THRESHOLD:
            self._attach(ent, m)
            decision = "auto_link"
        elif j.confidence >= REVIEW_THRESHOLD:
            # Don't merge silently. Keep the mention as its own pending entity and
            # queue the proposed link for a human to approve/reject.
            self._new_entity(m, status="pending")
            decision = "pending"
        else:
            self._new_entity(m, status="confirmed")
            decision = "rejected"

        self.candidate_links.append(
            CandidateLink(
                incoming_quote=m.source_quote,
                matched_entity_id=ent.id,
                matched_entity_name=ent.canonical_name,
                confidence=j.confidence,
                reasoning=j.reasoning,
                decision=decision,
            )
        )

    def ingest_document(self, doc_id: str, ex: Extraction) -> None:
        """Feed one document's extraction into the resolver."""
        for p in ex.persons:
            self.ingest_mention(Mention(
                doc_id, "person", p.name, p.romanized,
                context="; ".join([*p.titles_roles, *p.affiliations]),
                source_quote=p.source.quote,
            ))
        for o in ex.organizations:
            self.ingest_mention(Mention(
                doc_id, "organization", o.name, o.romanized,
                context=f"{o.type}; aliases: {', '.join(o.aliases)}",
                source_quote=o.source.quote,
            ))
        for l in ex.places:
            self.ingest_mention(Mention(
                doc_id, "place", l.name, l.romanized,
                context=l.type, source_quote=l.source.quote,
            ))


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve entities across extraction outputs.")
    parser.add_argument("inputs", nargs="+", help="JSON files written by `extract.py --out`.")
    parser.add_argument("--out", help="Write resolved entities + candidate links to this JSON file.")
    args = parser.parse_args()

    client = anthropic.Anthropic()
    resolver = EntityResolver(client)

    for path in args.inputs:
        with open(path, encoding="utf-8") as f:
            ex = Extraction.model_validate(json.load(f))
        resolver.ingest_document(doc_id=path, ex=ex)

    print(f"\n=== Resolved {len(resolver.entities)} canonical entities "
          f"from {len(args.inputs)} documents ===")
    for ent in resolver.entities.values():
        docs = {m.doc_id for m in ent.mentions}
        flag = "  <- spans multiple documents" if len(docs) > 1 else ""
        status = "" if ent.status == "confirmed" else f" [{ent.status}]"
        print(f"  [{ent.entity_type}] {ent.canonical_name}{status} "
              f"({len(ent.mentions)} mentions){flag}")

    print(f"\n=== {len(resolver.candidate_links)} candidate links for review ===")
    for c in resolver.candidate_links:
        print(f"  ~{c.confidence:.2f} [{c.decision}] -> {c.matched_entity_name}: {c.reasoning}")

    if args.out:
        payload = {
            "entities": [
                {
                    "id": e.id, "type": e.entity_type, "name": e.canonical_name,
                    "romanized": e.romanized, "aliases": sorted(e.aliases),
                    "status": e.status, "documents": sorted({m.doc_id for m in e.mentions}),
                    "mentions": [
                        {"doc_id": m.doc_id, "name": m.name, "quote": m.source_quote}
                        for m in e.mentions
                    ],
                }
                for e in resolver.entities.values()
            ],
            "candidate_links": [vars(c) for c in resolver.candidate_links],
        }
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\nWrote resolved graph to {args.out}")


if __name__ == "__main__":
    main()
