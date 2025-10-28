#!/usr/bin/env python3
"""Simple simulator that emits telemetry and decisions to backend via HTTP.

Usage:
  python -m ai_engine.simulator --mode http --interval 5 --backend http://127.0.0.1:8000
"""
import argparse
import random
import time
import requests
from datetime import datetime, timezone

SERVICES = ["fetcher", "indexer", "ranker"]
PROVIDERS = ["aws", "alibaba"]
REGIONS = ["us-east-1", "eu-west-1", "cn-hangzhou"]


def make_telemetry():
    return {
        "service": random.choice(SERVICES),
        "provider": random.choice(PROVIDERS),
        "region": random.choice(REGIONS),
        "cpu": round(random.random(), 2),
        "memory": round(random.random(), 2),
        "latency_ms": random.randint(50, 400),
        "cost_per_min": round(random.uniform(0.001, 0.005), 6),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def simple_decision(telemetry):
    # trivial rule: choose the provider with lower recent cost_per_min
    recommended = telemetry.get('provider')
    return {
        "service": telemetry.get('service'),
        "current_provider": telemetry.get('provider'),
        "recommended_provider": recommended,
        "region": telemetry.get('region'),
        "reason": "rule: keep"
    }


def post_json(url, path, payload):
    try:
        resp = requests.post(url.rstrip('/') + path, json=payload, timeout=5)
        return resp.ok
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['http'], default='http')
    parser.add_argument('--interval', type=float, default=5.0)
    parser.add_argument('--backend', default='http://127.0.0.1:8000')
    args = parser.parse_args()

    print(f"Starting simulator for mode={args.mode} interval={args.interval}s backend={args.backend}")
    try:
        while True:
            t = make_telemetry()
            post_json(args.backend, '/telemetry', t)
            d = simple_decision(t)
            post_json(args.backend, '/decisions', d)
            print('emitted telemetry:', t)
            print('decision:', d)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print('stopping simulator')


if __name__ == '__main__':
    main()
