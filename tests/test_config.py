"""
Tests for Configuration Manager
"""

import unittest
import os
import tempfile
from cloud_backbone.config import ConfigManager


class TestConfigManager(unittest.TestCase):
    
    def test_default_config(self):
        """Test that default config is loaded"""
        config = ConfigManager()
        self.assertTrue(config.get('health_monitoring.enabled'))
        self.assertEqual(config.get('health_monitoring.check_interval'), 60)
    
    def test_get_config_value(self):
        """Test getting config values"""
        config = ConfigManager()
        
        # Test nested value
        self.assertEqual(config.get('logging.level'), 'INFO')
        
        # Test with default
        self.assertEqual(config.get('nonexistent.key', 'default'), 'default')
    
    def test_set_config_value(self):
        """Test setting config values"""
        config = ConfigManager()
        
        config.set('health_monitoring.check_interval', 120)
        self.assertEqual(config.get('health_monitoring.check_interval'), 120)
    
    def test_load_and_save_config(self):
        """Test loading and saving config"""
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('health_monitoring:\n  check_interval: 90\n')
            temp_path = f.name
        
        try:
            # Load config
            config = ConfigManager(temp_path)
            self.assertEqual(config.get('health_monitoring.check_interval'), 90)
            
            # Modify and save
            config.set('health_monitoring.check_interval', 180)
            config.save_config(temp_path)
            
            # Load again to verify
            config2 = ConfigManager(temp_path)
            self.assertEqual(config2.get('health_monitoring.check_interval'), 180)
        finally:
            os.unlink(temp_path)
    
    def test_get_all_config(self):
        """Test getting all configuration"""
        config = ConfigManager()
        all_config = config.get_all()
        
        self.assertIn('health_monitoring', all_config)
        self.assertIn('self_healing', all_config)
        self.assertIn('cost_optimization', all_config)


if __name__ == '__main__':
    unittest.main()
