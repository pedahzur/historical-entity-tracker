"""Extraction schema for the historical entity-tracking tool.

Every extracted item carries an exact supporting quote (`source`) so each fact can
be traced back to the document — essential for scholarly causality claims. Events,
relationships, and presence assertions reference other entities by their
document-local id (e.g. "p1", "u2"), which keeps the cross-document entity-resolution
step (planned next) cleanly separated from per-document extraction.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceSpan(BaseModel):
    """The exact text from the document that supports an extraction."""

    quote: str = Field(description="Verbatim quote from the document, copied exactly.")


class Person(BaseModel):
    local_id: str = Field(description='Document-local id, e.g. "p1".')
    name: str = Field(description="The person's name exactly as it appears in the text.")
    romanized: str = Field(
        description="Latin-script transliteration of the name; copy `name` if it is already Latin script. "
        "Used later for cross-language matching."
    )
    titles_roles: list[str] = Field(
        description="Ranks, titles, or roles attributed to the person in THIS document "
        '(e.g. "commander of Sayeret Matkal", "protégé of Yarkoni").'
    )
    affiliations: list[str] = Field(
        description="Units, agencies, or organizations the person is associated with here."
    )
    source: SourceSpan


class Organization(BaseModel):
    local_id: str = Field(description='Document-local id, e.g. "u1".')
    name: str
    romanized: str = Field(description="Latin-script form; copy `name` if already Latin script.")
    type: str = Field(
        description='One of: military_unit, intelligence_agency, government_body, company, other.'
    )
    aliases: list[str] = Field(
        description='Alternative names given in the text (e.g. "Shaldag" / "5101 Battalion").'
    )
    source: SourceSpan


class Place(BaseModel):
    local_id: str = Field(description='Document-local id, e.g. "l1".')
    name: str
    romanized: str = Field(description="Latin-script form; copy `name` if already Latin script.")
    type: str = Field(description="One of: city, town, village, base, country, region, geographic_feature, other.")
    source: SourceSpan


class TimeExpression(BaseModel):
    local_id: str = Field(description='Document-local id, e.g. "t1".')
    raw: str = Field(description="The time expression exactly as written in the text.")
    normalized_start: str = Field(
        description="ISO-8601 start of the interval the expression denotes, as precise as the text allows "
        '(e.g. "1973-10-06", "1973-10", "1974"). Empty string if not determinable.'
    )
    normalized_end: str = Field(
        description="ISO-8601 end of the interval. Equal to normalized_start for a precise point; "
        'wider for ranges/approximate expressions (e.g. "early 1980s" -> 1980-01-01..1983-12-31).'
    )
    precision: str = Field(description="One of: time, day, month, year, range, approximate.")
    source: SourceSpan


class Event(BaseModel):
    local_id: str = Field(description='Document-local id, e.g. "e1".')
    description: str = Field(description="One-sentence description of what happened.")
    event_type: str = Field(
        description="One of: battle, operation, meeting, appointment, casualty, capture, "
        "rescue, formation, dissolution, other."
    )
    participant_ids: list[str] = Field(
        description="local_ids of persons/organizations involved in the event."
    )
    place_id: str = Field(description="local_id of the place, or empty string if none stated.")
    time_id: str = Field(description="local_id of the time expression, or empty string if none stated.")
    source: SourceSpan


class Relationship(BaseModel):
    subject_id: str = Field(description="local_id of the subject entity.")
    relation: str = Field(
        description="One of: commands, member_of, protege_of, served_with, recruited, "
        "succeeded, killed, captured, met, located_at, allied_with, opposed."
    )
    object_id: str = Field(description="local_id of the object entity.")
    confidence: float = Field(description="0.0-1.0: how strongly the text supports this relationship.")
    source: SourceSpan


class PresenceAssertion(BaseModel):
    """A (person, place, time) the document supports — the building block for co-presence inference."""

    person_id: str
    place_id: str
    time_id: str
    certainty: float = Field(
        description="0.0-1.0. Use high (>=0.8) when presence is stated explicitly; "
        "lower when it is inferred from context."
    )
    source: SourceSpan


class Extraction(BaseModel):
    """Top-level structured result for one document."""

    persons: list[Person]
    organizations: list[Organization]
    places: list[Place]
    times: list[TimeExpression]
    events: list[Event]
    relationships: list[Relationship]
    presence_assertions: list[PresenceAssertion]
