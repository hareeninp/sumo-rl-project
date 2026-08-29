"""
verification.py - Emergency Request Authentication & Runtime Token Verification

Provides runtime verification logic for emergency requests. Uses an in-memory
token registry (no persistent database required for hackathon prototype).
"""

import logging
from typing import Dict, Any, Set

logger = logging.getLogger(__name__)

# In-memory runtime token registry
_RUNTIME_TOKEN_REGISTRY: Set[str] = set()


def register_token(token: str) -> None:
    """
    Registers a newly generated verification token in the runtime registry.

    Args:
        token: Verification token string.
    """
    if token:
        _RUNTIME_TOKEN_REGISTRY.add(token)
        logger.info(f"[TOKEN REGISTRY] Token registered: {token[:8]}...")


def revoke_token(token: str) -> None:
    """
    Revokes a token from the runtime registry.
    """
    if token in _RUNTIME_TOKEN_REGISTRY:
        _RUNTIME_TOKEN_REGISTRY.remove(token)


def clear_token_registry() -> None:
    """
    Clears all tokens from the runtime registry (used for test resets).
    """
    _RUNTIME_TOKEN_REGISTRY.clear()


def is_token_registered(token: str) -> bool:
    """
    Checks if a token is present in the runtime registry.
    """
    return token in _RUNTIME_TOKEN_REGISTRY


def verify_emergency_request(request: Dict[str, Any]) -> bool:
    """
    Verifies that an emergency request contains a valid registered verification token.

    Args:
        request: Dictionary containing emergency request fields (must include 'verificationToken').

    Returns:
        True if the request token is valid and registered, False otherwise.
    """
    if not isinstance(request, dict):
        logger.warning("Verification FAILED: Request is not a dictionary.")
        return False

    token = request.get("verificationToken")
    if not token:
        logger.warning(f"Verification FAILED for vehicle '{request.get('vehicleId')}': Missing verificationToken.")
        return False

    if not is_token_registered(token):
        logger.warning(f"Verification FAILED for vehicle '{request.get('vehicleId')}': Invalid/Unregistered token '{token[:8]}...'.")
        return False

    logger.info(f"[VERIFICATION SUCCESS] Valid token verified for vehicle '{request.get('vehicleId')}'.")
    return True
