"""Core engine orchestrator for HIMSETU.

Coordinates configuration, logging, security permissions, command registry,
intent dispatching, and engine lifecycle state management.
"""

from __future__ import annotations

from enum import Enum
import logging
import time
from typing import Any, Dict, Optional, Union

from himsetu.config import AppConfig, load_config
from himsetu.logging import setup_logger
from himsetu.permissions import PermissionManager, PermissionLevel
from himsetu.commands import CommandRegistry, IntentDispatcher, CommandResult


class EngineState(Enum):
    """Lifecycle states of HimSetuEngine."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    PROCESSING = "PROCESSING"
    STOPPED = "STOPPED"


class HimSetuEngine:
    """Primary orchestrator for HIMSETU Core Engine."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config: AppConfig = config or load_config()
        self.state: EngineState = EngineState.INITIALIZING
        self.logger: logging.Logger = setup_logger(config=self.config, name="himsetu.engine")
        self.permission_manager: PermissionManager = PermissionManager(
            default_user_level=self.config.default_permission_level
        )
        self.command_registry: CommandRegistry = CommandRegistry()
        self.intent_dispatcher: IntentDispatcher = IntentDispatcher(
            registry=self.command_registry,
            permission_manager=self.permission_manager,
        )
        self.start_time: float = time.time()
        self._processed_count: int = 0

    def initialize(self) -> None:
        """Initialize engine components, register built-in commands, and set state to READY."""
        if self.state not in (EngineState.INITIALIZING, EngineState.STOPPED):
            raise RuntimeError(f"Cannot initialize engine from state '{self.state.value}'.")

        self.logger.info("Initializing HIMSETU Core Engine v%s...", self.config.version)

        # Register built-in commands
        self._register_builtin_commands()

        self.state = EngineState.READY
        self.logger.info("HIMSETU Core Engine initialized successfully and READY.")

    def _register_builtin_commands(self) -> None:
        """Register Milestone 1 built-in command handlers."""
        # /help command
        def help_handler(kwargs: Dict[str, Any]) -> CommandResult:
            cmds = self.command_registry.list_commands()
            lines = ["Available Commands:"]
            for name, cmd in sorted(cmds.items()):
                lines.append(f"  /{name:<10} - {cmd.description}")
            return CommandResult(
                success=True,
                intent="help",
                message="\n".join(lines),
                data={"commands": {k: v.description for k, v in cmds.items()}},
            )

        self.command_registry.register(
            name="help",
            handler=help_handler,
            description="List available system commands",
            action_key="system.help",
            required_permission=PermissionLevel.READ_ONLY,
        )

        # /status command
        def status_handler(kwargs: Dict[str, Any]) -> CommandResult:
            st = self.status()
            lines = [
                f"Application: {st['app_name']} v{st['version']}",
                f"Engine State: {st['state']}",
                f"Uptime: {st['uptime_seconds']:.2f}s",
                f"Processed Messages: {st['processed_count']}",
                f"Registered Commands: {st['registered_commands_count']}",
            ]
            return CommandResult(
                success=True,
                intent="status",
                message="\n".join(lines),
                data=st,
            )

        self.command_registry.register(
            name="status",
            handler=status_handler,
            description="Display engine lifecycle and system status",
            action_key="system.status",
            required_permission=PermissionLevel.READ_ONLY,
        )

        # /config command
        def config_handler(kwargs: Dict[str, Any]) -> CommandResult:
            safe_cfg = self.config.get_safe_dict()
            lines = ["Current Configuration:"]
            for k, v in safe_cfg.items():
                lines.append(f"  {k}: {v}")
            return CommandResult(
                success=True,
                intent="config",
                message="\n".join(lines),
                data=safe_cfg,
            )

        self.command_registry.register(
            name="config",
            handler=config_handler,
            description="View active application configuration (excluding secrets)",
            action_key="config.view",
            required_permission=PermissionLevel.READ_ONLY,
        )

        # /exit command
        def exit_handler(kwargs: Dict[str, Any]) -> CommandResult:
            return CommandResult(
                success=True,
                intent="exit",
                message="Shutting down HIMSETU...",
                data={"action": "exit"},
            )

        self.command_registry.register(
            name="exit",
            handler=exit_handler,
            description="Exit interactive HIMSETU CLI session",
            action_key="system.exit",
            required_permission=PermissionLevel.READ_ONLY,
        )

    def process(
        self,
        input_text: str,
        user_permission: Optional[Union[PermissionLevel, str]] = None,
    ) -> CommandResult:
        """Process user input string through intent dispatcher."""
        if self.state != EngineState.READY:
            raise RuntimeError(f"Engine is not READY to process requests (current state: '{self.state.value}').")

        self.state = EngineState.PROCESSING
        try:
            self._processed_count += 1
            result = self.intent_dispatcher.dispatch(input_text, user_permission=user_permission)
            return result
        finally:
            if self.state == EngineState.PROCESSING:
                self.state = EngineState.READY

    def status(self) -> Dict[str, Any]:
        """Return engine state and runtime metrics snapshot."""
        return {
            "app_name": self.config.app_name,
            "version": self.config.version,
            "environment": self.config.environment,
            "state": self.state.value,
            "uptime_seconds": round(time.time() - self.start_time, 2),
            "processed_count": self._processed_count,
            "registered_commands_count": len(self.command_registry.list_commands()),
            "default_permission_level": self.permission_manager.user_level.name,
        }

    def shutdown(self) -> None:
        """Shutdown engine and set state to STOPPED."""
        if self.state == EngineState.STOPPED:
            return

        self.logger.info("Shutting down HIMSETU Core Engine...")
        self.state = EngineState.STOPPED
        self.logger.info("HIMSETU Core Engine stopped.")
