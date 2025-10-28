# Cloud Backbone - Self-Healing, Cost-Optimizing Infrastructure

A comprehensive cloud infrastructure management system that provides self-healing capabilities and cost optimization for the SWEN project.

## Features

### 🏥 Health Monitoring
- Continuous monitoring of system resources (CPU, Memory, Disk)
- Customizable health checks
- Real-time status reporting
- Alert generation for unhealthy states

### 🔧 Self-Healing
- Automatic detection and recovery from failures
- Configurable healing rules
- Cooldown periods to prevent excessive interventions
- Action history tracking

### 💰 Cost Optimization
- Resource utilization monitoring
- Identification of idle and underutilized resources
- Cost-saving recommendations
- Automated or manual optimization actions
- Savings tracking and reporting

## Installation

```bash
# Clone the repository
git clone https://github.com/Sofoniasm/swen-project-.git
cd swen-project-

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```bash
# Run with default configuration
python main.py

# Run with custom configuration
python main.py --config config.yaml

# Check status
python main.py --status
```

### Configuration

Copy the example configuration:
```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` to customize:
- Health check intervals
- Self-healing behavior
- Cost optimization thresholds
- Logging settings

## Usage Examples

### Example 1: Basic Monitoring

```python
from cloud_backbone import CloudBackbone

# Initialize with default settings
backbone = CloudBackbone()

# Start monitoring
backbone.start()
```

### Example 2: Custom Health Checks

```python
from cloud_backbone.health import HealthMonitor, HealthCheck

def check_api_health():
    # Your custom health check logic
    return {"healthy": True, "response_time": 0.5}

monitor = HealthMonitor()
monitor.register_check(HealthCheck("api", check_api_health))
```

### Example 3: Cost Tracking

```python
from cloud_backbone.cost import CostOptimizer, Resource, ResourceType

optimizer = CostOptimizer()

# Register resources
optimizer.register_resource(
    Resource("server-1", ResourceType.COMPUTE, cost_per_hour=0.5, utilization=0.3)
)

# Get recommendations
recommendations = optimizer.get_optimization_recommendations()

# Apply optimizations
for rec in recommendations:
    result = optimizer.apply_optimization(rec)
    print(f"Saved: ${result.get('savings', 0)}/month")
```

### Example 4: Self-Healing Rules

```python
from cloud_backbone.healing import SelfHealingSystem, HealingRule

healing = SelfHealingSystem()

# Define a healing rule
def high_memory_condition(health_data):
    for check in health_data.get('checks', []):
        if check['name'] == 'memory' and check['status'] == 'unhealthy':
            return True
    return False

def restart_service_action(health_data):
    # Your service restart logic
    print("Restarting service...")
    return True

rule = HealingRule(
    "memory_healing",
    high_memory_condition,
    restart_service_action,
    cooldown=300
)

healing.register_rule(rule)
```

## Architecture

```
cloud_backbone/
├── health/          # Health monitoring system
│   └── monitor.py   # Health checks and monitoring
├── healing/         # Self-healing system
│   └── self_healing.py  # Healing rules and actions
├── cost/            # Cost optimization
│   └── optimizer.py # Resource cost tracking and optimization
├── config/          # Configuration management
│   └── manager.py   # YAML config loader
└── backbone.py      # Main orchestrator
```

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Or run individual test modules:
```bash
python -m unittest tests/test_health.py
python -m unittest tests/test_healing.py
python -m unittest tests/test_cost.py
python -m unittest tests/test_config.py
```

## Configuration Options

### Health Monitoring
- `enabled`: Enable/disable health monitoring
- `check_interval`: Seconds between health checks
- `cpu_threshold`: CPU usage threshold (%)
- `memory_threshold`: Memory usage threshold (%)
- `disk_threshold`: Disk usage threshold (%)

### Self-Healing
- `enabled`: Enable/disable self-healing
- `cooldown`: Seconds between healing attempts
- `max_healing_attempts`: Maximum retry attempts

### Cost Optimization
- `enabled`: Enable/disable cost optimization
- `check_interval`: Seconds between optimization checks
- `underutilization_threshold`: Resource utilization threshold
- `auto_optimize`: Automatically apply optimizations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is part of the SWEN project.

## Support

For issues and questions, please open an issue on GitHub.