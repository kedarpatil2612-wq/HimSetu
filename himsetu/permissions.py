"""Permission management and security foundation for HIMSETU.

Enforces security tiers (READ_ONLY, LOW_RISK, HIGH_RISK, ADMIN) and policy checks.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Dict, Optional, Union


class PermissionLevel(IntEnum):
    """Security tier hierarchy ordering."""

    READ_ONLY = 1
    LOW_RISK = 2
    HIGH_RISK = 3
    ADMIN = 4

    @classmethod
    def from_str(cls, level_str: str) -> PermissionLevel:
        """Convert string name to PermissionLevel enum safely."""
        cleaned = level_str.strip().upper()
        try:
            return cls[cleaned]
        except KeyError:
            raise ValueError(f"Unknown permission level: '{level_str}'. Valid levels: {[e.name for e in cls]}")


class HimSetuPermissionError(Exception):
    """Raised when an operation violates security policy or lacks necessary privileges."""

    def __init__(self, action: str, required_level: PermissionLevel, current_level: PermissionLevel):
        self.action = action
        self.required_level = required_level
        self.current_level = current_level
        super().__init__(
            f"Permission denied for action '{action}'. "
            f"Required level: {required_level.name}, Current level: {current_level.name}"
        )


class PermissionManager:
    """Manages security policies and evaluates action permission requirements."""

    def __init__(self, default_user_level: Union[PermissionLevel, str] = PermissionLevel.READ_ONLY):
        if isinstance(default_user_level, str):
            self.user_level = PermissionLevel.from_str(default_user_level)
        else:
            self.user_level = default_user_level

        # Action permission mapping registry
        self._action_requirements: Dict[str, PermissionLevel] = {
            "system.help": PermissionLevel.READ_ONLY,
            "system.status": PermissionLevel.READ_ONLY,
            "config.view": PermissionLevel.READ_ONLY,
            "system.exit": PermissionLevel.READ_ONLY,
            "file.read": PermissionLevel.READ_ONLY,
            "file.write": PermissionLevel.LOW_RISK,
            "file.delete": PermissionLevel.HIGH_RISK,
            "system.execute": PermissionLevel.HIGH_RISK,
            "vision.screen_capture": PermissionLevel.HIGH_RISK,
            "audio.microphone_listen": PermissionLevel.HIGH_RISK,
            "admin.system_control": PermissionLevel.ADMIN,
        }

    def register_action(self, action: str, required_level: Union[PermissionLevel, str]) -> None:
        """Register or override required permission level for an action."""
        if isinstance(required_level, str):
            level_enum = PermissionLevel.from_str(required_level)
        else:
            level_enum = required_level
        self._action_requirements[action] = level_enum

    def get_required_level(self, action: str) -> PermissionLevel:
        """Get required permission level for an action (defaults restrictively to HIGH_RISK)."""
        return self._action_requirements.get(action, PermissionLevel.HIGH_RISK)

    def check_permission(
        self, action: str, current_level: Optional[Union[PermissionLevel, str]] = None
    ) -> bool:
        """Check if current or specified permission level satisfies the action requirements."""
        effective_level = self.user_level
        if current_level is not None:
            if isinstance(current_level, str):
                effective_level = PermissionLevel.from_str(current_level)
            else:
                effective_level = current_level

        required = self.get_required_level(action)
        return effective_level >= required

    def authorize(
        self, action: str, current_level: Optional[Union[PermissionLevel, str]] = None
    ) -> None:
        """Enforce permission check. Raises HimSetuPermissionError if authorization fails."""
        effective_level = self.user_level
        if current_level is not None:
            if isinstance(current_level, str):
                effective_level = PermissionLevel.from_str(current_level)
            else:
                effective_level = current_level

        required = self.get_required_level(action)
        if effective_level < required:
            raise HimSetuPermissionError(action, required, effective_level)
