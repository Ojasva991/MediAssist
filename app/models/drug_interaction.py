"""
Data models for POST /drug-interactions/check.

See app/interactions/corpus.py for the crucial scope note: this checks
against a small, hand-curated list, not a comprehensive database. The
response model deliberately has no single "is_safe: bool" field - a
boolean like that invites being read as a guarantee, which this
feature can never honestly give.
"""

from pydantic import BaseModel, Field, field_validator


class DrugInteractionCheckRequest(BaseModel):
    drugs: list[str] = Field(
        ..., min_length=2, max_length=10, description="Two or more drug names to check pairwise."
    )

    @field_validator("drugs")
    @classmethod
    def _validate_drugs(cls, value: list[str]) -> list[str]:
        cleaned = [d.strip() for d in value if d.strip()]
        if len(cleaned) < 2:
            raise ValueError("Enter at least two drug names to check for interactions.")
        return cleaned


class InteractionMatchOut(BaseModel):
    drug_a: str
    drug_b: str
    severity: str  # "MODERATE" | "MAJOR"
    description: str


class DrugInteractionCheckResponse(BaseModel):
    matches: list[InteractionMatchOut]
    unrecognized_drugs: list[str] = Field(
        default_factory=list,
        description=(
            "Names that didn't match anything in our limited reference list - these were NOT "
            "checked, which is different from being checked and found safe."
        ),
    )
    disclaimer: str
