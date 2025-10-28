"""
Tests for Health Monitoring
"""

import unittest
from cloud_backbone.health import HealthMonitor, HealthCheck, check_cpu_health, check_memory_health, check_disk_health


class TestHealthMonitor(unittest.TestCase):
    
    def setUp(self):
        self.monitor = HealthMonitor()
    
    def test_register_check(self):
        """Test registering a health check"""
        check = HealthCheck("test", lambda: {"healthy": True})
        self.monitor.register_check(check)
        self.assertEqual(len(self.monitor.checks), 1)
    
    def test_run_all_checks_healthy(self):
        """Test running checks when all are healthy"""
        check = HealthCheck("test", lambda: {"healthy": True, "message": "OK"})
        self.monitor.register_check(check)
        
        results = self.monitor.run_all_checks()
        self.assertEqual(results['overall_status'], 'healthy')
        self.assertEqual(results['unhealthy_count'], 0)
        self.assertEqual(len(results['checks']), 1)
    
    def test_run_all_checks_unhealthy(self):
        """Test running checks when some are unhealthy"""
        healthy_check = HealthCheck("healthy", lambda: {"healthy": True})
        unhealthy_check = HealthCheck("unhealthy", lambda: {"healthy": False})
        
        self.monitor.register_check(healthy_check)
        self.monitor.register_check(unhealthy_check)
        
        results = self.monitor.run_all_checks()
        self.assertEqual(results['overall_status'], 'degraded')
        self.assertEqual(results['unhealthy_count'], 1)
    
    def test_get_unhealthy_checks(self):
        """Test getting only unhealthy checks"""
        healthy_check = HealthCheck("healthy", lambda: {"healthy": True})
        unhealthy_check = HealthCheck("unhealthy", lambda: {"healthy": False})
        
        self.monitor.register_check(healthy_check)
        self.monitor.register_check(unhealthy_check)
        
        unhealthy = self.monitor.get_unhealthy_checks()
        self.assertEqual(len(unhealthy), 1)
        self.assertEqual(unhealthy[0]['name'], 'unhealthy')


class TestDefaultHealthChecks(unittest.TestCase):
    
    def test_check_cpu_health(self):
        """Test CPU health check"""
        result = check_cpu_health()
        self.assertIn('healthy', result)
        self.assertIn('cpu_percent', result)
        self.assertIn('message', result)
    
    def test_check_memory_health(self):
        """Test memory health check"""
        result = check_memory_health()
        self.assertIn('healthy', result)
        self.assertIn('memory_percent', result)
        self.assertIn('available_gb', result)
    
    def test_check_disk_health(self):
        """Test disk health check"""
        result = check_disk_health()
        self.assertIn('healthy', result)
        self.assertIn('disk_percent', result)
        self.assertIn('free_gb', result)


if __name__ == '__main__':
    unittest.main()
