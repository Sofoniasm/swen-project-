"""
Health Monitor - Monitors system and service health
"""

import logging
import time
from typing import Dict, List, Callable
import psutil


class HealthCheck:
    """Represents a single health check"""
    
    def __init__(self, name: str, check_func: Callable, threshold: float = 0.8):
        self.name = name
        self.check_func = check_func
        self.threshold = threshold
        self.status = "unknown"
        self.last_check_time = None
        
    def execute(self) -> Dict:
        """Execute the health check"""
        try:
            result = self.check_func()
            self.status = "healthy" if result["healthy"] else "unhealthy"
            self.last_check_time = time.time()
            return {
                "name": self.name,
                "status": self.status,
                "details": result,
                "timestamp": self.last_check_time
            }
        except Exception as e:
            self.status = "error"
            self.last_check_time = time.time()
            return {
                "name": self.name,
                "status": "error",
                "error": str(e),
                "timestamp": self.last_check_time
            }


class HealthMonitor:
    """Monitors overall system health"""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.logger = logging.getLogger(__name__)
        
    def register_check(self, check: HealthCheck):
        """Register a health check"""
        self.checks.append(check)
        self.logger.info(f"Registered health check: {check.name}")
        
    def run_all_checks(self) -> Dict:
        """Run all registered health checks"""
        results = []
        for check in self.checks:
            result = check.execute()
            results.append(result)
            
        # Determine overall health
        unhealthy_count = sum(1 for r in results if r["status"] != "healthy")
        overall_status = "healthy" if unhealthy_count == 0 else "degraded"
        
        return {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": time.time(),
            "unhealthy_count": unhealthy_count
        }
    
    def get_unhealthy_checks(self) -> List[Dict]:
        """Get list of unhealthy checks"""
        results = self.run_all_checks()
        return [c for c in results["checks"] if c["status"] != "healthy"]


# Default health check functions
def check_cpu_health() -> Dict:
    """Check CPU utilization"""
    cpu_percent = psutil.cpu_percent(interval=1)
    return {
        "healthy": cpu_percent < 80,
        "cpu_percent": cpu_percent,
        "message": f"CPU at {cpu_percent}%"
    }


def check_memory_health() -> Dict:
    """Check memory utilization"""
    memory = psutil.virtual_memory()
    return {
        "healthy": memory.percent < 85,
        "memory_percent": memory.percent,
        "available_gb": round(memory.available / (1024**3), 2),
        "message": f"Memory at {memory.percent}%"
    }


def check_disk_health() -> Dict:
    """Check disk utilization"""
    disk = psutil.disk_usage('/')
    return {
        "healthy": disk.percent < 90,
        "disk_percent": disk.percent,
        "free_gb": round(disk.free / (1024**3), 2),
        "message": f"Disk at {disk.percent}%"
    }
