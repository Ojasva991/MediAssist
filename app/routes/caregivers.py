"""
/caregivers routes - see app/storage/models.py's CaregiverLinkRecord
docstring for the full design rationale (separate accounts linked by
an invite code, not a shared login; read-only Passport/History access
plus reminder management for the caregiver; patient can revoke at any
time).

Every route that touches a specific patient's data
(GET /caregivers/{patient_user_id}/...) calls
caregiver_store.has_active_access() first - that single function is
the entire authorization boundary for this feature. If it's ever
buggy, everything downstream of it is wrong, so it deliberately does
ONE thing (checked for exactly caregiver_user_id + patient_user_id +
status="active") rather than something more clever.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user_id
from app.models.caregiver import AcceptInviteRequest, CaregiverLinkOut, InviteCodeOut
from app.models.history import AnalysisHistoryItem
from app.models.passport import HealthPassport
from app.models.reminder import ReminderCreate, ReminderOut, ReminderUpdate
from app.storage.caregiver_store import (
    CaregiverError,
    accept_invite,
    create_invite,
    has_active_access,
    list_caregivers_for_patient,
    list_patients_for_caregiver,
    revoke_link,
)
from app.storage.history_store import get_history
from app.storage.passport_store import get_passport
from app.storage.reminder_store import (
    complete_reminder,
    create_reminder,
    delete_reminder,
    get_reminder,
    list_reminders,
    update_reminder,
)
from app.storage.user_store import get_user_by_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/caregivers", tags=["Caregivers"])


def _require_access(caregiver_user_id: str, patient_user_id: str) -> None:
    if not has_active_access(caregiver_user_id, patient_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have caregiver access to this person's account.",
        )


def _to_link_out(record, viewer_role: str) -> CaregiverLinkOut:
    """viewer_role: 'patient' means show the CAREGIVER's identity to the
    patient; 'caregiver' means show the PATIENT's identity to the caregiver."""
    other_id = record.caregiver_user_id if viewer_role == "patient" else record.patient_user_id
    other = get_user_by_id(other_id) if other_id else None
    return CaregiverLinkOut(
        id=record.id,
        status=record.status,
        created_at=record.created_at,
        accepted_at=record.accepted_at,
        other_party_name=other["name"] if other else None,
        other_party_email=other["email"] if other else None,
        other_party_user_id=other_id,
    )


# --- Invite / accept / revoke -------------------------------------------------


@router.post("/invite", response_model=InviteCodeOut)
def create_invite_route(current_user_id: str = Depends(get_current_user_id)) -> InviteCodeOut:
    """The PATIENT generates a code to share with a caregiver, out of
    band (text message, in person, etc.) - see the module docstring for
    why this isn't emailed automatically."""
    record = create_invite(current_user_id)
    return InviteCodeOut(code=record.invite_code, expires_at=record.expires_at)


@router.post("/accept", response_model=CaregiverLinkOut)
def accept_invite_route(
    payload: AcceptInviteRequest, current_user_id: str = Depends(get_current_user_id)
) -> CaregiverLinkOut:
    """The CAREGIVER, logged into their own account, redeems a code a
    patient shared with them."""
    try:
        record = accept_invite(payload.code, current_user_id)
    except CaregiverError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return _to_link_out(record, viewer_role="caregiver")


@router.get("/my-caregivers", response_model=list[CaregiverLinkOut])
def list_my_caregivers(current_user_id: str = Depends(get_current_user_id)) -> list[CaregiverLinkOut]:
    """As a PATIENT: who has (or has been invited to have) access to my account."""
    return [_to_link_out(r, viewer_role="patient") for r in list_caregivers_for_patient(current_user_id)]


@router.get("/my-patients", response_model=list[CaregiverLinkOut])
def list_my_patients(current_user_id: str = Depends(get_current_user_id)) -> list[CaregiverLinkOut]:
    """As a CAREGIVER: whose accounts I currently have access to."""
    return [_to_link_out(r, viewer_role="caregiver") for r in list_patients_for_caregiver(current_user_id)]


@router.post("/{link_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
def revoke_link_route(link_id: int, current_user_id: str = Depends(get_current_user_id)) -> None:
    """Only the PATIENT who owns this link can revoke it - enforced inside
    revoke_link() itself, not just by convention here."""
    if not revoke_link(link_id, current_user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such caregiver link found for your account.",
        )


# --- Read-only patient data, for an authorized caregiver ----------------------


@router.get("/{patient_user_id}/passport", response_model=HealthPassport)
def get_patient_passport(
    patient_user_id: str, current_user_id: str = Depends(get_current_user_id)
) -> HealthPassport:
    _require_access(current_user_id, patient_user_id)
    passport = get_passport(patient_user_id)
    if passport is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This person hasn't set up a Health Passport yet.",
        )
    return passport


@router.get("/{patient_user_id}/history", response_model=list[AnalysisHistoryItem])
def get_patient_history(
    patient_user_id: str, current_user_id: str = Depends(get_current_user_id)
) -> list[AnalysisHistoryItem]:
    _require_access(current_user_id, patient_user_id)
    return get_history(patient_user_id)


# --- Reminder management, on behalf of an authorized patient -------------------


@router.get("/{patient_user_id}/reminders", response_model=list[ReminderOut])
def list_patient_reminders(
    patient_user_id: str, current_user_id: str = Depends(get_current_user_id)
) -> list[ReminderOut]:
    _require_access(current_user_id, patient_user_id)
    return list_reminders(patient_user_id)


@router.post(
    "/{patient_user_id}/reminders", response_model=ReminderOut, status_code=status.HTTP_201_CREATED
)
def create_patient_reminder(
    patient_user_id: str,
    payload: ReminderCreate,
    current_user_id: str = Depends(get_current_user_id),
) -> ReminderOut:
    _require_access(current_user_id, patient_user_id)
    return create_reminder(patient_user_id, payload.model_dump())


def _require_reminder_belongs_to_patient(reminder_id: int, patient_user_id: str):
    record = get_reminder(reminder_id)
    if record is None or record.user_id != patient_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No reminder found for this person."
        )
    return record


@router.patch("/{patient_user_id}/reminders/{reminder_id}", response_model=ReminderOut)
def update_patient_reminder(
    patient_user_id: str,
    reminder_id: int,
    payload: ReminderUpdate,
    current_user_id: str = Depends(get_current_user_id),
) -> ReminderOut:
    _require_access(current_user_id, patient_user_id)
    _require_reminder_belongs_to_patient(reminder_id, patient_user_id)
    return update_reminder(reminder_id, payload.model_dump(exclude_unset=True))


@router.post("/{patient_user_id}/reminders/{reminder_id}/complete", response_model=ReminderOut)
def complete_patient_reminder(
    patient_user_id: str, reminder_id: int, current_user_id: str = Depends(get_current_user_id)
) -> ReminderOut:
    _require_access(current_user_id, patient_user_id)
    _require_reminder_belongs_to_patient(reminder_id, patient_user_id)
    return complete_reminder(reminder_id)


@router.delete("/{patient_user_id}/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient_reminder(
    patient_user_id: str, reminder_id: int, current_user_id: str = Depends(get_current_user_id)
) -> None:
    _require_access(current_user_id, patient_user_id)
    _require_reminder_belongs_to_patient(reminder_id, patient_user_id)
    delete_reminder(reminder_id)
