"""
Data models for /caregivers routes.

Scope note (see app/storage/models.py's CaregiverLinkRecord for the
full design): read-only access to Passport/History, plus reminder
management, for a caregiver linked via an accepted invite code. No
edit access to the patient's Health Passport itself, and no separate
per-action audit log yet - both explicit, documented scope limits for
this first version, not oversights.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class InviteCodeOut(BaseModel):
    code: str
    expires_at: datetime


class AcceptInviteRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=12)


class CaregiverLinkOut(BaseModel):
    id: int
    status: str  # "pending" | "active" | "revoked"
    created_at: datetime
    accepted_at: datetime | None
    # Display-only identity of the OTHER party in this link - never
    # includes password_hash or anything auth-relevant, see
    # app/storage/user_store.py's get_user_by_id docstring.
    other_party_name: str | None
    other_party_email: str | None
    # The other party's user_id - when viewer_role="caregiver" (see
    # app/routes/caregivers.py's _to_link_out), this is the PATIENT's
    # user_id, which the caregiver frontend needs to actually call
    # GET /caregivers/{patient_user_id}/... Not sensitive on its own -
    # it's a derived hash, not the email/password - but only ever shown
    # to someone who already has an active or pending link to that
    # account.
    other_party_user_id: str | None
