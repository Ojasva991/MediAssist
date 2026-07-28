"""
Disposable/throwaway email domain blocklist for signup.

Scope note (read before relying on this too heavily): this is a static
list of well-known disposable-email domains, checked at signup. It is
NOT exhaustive and NEVER will be - new throwaway-email services appear
constantly, and this list doesn't auto-update. Treat this as "blocks
the obvious, common cases," not "guarantees every account has a real
email." That stronger guarantee is what actual email verification (a
confirmation link, requiring a real email-sending service) would give -
see PROJECT_STATE.md's backlog for that as a separate, bigger decision
(needs a new email provider - Brevo/Resend, etc.) that hasn't been made
yet as of this list's addition.

If this list needs to grow, prefer adding specific domains you've
actually observed being used to sign up, over trying to import a huge
public blocklist wholesale - a giant imported list is more likely to
have false positives (blocking a legitimate small email provider) than
this project can easily audit.
"""

DISPOSABLE_EMAIL_DOMAINS: frozenset[str] = frozenset(
    {
        "mailinator.com",
        "tempmail.com",
        "temp-mail.org",
        "tempmail.net",
        "guerrillamail.com",
        "guerrillamail.info",
        "guerrillamail.biz",
        "guerrillamail.org",
        "sharklasers.com",
        "10minutemail.com",
        "10minutemail.net",
        "20minutemail.com",
        "throwawaymail.com",
        "throwaway.email",
        "yopmail.com",
        "yopmail.fr",
        "yopmail.net",
        "trashmail.com",
        "trashmail.net",
        "fakeinbox.com",
        "dispostable.com",
        "mohmal.com",
        "getnada.com",
        "maildrop.cc",
        "mailnesia.com",
        "mintemail.com",
        "mailcatch.com",
        "spamgourmet.com",
        "moakt.com",
        "emailondeck.com",
        "burnermail.io",
        "tempinbox.com",
        "discard.email",
        "mytemp.email",
        "inboxbear.com",
        "tempr.email",
        "fakemailgenerator.com",
        "harakirimail.com",
        "mailsac.com",
        "crazymailing.com",
    }
)


def is_disposable_email(email: str) -> bool:
    """
    True if the email's domain is a known disposable/throwaway provider.

    Case-insensitive. Assumes the email has already passed basic format
    validation (an "@" present) - callers (see app/models/auth.py)
    should run this after that check, not instead of it.
    """
    domain = email.strip().lower().rsplit("@", 1)[-1]
    return domain in DISPOSABLE_EMAIL_DOMAINS
