#!/usr/bin/env python3
"""Small helper to POST a deploy_request to the local backend and print the JSON response.

Usage:
  python scripts/post_deploy_request.py --service indexer --cpu 0.5 --memory 128 --region eu-west-1
"""
import argparse
import json
import sys

import requests


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--backend", default="http://127.0.0.1:8000", help="Backend base URL")
    p.add_argument("--service", required=True)
    p.add_argument("--cpu", type=float, required=True)
    p.add_argument("--memory", type=float, required=True)
    p.add_argument("--region", default=None)
    p.add_argument("--max-latency-ms", type=int, default=None)
    args = p.parse_args()

    payload = {
        "service": args.service,
        "cpu": args.cpu,
        "memory": args.memory,
    }
    if args.region:
        payload["region"] = args.region
    if args.max_latency_ms is not None:
        payload["max_latency_ms"] = args.max_latency_ms

    url = args.backend.rstrip("/") + "/deploy_request"
    try:
        resp = requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Request failed:", e, file=sys.stderr)
        sys.exit(2)

    try:
        j = resp.json()
        print(json.dumps(j, indent=2))
    except Exception:
        print("Non-JSON response:\n", resp.text)
        sys.exit(3)


if __name__ == '__main__':
    main()
