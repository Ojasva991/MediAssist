"""
Grant or revoke the "admin" role for a user, by email.

This is the deliberate, manual bootstrap step for the FIRST admin -
there's no other way to create one, by design (an unauthenticated
"become admin" API endpoint would be a real vulnerability). Once at
least one admin exists, further promotions can happen through the app
itself via POST /admin/users/{user_id}/role (see
app/routes/admin_users.py) - this script is specifically for the
chicken-and-egg problem of creating the first one, or for anyone who
prefers shell access over the API.

Usage:
    python -m app.scripts.grant_admin user@example.com
    python -m app.scripts.grant_admin user@example.com --revoke
"""

import argparse
import logging

from app.storage.user_store import get_user_by_email, set_role

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email", help="Email of the account to promote/demote")
    parser.add_argument(
        "--revoke", action="store_true", help="Revoke admin (set role back to 'user') instead of granting it"
    )
    args = parser.parse_args()

    user = get_user_by_email(args.email)
    if user is None:
        raise SystemExit(f"No account found for {args.email!r} - they need to sign up first.")

    new_role = "user" if args.revoke else "admin"
    if user["role"] == new_role:
        print(f"{args.email} already has role={new_role!r} - nothing to do.")
        return

    if not set_role(user["user_id"], new_role):
        raise SystemExit("Failed to update role - see logs.")

    action = "Revoked admin from" if args.revoke else "Granted admin to"
    print(f"{action} {args.email} (user_id={user['user_id']}).")


if __name__ == "__main__":
    main()
