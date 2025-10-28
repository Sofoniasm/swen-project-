"""
Tests for Cost Optimization
"""

import unittest
from cloud_backbone.cost import CostOptimizer, Resource, ResourceType


class TestResource(unittest.TestCase):
    
    def test_resource_creation(self):
        """Test creating a resource"""
        resource = Resource("test-1", ResourceType.COMPUTE, 0.5, 0.3)
        self.assertEqual(resource.resource_id, "test-1")
        self.assertEqual(resource.resource_type, ResourceType.COMPUTE)
        self.assertEqual(resource.cost_per_hour, 0.5)
        self.assertEqual(resource.utilization, 0.3)
    
    def test_cost_calculations(self):
        """Test cost calculation methods"""
        resource = Resource("test-1", ResourceType.COMPUTE, 1.0, 0.5)
        
        self.assertEqual(resource.get_daily_cost(), 24.0)
        self.assertEqual(resource.get_monthly_cost(), 720.0)
    
    def test_is_underutilized(self):
        """Test underutilization detection"""
        underutilized = Resource("test-1", ResourceType.COMPUTE, 1.0, 0.1)
        normal = Resource("test-2", ResourceType.COMPUTE, 1.0, 0.5)
        
        self.assertTrue(underutilized.is_underutilized(0.2))
        self.assertFalse(normal.is_underutilized(0.2))


class TestCostOptimizer(unittest.TestCase):
    
    def setUp(self):
        self.optimizer = CostOptimizer()
    
    def test_register_resource(self):
        """Test registering a resource"""
        resource = Resource("test-1", ResourceType.COMPUTE, 0.5, 0.3)
        self.optimizer.register_resource(resource)
        self.assertEqual(len(self.optimizer.resources), 1)
    
    def test_get_total_cost(self):
        """Test calculating total cost"""
        self.optimizer.register_resource(
            Resource("test-1", ResourceType.COMPUTE, 1.0, 0.5)
        )
        self.optimizer.register_resource(
            Resource("test-2", ResourceType.STORAGE, 0.5, 0.8)
        )
        
        costs = self.optimizer.get_total_cost()
        self.assertEqual(costs['hourly'], 1.5)
        self.assertEqual(costs['daily'], 36.0)
        self.assertEqual(costs['monthly'], 1080.0)
        self.assertEqual(costs['resources_count'], 2)
    
    def test_find_underutilized_resources(self):
        """Test finding underutilized resources"""
        self.optimizer.register_resource(
            Resource("underutilized", ResourceType.COMPUTE, 1.0, 0.1)
        )
        self.optimizer.register_resource(
            Resource("normal", ResourceType.COMPUTE, 1.0, 0.5)
        )
        
        underutilized = self.optimizer.find_underutilized_resources(0.2)
        self.assertEqual(len(underutilized), 1)
        self.assertEqual(underutilized[0].resource_id, "underutilized")
    
    def test_find_idle_resources(self):
        """Test finding idle resources"""
        self.optimizer.register_resource(
            Resource("idle", ResourceType.COMPUTE, 1.0, 0.0)
        )
        self.optimizer.register_resource(
            Resource("active", ResourceType.COMPUTE, 1.0, 0.5)
        )
        
        idle = self.optimizer.find_idle_resources()
        self.assertEqual(len(idle), 1)
        self.assertEqual(idle[0].resource_id, "idle")
    
    def test_get_optimization_recommendations(self):
        """Test getting optimization recommendations"""
        # Add idle resource
        self.optimizer.register_resource(
            Resource("idle", ResourceType.COMPUTE, 1.0, 0.0)
        )
        # Add underutilized resource
        self.optimizer.register_resource(
            Resource("underutilized", ResourceType.COMPUTE, 1.0, 0.2)
        )
        # Add normal resource
        self.optimizer.register_resource(
            Resource("normal", ResourceType.COMPUTE, 1.0, 0.8)
        )
        
        recommendations = self.optimizer.get_optimization_recommendations()
        
        # Should have 2 recommendations: terminate idle, downsize underutilized
        self.assertEqual(len(recommendations), 2)
        
        # Check that we have both types
        types = [r['type'] for r in recommendations]
        self.assertIn('terminate', types)
        self.assertIn('downsize', types)
    
    def test_apply_optimization(self):
        """Test applying optimization"""
        resource = Resource("test", ResourceType.COMPUTE, 1.0, 0.0)
        self.optimizer.register_resource(resource)
        
        recommendation = {
            "type": "terminate",
            "resource_id": "test",
            "resource_type": "compute"
        }
        
        initial_count = len(self.optimizer.resources)
        result = self.optimizer.apply_optimization(recommendation)
        
        self.assertTrue(result['success'])
        self.assertEqual(len(self.optimizer.resources), initial_count - 1)
        self.assertGreater(self.optimizer.savings, 0)


if __name__ == '__main__':
    unittest.main()
