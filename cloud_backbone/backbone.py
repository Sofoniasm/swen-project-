"""
Cloud Backbone - Main orchestrator
"""

import logging
import time
import schedule
from typing import Optional

from cloud_backbone.health import HealthMonitor, HealthCheck, check_cpu_health, check_memory_health, check_disk_health
from cloud_backbone.healing import SelfHealingSystem, HealingRule
from cloud_backbone.cost import CostOptimizer
from cloud_backbone.config import ConfigManager


class CloudBackbone:
    """
    Main orchestrator for the self-healing, cost-optimizing cloud backbone.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the cloud backbone"""
        self.config = ConfigManager(config_path)
        self._setup_logging()
        
        self.health_monitor = HealthMonitor()
        self.healing_system = SelfHealingSystem()
        self.cost_optimizer = CostOptimizer()
        
        self.logger = logging.getLogger(__name__)
        self.running = False
        
        # Setup default checks
        self._setup_default_health_checks()
        self._setup_default_healing_rules()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('logging.level', 'INFO')
        log_format = self.config.get('logging.format')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format=log_format
        )
        
    def _setup_default_health_checks(self):
        """Setup default health checks"""
        if self.config.get('health_monitoring.enabled'):
            self.health_monitor.register_check(
                HealthCheck("cpu", check_cpu_health)
            )
            self.health_monitor.register_check(
                HealthCheck("memory", check_memory_health)
            )
            self.health_monitor.register_check(
                HealthCheck("disk", check_disk_health)
            )
            
    def _setup_default_healing_rules(self):
        """Setup default healing rules"""
        if self.config.get('self_healing.enabled'):
            # High CPU healing rule
            def high_cpu_condition(health_data):
                for check in health_data.get('checks', []):
                    if check['name'] == 'cpu' and check['status'] == 'unhealthy':
                        return True
                return False
            
            def high_cpu_action(health_data):
                self.logger.warning("High CPU detected, initiating healing action")
                # In production, this would restart services, scale resources, etc.
                return True
            
            self.healing_system.register_rule(
                HealingRule(
                    "high_cpu_healing",
                    high_cpu_condition,
                    high_cpu_action,
                    cooldown=self.config.get('self_healing.cooldown', 300)
                )
            )
            
    def run_health_check_cycle(self):
        """Run a health check cycle"""
        self.logger.debug("Running health check cycle")
        health_data = self.health_monitor.run_all_checks()
        
        # Log health status
        if health_data['overall_status'] != 'healthy':
            self.logger.warning(f"System health: {health_data['overall_status']}")
            self.logger.warning(f"Unhealthy checks: {health_data['unhealthy_count']}")
            
            # Trigger self-healing if enabled
            if self.config.get('self_healing.enabled'):
                healing_actions = self.healing_system.evaluate_and_heal(health_data)
                if healing_actions:
                    self.logger.info(f"Executed {len(healing_actions)} healing actions")
        else:
            self.logger.debug("System health: healthy")
            
        return health_data
    
    def run_cost_optimization_cycle(self):
        """Run a cost optimization cycle"""
        self.logger.debug("Running cost optimization cycle")
        
        recommendations = self.cost_optimizer.get_optimization_recommendations()
        
        if recommendations:
            self.logger.info(f"Found {len(recommendations)} cost optimization opportunities")
            
            # Auto-optimize if enabled
            if self.config.get('cost_optimization.auto_optimize'):
                for rec in recommendations:
                    result = self.cost_optimizer.apply_optimization(rec)
                    if result['success']:
                        self.logger.info(f"Applied optimization: {rec['type']} for {rec['resource_id']}")
        
        return self.cost_optimizer.get_total_cost()
    
    def get_status(self):
        """Get current system status"""
        return {
            "health": self.health_monitor.run_all_checks(),
            "costs": self.cost_optimizer.get_total_cost(),
            "savings": self.cost_optimizer.get_savings_report(),
            "healing_history": self.healing_system.get_healing_history()
        }
    
    def start(self):
        """Start the cloud backbone monitoring"""
        self.logger.info("Starting Cloud Backbone...")
        self.running = True
        
        # Schedule health checks
        health_interval = self.config.get('health_monitoring.check_interval', 60)
        schedule.every(health_interval).seconds.do(self.run_health_check_cycle)
        
        # Schedule cost optimization checks
        cost_interval = self.config.get('cost_optimization.check_interval', 3600)
        schedule.every(cost_interval).seconds.do(self.run_cost_optimization_cycle)
        
        self.logger.info("Cloud Backbone started successfully")
        
        # Run initial checks
        self.run_health_check_cycle()
        self.run_cost_optimization_cycle()
        
        # Main loop
        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
            self.stop()
            
    def stop(self):
        """Stop the cloud backbone monitoring"""
        self.logger.info("Stopping Cloud Backbone...")
        self.running = False
        schedule.clear()
        self.logger.info("Cloud Backbone stopped")
