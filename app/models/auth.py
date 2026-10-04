"""Backward-compatible export. Prefer `from app.models import User`."""

from app.models.user import User

__all__ = ["User"]
