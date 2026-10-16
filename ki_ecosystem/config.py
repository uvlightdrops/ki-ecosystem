"""
Configuration loader for ki-ecosystem meta-project.

ki-ecosystem is a coordination project - it loads minimal stack config
from config/defaults/stack.yaml without requiring ki-core to be installed.
"""

from pathlib import Path
import yaml


def load_config() -> dict:
    """Load ki-ecosystem stack configuration.
    
    Returns stack configuration from config/defaults/stack.yaml.
    This is used by stackctl for coordination and status commands.
    
    Returns:
        dict: Stack configuration with 'stack', 'logging', 'development' keys
    """
    # Use absolute path to find config file
    # __file__ is ki_ecosystem/config.py, so parent.parent is ki-ecosystem root
    ki_ecosystem_root = Path(__file__).parent.parent
    config_file = ki_ecosystem_root / "config" / "defaults" / "stack.yaml"
    
    if not config_file.exists():
        # Fallback: empty stack if config file not found
        return {
            "stack": {"services": {}},
            "logging": {"level": "INFO"},
            "development": {"debug": False},
        }
    
    with open(config_file) as f:
        config = yaml.safe_load(f) or {}
    
    # Ensure required keys exist
    config.setdefault("stack", {"services": {}})
    config.setdefault("logging", {"level": "INFO"})
    config.setdefault("development", {"debug": False})
    
    return config
