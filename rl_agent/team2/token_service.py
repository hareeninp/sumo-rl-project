"""
token_service.py - Verification Token Generator

Generates secure random verification tokens for emergency requests using Python's
secrets standard library.
"""

import secrets


def generate_verification_token() -> str:
    """
    Generates a secure, random verification token string.

    Returns:
        URL-safe random token string.
    """
    return secrets.token_urlsafe(16)
