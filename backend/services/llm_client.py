"""Shared Anthropic client construction for the NL-filter and narrative services."""

import anthropic

from backend.config import settings


def get_anthropic_client() -> anthropic.Anthropic:
    """Build an Anthropic client from the configured API key."""
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY must be set in .env to use the NL/summary endpoints")
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)
