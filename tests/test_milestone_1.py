"""Unit test suite for HIMSETU Milestone 1: Core Engine Foundation."""

import logging
import os
import tempfile
import unittest
from pathlib import Path

from himsetu.config import AppConfig, load_config
from himsetu.logging import setup_logger
from himsetu.permissions import PermissionManager, PermissionLevel, HimSetuPermissionError
from himsetu.commands import CommandRegistry, IntentDispatcher, CommandResult
from himsetu.engine import HimSetuEngine, EngineState


class TestMilestone1(unittest.TestCase):
    """Milestone 1 Core Engine comprehensive test suite."""

    # 1. Configuration Defaults
    def test_config_defaults(self):
        config = AppConfig()
        self.assertEqual(config.app_name, "HIMSETU")
        self.assertEqual(config.version, "0.1.0")
        self.assertEqual(config.environment, "development")
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.default_permission_level, "READ_ONLY")

    # 2. Environment-variable configuration
    def test_config_env_variables(self):
        os.environ["HIMSETU_LOG_LEVEL"] = "DEBUG"
        os.environ["HIMSETU_DEFAULT_PERMISSION_LEVEL"] = "ADMIN"
        try:
            config = load_config()
            self.assertEqual(config.log_level, "DEBUG")
            self.assertEqual(config.default_permission_level, "ADMIN")
        finally:
            os.environ.pop("HIMSETU_LOG_LEVEL", None)
            os.environ.pop("HIMSETU_DEFAULT_PERMISSION_LEVEL", None)

    # 3. YAML configuration loading
    def test_config_yaml_loading(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("app_name: TestSetu\nlog_level: WARNING\n")
            temp_path = f.name

        try:
            config = load_config(config_path=temp_path)
            self.assertEqual(config.app_name, "TestSetu")
            self.assertEqual(config.log_level, "WARNING")
        finally:
            Path(temp_path).unlink(missing_ok=True)

    # 4. Invalid configuration handling
    def test_invalid_config_handling(self):
        with self.assertRaises(ValueError):
            AppConfig(log_level="INVALID_LEVEL")

        with self.assertRaises(ValueError):
            AppConfig(default_permission_level="INVALID_PERM")

    # 5. Logger creation
    def test_logger_creation(self):
        config = AppConfig(log_level="DEBUG")
        logger = setup_logger(config=config, name="test_logger_1")
        self.assertIsNotNone(logger)
        self.assertEqual(logger.level, logging.DEBUG)

    # 6. Logger level handling
    def test_logger_level_handling(self):
        logger = setup_logger(name="test_logger_2", level="ERROR")
        self.assertEqual(logger.level, logging.ERROR)

    # 7. Duplicate logger handler prevention
    def test_duplicate_logger_handler_prevention(self):
        logger_name = "test_logger_handler_check"
        setup_logger(name=logger_name)
        setup_logger(name=logger_name)
        logger = logging.getLogger(logger_name)
        self.assertEqual(len(logger.handlers), 1)

    # 8. Permission level behavior
    def test_permission_level_hierarchy(self):
        self.assertTrue(PermissionLevel.READ_ONLY < PermissionLevel.LOW_RISK)
        self.assertTrue(PermissionLevel.LOW_RISK < PermissionLevel.HIGH_RISK)
        self.assertTrue(PermissionLevel.HIGH_RISK < PermissionLevel.ADMIN)

    # 9. Permission denial behavior
    def test_permission_denial(self):
        pm = PermissionManager(default_user_level=PermissionLevel.READ_ONLY)
        self.assertTrue(pm.check_permission("system.help"))
        self.assertFalse(pm.check_permission("system.execute"))

        with self.assertRaises(HimSetuPermissionError):
            pm.authorize("system.execute")

    # 10. Command registration
    def test_command_registration(self):
        registry = CommandRegistry()
        handler = lambda kwargs: CommandResult(success=True, intent="test", message="ok")
        registry.register("test", handler, description="Test command")
        cmd = registry.get("test")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.name, "test")
        self.assertEqual(cmd.description, "Test command")

    # 11. Command lookup
    def test_command_lookup(self):
        registry = CommandRegistry()
        handler = lambda kwargs: CommandResult(success=True, intent="ping", message="pong")
        registry.register("ping", handler)

        self.assertIsNotNone(registry.get("ping"))
        self.assertIsNotNone(registry.get("/ping"))
        self.assertIsNone(registry.get("nonexistent"))

    # 12. Unknown command handling
    def test_unknown_command_handling(self):
        registry = CommandRegistry()
        pm = PermissionManager()
        dispatcher = IntentDispatcher(registry=registry, permission_manager=pm)

        result = dispatcher.dispatch("foo_bar")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "UNKNOWN_COMMAND")

    # 13. Intent dispatch
    def test_intent_dispatch_success(self):
        registry = CommandRegistry()
        pm = PermissionManager()
        handler = lambda kwargs: CommandResult(
            success=True, intent="greet", message=f"Hello {kwargs.get('raw_args', 'World')}"
        )
        registry.register("greet", handler, action_key="file.read")
        dispatcher = IntentDispatcher(registry=registry, permission_manager=pm)

        result = dispatcher.dispatch("greet Alice")
        self.assertTrue(result.success)
        self.assertEqual(result.intent, "greet")
        self.assertEqual(result.message, "Hello Alice")

    # 14. Engine initialization
    def test_engine_initialization(self):
        engine = HimSetuEngine()
        self.assertEqual(engine.state, EngineState.INITIALIZING)
        engine.initialize()
        self.assertEqual(engine.state, EngineState.READY)

    # 15. Engine READY state
    def test_engine_ready_state(self):
        engine = HimSetuEngine()
        engine.initialize()
        self.assertEqual(engine.state, EngineState.READY)

    # 16. Engine PROCESSING state
    def test_engine_processing_state(self):
        engine = HimSetuEngine()
        engine.initialize()
        # Verify engine processes message and returns to READY state
        result = engine.process("help")
        self.assertTrue(result.success)
        self.assertEqual(engine.state, EngineState.READY)

    # 17. Engine STOPPED state
    def test_engine_stopped_state(self):
        engine = HimSetuEngine()
        engine.initialize()
        engine.shutdown()
        self.assertEqual(engine.state, EngineState.STOPPED)

    # 18. Invalid lifecycle behavior
    def test_invalid_lifecycle_behavior(self):
        engine = HimSetuEngine()
        # Processing before initialize should raise RuntimeError
        with self.assertRaises(RuntimeError):
            engine.process("help")

    # 19. Engine status
    def test_engine_status(self):
        engine = HimSetuEngine()
        engine.initialize()
        st = engine.status()
        self.assertEqual(st["app_name"], "HIMSETU")
        self.assertEqual(st["version"], "0.1.0")
        self.assertEqual(st["state"], "READY")
        self.assertGreaterEqual(st["registered_commands_count"], 4)

    # 20. Basic CLI command processing via engine
    def test_cli_command_processing(self):
        engine = HimSetuEngine()
        engine.initialize()

        res_help = engine.process("/help")
        self.assertTrue(res_help.success)
        self.assertEqual(res_help.intent, "help")

        res_status = engine.process("/status")
        self.assertTrue(res_status.success)
        self.assertEqual(res_status.intent, "status")

        res_config = engine.process("/config")
        self.assertTrue(res_config.success)
        self.assertEqual(res_config.intent, "config")


if __name__ == "__main__":
    unittest.main()
