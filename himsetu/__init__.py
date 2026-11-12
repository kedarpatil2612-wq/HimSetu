"""HIMSETU Core Engine Package.

Lightweight initialization exporting primary public API symbols.
"""

from himsetu.config import AppConfig, load_config
from himsetu.logging import setup_logger
from himsetu.permissions import PermissionManager, PermissionLevel, HimSetuPermissionError
from himsetu.commands import CommandRegistry, IntentDispatcher, CommandResult
from himsetu.engine import HimSetuEngine, EngineState

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "AppConfig",
    "load_config",
    "setup_logger",
    "PermissionManager",
    "PermissionLevel",
    "HimSetuPermissionError",
    "CommandRegistry",
    "IntentDispatcher",
    "CommandResult",
    "HimSetuEngine",
    "EngineState",
]
