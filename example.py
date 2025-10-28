#!/usr/bin/env python3
"""
Example usage of Cloud Backbone
"""

import time
from cloud_backbone.backbone import CloudBackbone
from cloud_backbone.cost import Resource, ResourceType
from cloud_backbone.health import HealthCheck


def custom_service_check():
    """Example custom health check"""
    # Simulate checking a service
    return {
        "healthy": True,
        "response_time": 0.15,
        "message": "Service responding normally"
    }


def main():
    print("=== Cloud Backbone Example ===\n")
    
    # Initialize the cloud backbone
    print("1. Initializing Cloud Backbone...")
    backbone = CloudBackbone()
    
    # Add custom health check
    print("2. Registering custom health check...")
    backbone.health_monitor.register_check(
        HealthCheck("custom_service", custom_service_check)
    )
    
    # Register some mock resources for cost tracking
    print("3. Registering resources for cost optimization...")
    
    # Active server
    backbone.cost_optimizer.register_resource(
        Resource("web-server-1", ResourceType.COMPUTE, 0.50, 0.75)
    )
    
    # Underutilized server
    backbone.cost_optimizer.register_resource(
        Resource("app-server-1", ResourceType.COMPUTE, 1.00, 0.15)
    )
    
    # Idle server
    backbone.cost_optimizer.register_resource(
        Resource("backup-server-1", ResourceType.COMPUTE, 0.75, 0.0)
    )
    
    # Storage resources
    backbone.cost_optimizer.register_resource(
        Resource("data-storage-1", ResourceType.STORAGE, 0.10, 0.60)
    )
    
    backbone.cost_optimizer.register_resource(
        Resource("archive-storage-1", ResourceType.STORAGE, 0.05, 0.05)
    )
    
    # Run initial health check
    print("\n4. Running health checks...")
    health = backbone.run_health_check_cycle()
    print(f"   Overall Status: {health['overall_status']}")
    print(f"   Checks Run: {len(health['checks'])}")
    
    # Check costs
    print("\n5. Analyzing costs...")
    costs = backbone.cost_optimizer.get_total_cost()
    print(f"   Current Monthly Cost: ${costs['monthly']:.2f}")
    print(f"   Resources Monitored: {costs['resources_count']}")
    
    # Get optimization recommendations
    print("\n6. Getting cost optimization recommendations...")
    recommendations = backbone.cost_optimizer.get_optimization_recommendations()
    print(f"   Found {len(recommendations)} optimization opportunities:")
    
    for rec in recommendations:
        print(f"   - {rec['type'].upper()}: {rec['resource_id']}")
        print(f"     Reason: {rec['reason']}")
        print(f"     Potential Savings: ${rec['potential_savings_monthly']:.2f}/month")
    
    # Apply optimizations
    print("\n7. Applying optimizations...")
    for rec in recommendations[:2]:  # Apply first 2 recommendations
        result = backbone.cost_optimizer.apply_optimization(rec)
        if result['success']:
            print(f"   ✓ Applied {rec['type']} for {rec['resource_id']}")
            print(f"     Monthly Savings: ${result['savings']:.2f}")
    
    # Show final status
    print("\n8. Final Status Report:")
    status = backbone.get_status()
    
    print(f"\n   Health:")
    print(f"   - Overall: {status['health']['overall_status']}")
    print(f"   - Healthy Checks: {len(status['health']['checks']) - status['health']['unhealthy_count']}/{len(status['health']['checks'])}")
    
    print(f"\n   Costs:")
    print(f"   - Current Monthly: ${status['costs']['monthly']:.2f}")
    print(f"   - Resources: {status['costs']['resources_count']}")
    
    print(f"\n   Savings:")
    print(f"   - Total Achieved: ${status['savings']['total_savings']:.2f}")
    print(f"   - Optimizations: {status['savings']['optimizations_count']}")
    
    print("\n=== Example Complete ===")
    print("\nTo run continuous monitoring, use: python main.py")


if __name__ == "__main__":
    main()
