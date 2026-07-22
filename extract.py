"""Per-document historical entity extraction (prototype).

Reads a plain-text document, asks Claude to extract people, organizations, places,
dates, events, relationships, and presence assertions into a validated schema, then
prints a readable summary and writes the structured result to JSON.

Usage:
    export ANTHROPIC_API_KEY=...
    python extract.py examples/yom_kippur_excerpt.txt
    python extract.py examples/yom_kippur_excerpt.txt --out result.json

This is the foundation step. Cross-document entity resolution (deciding when two
mentions are the same person/unit/place) is intentionally handled later by
`resolve.py` — each document is extracted independently first.
"""

from __future__ import annotations

import argparse
import json
import sys

import anthropic

from schema import Extraction

MODEL = "claude-opus-4-8"

SYSTEM_PROMPT = """\
You are an expert historical-document analyst. Your job is to extract structured \
data that will populate a knowledge graph used to trace individuals, organizations, \
and processes across time and place — ultimately to study how historical actors and \
events are connected.

Principles:
- Extract every DISTINCT entity mention. The same surface name appearing twice is one \
entity (reuse its local_id); genuinely different entities get different ids.
- For every extracted item, put an EXACT verbatim quote from the document in `source.quote`. \
Never paraphrase the quote. This is how each fact is traced back to its source.
- Normalize dates as precisely as the text allows, and no more. "spring of 1974" is a \
range, not a guess at a day. Use empty strings when a field is not determinable.
- Roles and titles are time-bound: capture them as stated, even when the same person holds \
different roles at different points.
- Link events, relationships, and presence assertions to other entities using their local_id.
- presence_assertions are the most important output for downstream analysis: record every \
(person, place, time) the text supports. Use high certainty when presence is explicitly \
stated, lower certainty when it is only implied by context. Do NOT assert presence you \
cannot ground in a quote.
- Do not invent facts. If you are unsure, lower the confidence/certainty rather than omit \
or fabricate.
- Documents may be in any language. Keep names in their original form in `name`, and provide \
a Latin-script transliteration in `romanized`.
"""

USER_TEMPLATE = """\
Extract structured historical data from the following document.

<document>
{document}
</document>
"""


def extract(client: anthropic.Anthropic, text: str) -> Extraction:
    response = client.messages.parse(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_TEMPLATE.format(document=text)}],
        output_format=Extraction,
    )
    if response.stop_reason == "max_tokens":
        print(
            "WARNING: hit max_tokens — extraction may be truncated. "
            "For long documents, split the input into smaller sections.",
            file=sys.stderr,
        )
    if response.parsed_output is None:
        raise RuntimeError(f"Model did not return parseable output (stop_reason={response.stop_reason}).")
    return response.parsed_output


def print_summary(ex: Extraction) -> None:
    def line(label: str, n: int) -> None:
        print(f"  {label:<22} {n}")

    print("\n=== Extraction summary ===")
    line("persons", len(ex.persons))
    line("organizations", len(ex.organizations))
    line("places", len(ex.places))
    line("time expressions", len(ex.times))
    line("events", len(ex.events))
    line("relationships", len(ex.relationships))
    line("presence assertions", len(ex.presence_assertions))

    # Resolve local_ids to readable names for the human-facing summary.
    names = {p.local_id: p.name for p in ex.persons}
    names.update({o.local_id: o.name for o in ex.organizations})
    names.update({l.local_id: l.name for l in ex.places})
    times = {t.local_id: t.raw for t in ex.times}

    print("\n=== Sample relationships ===")
    for r in ex.relationships[:12]:
        subj = names.get(r.subject_id, r.subject_id)
        obj = names.get(r.object_id, r.object_id)
        print(f"  {subj} --{r.relation} ({r.confidence:.2f})--> {obj}")

    print("\n=== Presence assertions (co-presence raw material) ===")
    for pa in ex.presence_assertions[:15]:
        who = names.get(pa.person_id, pa.person_id)
        where = names.get(pa.place_id, pa.place_id or "?")
        when = times.get(pa.time_id, pa.time_id or "?")
        print(f"  {who} @ {where} @ {when}  (certainty {pa.certainty:.2f})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract historical entities from a document.")
    parser.add_argument("path", help="Path to a plain-text document.")
    parser.add_argument("--out", help="Write the full structured result to this JSON file.")
    args = parser.parse_args()

    with open(args.path, encoding="utf-8") as f:
        text = f.read()

    client = anthropic.Anthropic()
    ex = extract(client, text)

    print_summary(ex)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(ex.model_dump(), f, ensure_ascii=False, indent=2)
        print(f"\nWrote structured result to {args.out}")


if __name__ == "__main__":
    main()
