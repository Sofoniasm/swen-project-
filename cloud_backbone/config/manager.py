"""
Configuration Manager - Manages system configuration
"""

import yaml
import logging
from typing import Dict, Any, Optional
import os


class ConfigManager:
    """Manages configuration for the cloud backbone"""
    
    DEFAULT_CONFIG = {
        "health_monitoring": {
            "enabled": True,
            "check_interval": 60,  # seconds
            "cpu_threshold": 80,
            "memory_threshold": 85,
            "disk_threshold": 90
        },
        "self_healing": {
            "enabled": True,
            "cooldown": 300,  # seconds
            "max_healing_attempts": 3
        },
        "cost_optimization": {
            "enabled": True,
            "check_interval": 3600,  # seconds
            "underutilization_threshold": 0.2,
            "auto_optimize": False
        },
        "logging": {
            "level": "INFO",
            "file": "cloud_backbone.log",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = self.DEFAULT_CONFIG.copy()
        self.logger = logging.getLogger(__name__)
        
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    self._merge_config(user_config)
            self.logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load config from {config_path}: {e}")
            
    def _merge_config(self, user_config: Dict):
        """Merge user config with defaults"""
        for key, value in user_config.items():
            if key in self.config and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
                
    def save_config(self, config_path: Optional[str] = None):
        """Save current configuration to YAML file"""
        path = config_path or self.config_path
        if not path:
            raise ValueError("No config path specified")
            
        try:
            with open(path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            self.logger.info(f"Saved configuration to {path}")
        except Exception as e:
            self.logger.error(f"Failed to save config to {path}: {e}")
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        
    def get_all(self) -> Dict:
        """Get all configuration"""
        return self.config.copy()
