from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import List, Optional
import os
import asyncio
from pydantic import BaseModel, Field
import random
import time


# Models for deploy requests and computed decisions
class DeployRequest(BaseModel):
    service: str = Field(..., description="Name of the service to deploy")
    cpu: float = Field(..., gt=0.0, le=10.0, description="Requested CPU units")
    memory: float = Field(..., gt=0.0, le=1024.0, description="Requested memory (MB)")
    region: Optional[str] = Field(None, description="Preferred region (optional)")
    max_latency_ms: Optional[int] = Field(None, description="Optional latency requirement in ms")


class DeployDecision(BaseModel):
    service: str
    from_provider: Optional[str] = None
    recommended_provider: str
    region: Optional[str] = None
    reason: str
    estimated_cost_per_min: float


# Simple pricing model (per-minute) for demo purposes
PRICING = {
    "aws": {
        "cpu_per_unit": 0.0025,    # $ per cpu unit per minute
        "mem_per_mb": 0.00001
    },
    "alibaba": {
        "cpu_per_unit": 0.0020,
        "mem_per_mb": 0.000009
    }
}


class PriceRequest(BaseModel):
    cpu: float = Field(..., gt=0.0)
    memory: float = Field(..., gt=0.0)
    region: Optional[str] = None
    provider: Optional[str] = None


def compute_price(provider: str, cpu: float, memory: float) -> float:
    p = PRICING.get(provider, PRICING['aws'])
    return round(cpu * p['cpu_per_unit'] + memory * p['mem_per_mb'], 6)

app = FastAPI()
# Allow local dev origins to access the API (helps when frontend and backend run on different ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

# In-memory stores (prototype)
telemetry_store: List[dict] = []
decision_store: List[dict] = []

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, message: dict):
        living = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                living.append(connection)
            except Exception:
                pass
        self.active_connections = living

manager = ConnectionManager()


async def _broadcast_demo_telemetry_loop():
    """Background task that periodically generates demo telemetry and decisions.
    This helps local dev and demo runs where no external telemetry producer exists.
    """
    services = ['fetcher','indexer','ranker','ingestor','api']
    providers = ['aws','gcp','azure','oracle']
    regions = ['us-east-1','eu-west-1','ap-south-1','us-west-2']
    while True:
        try:
            # generate a telemetry entry
            cpu = round(random.uniform(0.1, 2.0), 2)
            memory = round(random.uniform(32, 1024), 2)
            latency_ms = int(random.uniform(10, 350))
            cost_per_min = round(cpu * 0.005 + (memory/1024.0) * 0.002 + latency_ms/10000.0, 6)
            entry = {
                'timestamp': int(time.time() * 1000),
                'service': random.choice(services),
                'provider': random.choice(providers),
                'region': random.choice(regions),
                'cpu': cpu,
                'memory': memory,
                'latency_ms': latency_ms,
                'cost_per_min': cost_per_min,
            }
            telemetry_store.append(entry)
            # broadcast last 10 entries to WS clients
            try:
                await manager.broadcast({"telemetry_tail": [t for t in telemetry_store if isinstance(t, dict)][-10:]})
            except Exception:
                # ignore broadcast failures (clients may disconnect)
                pass

            # occasionally create a decision
            if random.random() < 0.25:
                decision = {
                    'service': entry['service'],
                    'from_provider': None,
                    'recommended_provider': random.choice(providers),
                    'region': entry['region'],
                    'reason': 'demo auto-decision',
                    'confidence': round(random.uniform(0.5, 0.98), 2),
                }
                decision_store.append(decision)
                try:
                    await manager.broadcast({"decisions_tail": [d for d in decision_store if isinstance(d, dict)][-10:]})
                except Exception:
                    pass

        except Exception:
            # don't let the loop die
            pass
        await asyncio.sleep(3)


@app.on_event("startup")
async def _start_demo_broadcaster():
    # start background demo broadcaster (non-blocking)
    try:
        asyncio.create_task(_broadcast_demo_telemetry_loop())
    except Exception:
        pass

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/telemetry")
async def get_telemetry():
    # return a flattened list of telemetry dicts to guard against historic nested lists
        # Return a flattened list of telemetry dicts so clients always receive an array of objects
        out = []
        for t in telemetry_store:
            if isinstance(t, dict):
                out.append(t)
            elif isinstance(t, list):
                for item in t:
                    if isinstance(item, dict):
                        out.append(item)
        return out

@app.post("/telemetry")
async def post_telemetry(req: Request):
    payload = await req.json()
    # Accept either a single telemetry dict or a list of telemetry dicts
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                telemetry_store.append(item)
    elif isinstance(payload, dict):
        telemetry_store.append(payload)
    else:
        # ignore other payload shapes
        pass

    # broadcast latest telemetry to ws clients (ensure list of dicts)
    tail = [t for t in telemetry_store if isinstance(t, dict)]
    await manager.broadcast({"telemetry_tail": tail[-10:]})
    return JSONResponse({"status": "ok"})

@app.get("/decisions")
async def get_decisions():
    # flatten any nested lists for robustness
        # Return a flattened list of decisions (filter out malformed entries)
        out = []
        for d in decision_store:
            if isinstance(d, dict):
                out.append(d)
            elif isinstance(d, list):
                for item in d:
                    if isinstance(item, dict):
                        out.append(item)
        return out

@app.post("/decisions")
async def post_decision(req: Request):
    payload = await req.json()
    # Accept list or single decision
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                decision_store.append(item)
    elif isinstance(payload, dict):
        decision_store.append(payload)
    else:
        pass

    tail = [d for d in decision_store if isinstance(d, dict)]
    await manager.broadcast({"decisions_tail": tail[-10:]})
    return JSONResponse({"status": "ok"})


@app.post("/deploy_request")
async def handle_deploy_request(req: Request):
    """Accept a deploy request, compute a simple cost-based recommendation and return it.

    Strategy:
    - Look at recent `telemetry_store` entries to estimate provider cost for the requested service/region.
    - If telemetry exists for providers, pick the provider with the lowest recent `cost_per_min`.
    - Otherwise, fall back to default static prices.
    - Append the resulting decision to `decision_store` and broadcast it to WebSocket clients.
    """
    payload = await req.json()
    try:
        dr = DeployRequest(**payload)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    # Compute average recent cost per provider for this service/region (simple heuristic)
    provider_costs = {}
    counts = {}
    for t in telemetry_store:
        # skip malformed entries (e.g., lists accidentally stored)
        if not isinstance(t, dict):
            continue
        if t.get('service') != dr.service:
            continue
        if dr.region and t.get('region') != dr.region:
            continue
        p = t.get('provider')
        c = t.get('cost_per_min')
        if p and isinstance(c, (int, float)):
            provider_costs[p] = provider_costs.get(p, 0.0) + float(c)
            counts[p] = counts.get(p, 0) + 1

    avg_cost = {}
    for p, total in provider_costs.items():
        avg_cost[p] = total / max(1, counts.get(p, 1))

    # fallback static pricing if no telemetry found
    if not avg_cost:
        avg_cost = {"aws": 0.0032, "alibaba": 0.0026}

    # choose provider with lowest estimated cost
    recommended = min(avg_cost.items(), key=lambda kv: kv[1])[0]
    est_cost = avg_cost[recommended]

    decision = DeployDecision(
        service=dr.service,
        from_provider=None,
        recommended_provider=recommended,
        region=dr.region,
        reason=f"cost-optimized (based on recent telemetry or defaults)",
        estimated_cost_per_min=round(float(est_cost), 6)
    )

    # store and broadcast
    decision_store.append(decision.dict())
    await manager.broadcast({"decisions_tail": decision_store[-10:]})

    return JSONResponse(decision.dict())


@app.post("/price")
async def price(req: Request):
    payload = await req.json()
    try:
        pr = PriceRequest(**payload)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    results = {}
    providers = [pr.provider] if pr.provider else list(PRICING.keys())
    for prov in providers:
        results[prov] = {
            "provider": prov,
            "region": pr.region,
            "cpu": pr.cpu,
            "memory": pr.memory,
            "cost_per_min": compute_price(prov, pr.cpu, pr.memory)
        }

    return JSONResponse(results)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # keep connection alive; we don't expect client messages
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/status")
async def status():
    """Return basic runtime counts for telemetry/decisions and active web socket connections.

    Useful for lightweight health/debug checks from the frontend or CI.
    """
    tcount = sum(1 for t in telemetry_store if isinstance(t, dict))
    dcount = sum(1 for d in decision_store if isinstance(d, dict))
    ws_count = len(manager.active_connections)
    return {"telemetry_count": tcount, "decisions_count": dcount, "ws_active": ws_count}

# Serve static frontend if present
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
if os.path.isdir(FRONTEND_DIST):
    app.mount('/', StaticFiles(directory=FRONTEND_DIST, html=True), name='static')

if __name__ == '__main__':
    uvicorn.run('api.main:app', host='127.0.0.1', port=8000, log_level='info')
