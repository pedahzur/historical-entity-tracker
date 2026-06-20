"""Push resolved.json into the Notion review workspace.

Closes the loop: extract.py -> resolve.py -> notion_sink.py -> Notion.
Writes canonical entities to the "Entities" database and proposed matches to the
"Candidate Links" database (the two created for this project).

Setup:
    pip install notion-client   # or: uv add notion-client
    # Create an internal integration at https://www.notion.so/my-integrations,
    # then share both databases with it (••• -> Connections -> your integration).
    export NOTION_TOKEN=secret_xxx

Usage:
    python notion_sink.py resolved.json

The database IDs below are this project's defaults; override via env vars if they
change.

Note: this prototype always *creates* pages, so re-running duplicates rows. The
production version should upsert — query the database by a stable key (e.g. the
romanized name) and update the existing page instead of creating a new one.
"""

from __future__ import annotations

import argparse
import json
import os

from notion_client import Client

ENTITIES_DB = os.environ.get("NOTION_ENTITIES_DB", "49b4012af7cc4cecadcd2921340adbb3")
CANDIDATE_LINKS_DB = os.environ.get("NOTION_CANDIDATE_LINKS_DB", "a64f139a9e3c4959af37199b24083de9")

# resolve.py decisions -> Notion "Decision" select options.
DECISION_MAP = {"auto_link": "approved", "pending": "pending", "rejected": "rejected"}


def _rich_text(text: str) -> list[dict]:
    """Notion rich_text value, clamped to the 2000-char per-block API limit."""
    return [{"type": "text", "text": {"content": text[:2000]}}] if text else []


def _bullet(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _rich_text(text)},
    }


def push_entity(notion: Client, e: dict) -> None:
    children = [
        {"object": "block", "type": "heading_2",
         "heading_2": {"rich_text": _rich_text("Mentions")}}
    ]
    for m in e["mentions"]:
        doc = os.path.basename(m["doc_id"])
        children.append(_bullet(f'[{doc}] {m["name"]} — "{m["quote"]}"'))

    notion.pages.create(
        parent={"database_id": ENTITIES_DB},
        properties={
            "Name": {"title": _rich_text(e["name"])},
            "Romanized": {"rich_text": _rich_text(e.get("romanized", ""))},
            "Type": {"select": {"name": e["type"]}},
            "Aliases": {"rich_text": _rich_text("; ".join(e.get("aliases", [])))},
            # Unknown multi_select options are auto-created by Notion.
            "Source Documents": {
                "multi_select": [{"name": os.path.basename(d)} for d in e.get("documents", [])]
            },
            "Review Status": {"select": {"name": e.get("status", "pending")}},
        },
        children=children,
    )


def push_candidate_link(notion: Client, c: dict) -> None:
    notion.pages.create(
        parent={"database_id": CANDIDATE_LINKS_DB},
        properties={
            "Match": {"title": _rich_text(f'→ {c["matched_entity_name"]}')},
            "Mention A": {"rich_text": _rich_text(c["incoming_quote"])},
            "Mention B": {"rich_text": _rich_text(c["matched_entity_name"])},
            "Confidence": {"number": round(float(c["confidence"]), 3)},
            "Reasoning": {"rich_text": _rich_text(c.get("reasoning", ""))},
            "Decision": {"select": {"name": DECISION_MAP.get(c["decision"], "pending")}},
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Push resolved.json to Notion.")
    parser.add_argument("resolved", help="Path to resolved.json (output of resolve.py).")
    args = parser.parse_args()

    with open(args.resolved, encoding="utf-8") as f:
        data = json.load(f)

    notion = Client(auth=os.environ["NOTION_TOKEN"])

    entities = data.get("entities", [])
    links = data.get("candidate_links", [])

    for e in entities:
        push_entity(notion, e)
    for c in links:
        push_candidate_link(notion, c)

    print(f"Pushed {len(entities)} entities and {len(links)} candidate links to Notion.")


if __name__ == "__main__":
    main()
