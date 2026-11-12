"""Command registry and intent dispatcher for HIMSETU.

Provides command registration, intent routing, permission enforcement, and structured results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from himsetu.permissions import PermissionManager, PermissionLevel, HimSetuPermissionError


@dataclass
class CommandResult:
    """Structured result returned by command handlers and intent dispatcher."""

    success: bool
    intent: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class Command:
    """Metadata and handler signature for a registered command/intent."""

    name: str
    handler: Callable[[Dict[str, Any]], CommandResult]
    description: str
    action_key: str
    required_permission: PermissionLevel = PermissionLevel.READ_ONLY


class CommandRegistry:
    """Registry for storing and retrieving commands."""

    def __init__(self):
        self._commands: Dict[str, Command] = {}

    def register(
        self,
        name: str,
        handler: Callable[[Dict[str, Any]], CommandResult],
        description: str = "",
        action_key: Optional[str] = None,
        required_permission: PermissionLevel = PermissionLevel.READ_ONLY,
    ) -> None:
        """Register a command by name."""
        cmd_name = name.strip().lower()
        if cmd_name.startswith("/"):
            cmd_name = cmd_name[1:]
        key = action_key or f"command.{cmd_name}"
        self._commands[cmd_name] = Command(
            name=cmd_name,
            handler=handler,
            description=description,
            action_key=key,
            required_permission=required_permission,
        )

    def unregister(self, name: str) -> bool:
        """Unregister a command by name. Returns True if removed."""
        cmd_name = name.strip().lower()
        if cmd_name.startswith("/"):
            cmd_name = cmd_name[1:]
        return self._commands.pop(cmd_name, None) is not None

    def get(self, name: str) -> Optional[Command]:
        """Safely retrieve a command by name."""
        clean_name = name.strip().lower()
        if clean_name.startswith("/"):
            clean_name = clean_name[1:]
        return self._commands.get(clean_name)

    def list_commands(self) -> Dict[str, Command]:
        """Return shallow copy of all registered commands."""
        return dict(self._commands)


class IntentDispatcher:
    """Parses user input, checks permissions, and dispatches intents to registered command handlers."""

    def __init__(self, registry: CommandRegistry, permission_manager: PermissionManager):
        self.registry = registry
        self.permission_manager = permission_manager

    def parse_input(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Parse raw string input into (intent_name, kwargs)."""
        clean_text = text.strip()
        if not clean_text:
            return "", {}

        # Handle leading slash if present (e.g. /help -> help)
        if clean_text.startswith("/"):
            clean_text = clean_text[1:]

        parts = clean_text.split(maxsplit=1)
        intent = parts[0].lower()
        arg_str = parts[1] if len(parts) > 1 else ""

        kwargs: Dict[str, Any] = {}
        if arg_str:
            kwargs["raw_args"] = arg_str

        return intent, kwargs

    def dispatch(
        self,
        text: str,
        user_permission: Optional[PermissionLevel | str] = None,
    ) -> CommandResult:
        """Parse, authorize, and execute command for input string."""
        intent, kwargs = self.parse_input(text)

        if not intent:
            return CommandResult(
                success=False,
                intent="",
                message="Empty command provided.",
                error="EMPTY_INPUT",
            )

        cmd = self.registry.get(intent)
        if not cmd:
            return CommandResult(
                success=False,
                intent=intent,
                message=f"Unknown command: '{intent}'. Type '/help' or 'help' for available commands.",
                error="UNKNOWN_COMMAND",
            )

        # Check permissions
        try:
            self.permission_manager.authorize(cmd.action_key, current_level=user_permission)
        except HimSetuPermissionError as exc:
            return CommandResult(
                success=False,
                intent=intent,
                message=str(exc),
                error="PERMISSION_DENIED",
            )

        # Execute handler safely
        try:
            result = cmd.handler(kwargs)
            return result
        except Exception as exc:
            return CommandResult(
                success=False,
                intent=intent,
                message=f"Execution error in command '{intent}': {exc}",
                error="EXECUTION_ERROR",
            )
