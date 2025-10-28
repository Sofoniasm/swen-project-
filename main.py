#!/usr/bin/env python3
"""
Main entry point for Cloud Backbone
"""

import sys
import argparse
from cloud_backbone.backbone import CloudBackbone


def main():
    parser = argparse.ArgumentParser(
        description="Self-Healing, Cost-Optimizing Cloud Backbone for SWEN"
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current status and exit'
    )
    
    args = parser.parse_args()
    
    # Initialize cloud backbone
    backbone = CloudBackbone(config_path=args.config)
    
    if args.status:
        # Show status and exit
        status = backbone.get_status()
        print("\n=== Cloud Backbone Status ===")
        print(f"\nHealth: {status['health']['overall_status']}")
        print(f"Total Monthly Cost: ${status['costs']['monthly']:.2f}")
        print(f"Total Savings: ${status['savings']['total_savings']:.2f}")
        print(f"Resources Monitored: {status['costs']['resources_count']}")
        sys.exit(0)
    
    # Start monitoring
    try:
        backbone.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
        backbone.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
