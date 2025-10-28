"""
Tests for Self-Healing System
"""

import unittest
import time
from cloud_backbone.healing import SelfHealingSystem, HealingRule


class TestSelfHealingSystem(unittest.TestCase):
    
    def setUp(self):
        self.healing_system = SelfHealingSystem()
    
    def test_register_rule(self):
        """Test registering a healing rule"""
        rule = HealingRule(
            "test_rule",
            lambda h: True,
            lambda h: True
        )
        self.healing_system.register_rule(rule)
        self.assertEqual(len(self.healing_system.rules), 1)
    
    def test_healing_rule_cooldown(self):
        """Test that healing rules respect cooldown"""
        rule = HealingRule(
            "test_rule",
            lambda h: True,
            lambda h: True,
            cooldown=2
        )
        
        # First trigger should work
        self.assertTrue(rule.can_trigger())
        rule.execute({})
        
        # Second trigger should be blocked by cooldown
        self.assertFalse(rule.can_trigger())
        
        # After cooldown, should work again
        time.sleep(2.1)
        self.assertTrue(rule.can_trigger())
    
    def test_evaluate_and_heal(self):
        """Test evaluating and executing healing actions"""
        executed = []
        
        def condition(health_data):
            return health_data.get('trigger', False)
        
        def action(health_data):
            executed.append(True)
            return True
        
        rule = HealingRule("test", condition, action, cooldown=0)
        self.healing_system.register_rule(rule)
        
        # Should not trigger without condition
        actions = self.healing_system.evaluate_and_heal({'trigger': False})
        self.assertEqual(len(actions), 0)
        
        # Should trigger with condition
        actions = self.healing_system.evaluate_and_heal({'trigger': True})
        self.assertEqual(len(actions), 1)
        self.assertTrue(actions[0]['success'])
    
    def test_enable_disable(self):
        """Test enabling and disabling self-healing"""
        rule = HealingRule(
            "test",
            lambda h: True,
            lambda h: True,
            cooldown=0
        )
        self.healing_system.register_rule(rule)
        
        # Should work when enabled
        actions = self.healing_system.evaluate_and_heal({})
        self.assertEqual(len(actions), 1)
        
        # Should not work when disabled
        self.healing_system.disable()
        actions = self.healing_system.evaluate_and_heal({})
        self.assertEqual(len(actions), 0)
        
        # Should work again when re-enabled
        self.healing_system.enable()
        actions = self.healing_system.evaluate_and_heal({})
        self.assertEqual(len(actions), 1)


if __name__ == '__main__':
    unittest.main()
