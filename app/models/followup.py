"""
Data models for POST /analyze/follow-up.

SCOPE NOTE: this feature is stateless on the backend - no chat history
is persisted to a database. The frontend holds the conversation array
in memory and sends the full thing with every request (same shape as
the Anthropic API's own stateless message-list convention). If
persistent, resumable chat threads are wanted later, that's a real
schema addition (a conversation/message table), not something to fake
by pretending this already remembers anything server-side.
"""

from pydantic import BaseModel, Field


class FollowUpTurn(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=2000)


class FollowUpRequest(BaseModel):
    # The original symptoms text from the analysis this conversation is
    # attached to - used to re-run the deterministic rule engine over
    # the FULL conversation (original + every message since), so a
    # rule-engine red flag raised mid-conversation isn't only caught if
    # the AI itself notices it. See app/ai/triage_service.py's
    # answer_follow_up.
    original_symptoms: str = Field(..., min_length=1, max_length=1000)
    conversation: list[FollowUpTurn] = Field(default_factory=list, max_length=20)
    message: str = Field(..., min_length=1, max_length=1000)


class FollowUpResponse(BaseModel):
    reply: str
    severity: str  # "LOW" | "MODERATE" | "HIGH" | "EMERGENCY"
    escalation_detected: bool
    sos_recommended: bool
    disclaimer: str
