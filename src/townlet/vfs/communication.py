"""Canonical communication VFS variable definitions."""

from __future__ import annotations

from townlet.vfs.schema import VariableDef

__all__ = ["canonical_l6_message_variables"]


def canonical_l6_message_variables(message_token_dims: int) -> tuple[VariableDef, ...]:
    """Return canonical L6 message-buffer variables."""
    if message_token_dims <= 0:
        raise ValueError("message_token_dims must be positive")

    return (
        VariableDef(
            id="recent_message_tokens",
            scope="message",
            type="message_token",
            dims=message_token_dims,
            lifetime="episode",
            readable_by=["agent", "social_model"],
            writable_by=["vtc"],
            default=[0.0 for _ in range(message_token_dims)],
            description="Recent per-agent message-token payloads in message-slot order.",
        ),
    )
