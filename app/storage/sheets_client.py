"""
Shared Google Sheets connection, reused by passport_store.py and
user_store.py so both tabs live in the same spreadsheet and the
service-account connection is only established once per process.
"""

import json
import logging

import gspread
from google.oauth2.service_account import Credentials

from app.config import settings

logger = logging.getLogger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_spreadsheet = None  # cached across requests within a process


def get_spreadsheet():
    """Return a cached handle to the whole spreadsheet (all tabs)."""
    global _spreadsheet
    if _spreadsheet is not None:
        return _spreadsheet

    if not settings.GOOGLE_SHEET_ID or not settings.GOOGLE_SHEETS_CREDENTIALS:
        raise RuntimeError(
            "GOOGLE_SHEET_ID and GOOGLE_SHEETS_CREDENTIALS must be set to use "
            "Sheets-backed storage."
        )

    creds_dict = json.loads(settings.GOOGLE_SHEETS_CREDENTIALS)
    credentials = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
    client = gspread.authorize(credentials)

    _spreadsheet = client.open_by_key(settings.GOOGLE_SHEET_ID)
    return _spreadsheet


def get_or_create_worksheet(title: str, header: list[str]):
    """
    Return the worksheet with this exact tab name, creating it (with the
    given header row) if it doesn't exist yet. Keeps passport_store and
    user_store from needing any manual spreadsheet setup beyond sharing
    it with the service account once.
    """
    spreadsheet = get_spreadsheet()
    try:
        worksheet = spreadsheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(header))
        worksheet.update("A1", [header])
        return worksheet

    existing_header = worksheet.row_values(1)
    if existing_header != header:
        worksheet.update("A1", [header])
    return worksheet
