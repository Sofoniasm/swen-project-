"""
Self-Healing Module - Automatically recovers from failures
"""

import logging
import time
from typing import Dict, List, Callable, Optional
from enum import Enum


class HealingAction(Enum):
    """Types of healing actions"""
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    CLEAN_CACHE = "clean_cache"
    KILL_PROCESS = "kill_process"
    CUSTOM = "custom"


class HealingRule:
    """Defines a healing rule for a specific condition"""
    
    def __init__(self, 
                 name: str,
                 condition: Callable[[Dict], bool],
                 action: Callable[[Dict], bool],
                 cooldown: int = 300):
        self.name = name
        self.condition = condition
        self.action = action
        self.cooldown = cooldown  # seconds before rule can trigger again
        self.last_triggered = 0
        
    def can_trigger(self) -> bool:
        """Check if rule is off cooldown"""
        return time.time() - self.last_triggered > self.cooldown
    
    def should_trigger(self, health_data: Dict) -> bool:
        """Check if healing condition is met"""
        try:
            return self.condition(health_data)
        except Exception as e:
            logging.error(f"Error evaluating healing condition for {self.name}: {e}")
            return False
            
    def execute(self, health_data: Dict) -> Dict:
        """Execute the healing action"""
        self.last_triggered = time.time()
        try:
            success = self.action(health_data)
            return {
                "rule": self.name,
                "success": success,
                "timestamp": self.last_triggered
            }
        except Exception as e:
            return {
                "rule": self.name,
                "success": False,
                "error": str(e),
                "timestamp": self.last_triggered
            }


class SelfHealingSystem:
    """Self-healing system that automatically recovers from failures"""
    
    def __init__(self):
        self.rules: List[HealingRule] = []
        self.healing_history: List[Dict] = []
        self.logger = logging.getLogger(__name__)
        self.enabled = True
        
    def register_rule(self, rule: HealingRule):
        """Register a healing rule"""
        self.rules.append(rule)
        self.logger.info(f"Registered healing rule: {rule.name}")
        
    def evaluate_and_heal(self, health_data: Dict) -> List[Dict]:
        """Evaluate all rules and execute healing actions if needed"""
        if not self.enabled:
            return []
            
        actions_taken = []
        
        for rule in self.rules:
            if rule.can_trigger() and rule.should_trigger(health_data):
                self.logger.warning(f"Triggering healing rule: {rule.name}")
                result = rule.execute(health_data)
                actions_taken.append(result)
                self.healing_history.append(result)
                
                if result["success"]:
                    self.logger.info(f"Successfully executed healing action: {rule.name}")
                else:
                    self.logger.error(f"Failed to execute healing action: {rule.name}")
                    
        return actions_taken
    
    def get_healing_history(self, limit: int = 10) -> List[Dict]:
        """Get recent healing history"""
        return self.healing_history[-limit:]
    
    def enable(self):
        """Enable self-healing"""
        self.enabled = True
        self.logger.info("Self-healing enabled")
        
    def disable(self):
        """Disable self-healing"""
        self.enabled = False
        self.logger.info("Self-healing disabled")


# Example healing actions
def restart_service_action(service_name: str) -> Callable[[Dict], bool]:
    """Create a service restart action"""
    def action(health_data: Dict) -> bool:
        logging.info(f"Simulating restart of service: {service_name}")
        # In real implementation, would use subprocess or API to restart service
        return True
    return action


def scale_resources_action(scale_factor: float) -> Callable[[Dict], bool]:
    """Create a resource scaling action"""
    def action(health_data: Dict) -> bool:
        logging.info(f"Simulating resource scaling by factor: {scale_factor}")
        # In real implementation, would call cloud provider API
        return True
    return action


def clean_cache_action() -> bool:
    """Clean system cache"""
    logging.info("Simulating cache cleanup")
    # In real implementation, would clean actual caches
    return True
