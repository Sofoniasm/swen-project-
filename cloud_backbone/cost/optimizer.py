"""
Cost Optimization Module - Monitors and optimizes cloud costs
"""

import logging
import time
from typing import Dict, List, Optional
from enum import Enum


# Constants
HOURS_PER_DAY = 24
DAYS_PER_MONTH = 30.44  # Average days per month


class ResourceType(Enum):
    """Types of cloud resources"""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"


class Resource:
    """Represents a cloud resource"""
    
    def __init__(self,
                 resource_id: str,
                 resource_type: ResourceType,
                 cost_per_hour: float,
                 utilization: float,
                 tags: Optional[Dict] = None):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.cost_per_hour = cost_per_hour
        self.utilization = utilization
        self.tags = tags or {}
        self.last_check = time.time()
        
    def get_daily_cost(self) -> float:
        """Calculate daily cost"""
        return self.cost_per_hour * HOURS_PER_DAY
    
    def get_monthly_cost(self) -> float:
        """Calculate monthly cost"""
        return self.cost_per_hour * HOURS_PER_DAY * DAYS_PER_MONTH
    
    def is_underutilized(self, threshold: float = 0.2) -> bool:
        """Check if resource is underutilized"""
        return self.utilization < threshold


class CostOptimizer:
    """Cost optimization system"""
    
    def __init__(self):
        self.resources: List[Resource] = []
        self.optimization_history: List[Dict] = []
        self.logger = logging.getLogger(__name__)
        self.savings = 0.0
        
    def register_resource(self, resource: Resource):
        """Register a resource for monitoring"""
        self.resources.append(resource)
        self.logger.info(f"Registered resource: {resource.resource_id}")
        
    def get_total_cost(self) -> Dict:
        """Calculate total costs"""
        hourly = sum(r.cost_per_hour for r in self.resources)
        daily = sum(r.get_daily_cost() for r in self.resources)
        monthly = sum(r.get_monthly_cost() for r in self.resources)
        
        return {
            "hourly": round(hourly, 2),
            "daily": round(daily, 2),
            "monthly": round(monthly, 2),
            "resources_count": len(self.resources)
        }
    
    def find_underutilized_resources(self, threshold: float = 0.2) -> List[Resource]:
        """Find underutilized resources"""
        return [r for r in self.resources if r.is_underutilized(threshold)]
    
    def find_idle_resources(self) -> List[Resource]:
        """Find completely idle resources (0% utilization)"""
        return [r for r in self.resources if r.utilization == 0]
    
    def get_optimization_recommendations(self) -> List[Dict]:
        """Get cost optimization recommendations"""
        recommendations = []
        
        # Find idle resources
        idle = self.find_idle_resources()
        for resource in idle:
            recommendations.append({
                "type": "terminate",
                "resource_id": resource.resource_id,
                "resource_type": resource.resource_type.value,
                "reason": "Resource is idle (0% utilization)",
                "potential_savings_monthly": round(resource.get_monthly_cost(), 2)
            })
        
        # Find underutilized resources
        underutilized = self.find_underutilized_resources(threshold=0.3)
        for resource in underutilized:
            if resource not in idle:  # Don't duplicate idle resources
                recommendations.append({
                    "type": "downsize",
                    "resource_id": resource.resource_id,
                    "resource_type": resource.resource_type.value,
                    "utilization": round(resource.utilization * 100, 1),
                    "reason": f"Resource underutilized ({round(resource.utilization * 100, 1)}%)",
                    "potential_savings_monthly": round(resource.get_monthly_cost() * 0.5, 2)
                })
        
        return recommendations
    
    def apply_optimization(self, recommendation: Dict) -> Dict:
        """Apply a cost optimization recommendation"""
        try:
            resource_id = recommendation["resource_id"]
            opt_type = recommendation["type"]
            
            # Find the resource
            resource = next((r for r in self.resources if r.resource_id == resource_id), None)
            if not resource:
                return {"success": False, "error": "Resource not found"}
            
            # Simulate optimization
            if opt_type == "terminate":
                self.resources.remove(resource)
                savings = resource.get_monthly_cost()
                self.savings += savings
                self.logger.info(f"Terminated resource {resource_id}, saving ${savings:.2f}/month")
            elif opt_type == "downsize":
                savings = resource.get_monthly_cost() * 0.5
                resource.cost_per_hour *= 0.5  # Simulate downsizing
                self.savings += savings
                self.logger.info(f"Downsized resource {resource_id}, saving ${savings:.2f}/month")
            
            result = {
                "success": True,
                "resource_id": resource_id,
                "optimization_type": opt_type,
                "savings": round(savings, 2),
                "timestamp": time.time()
            }
            
            self.optimization_history.append(result)
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_savings_report(self) -> Dict:
        """Get savings report"""
        return {
            "total_savings": round(self.savings, 2),
            "optimizations_count": len(self.optimization_history),
            "current_monthly_cost": self.get_total_cost()["monthly"],
            "history": self.optimization_history[-10:]  # Last 10 optimizations
        }
