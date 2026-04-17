from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import time
import combine

# ── P1 import ──────────────────────────────────────────────────────────────
try:
    from Optimizer import get_cpu_usage as aws_get_cpu
    AWS_AVAILABLE = True
    print("✅ AWS (optimizer1.py) loaded successfully")
except Exception as e:
    AWS_AVAILABLE = False
    print(f"⚠️  AWS not available, using dummy data for all servers. Reason: {e}")

# ── App setup ──────────────────────────────────────────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── AWS Cache — fetch once every 5 mins ────────────────────────────────────
aws_cache = {
    "cpu": None,
    "last_fetched": 0
}

# ── Server definitions ─────────────────────────────────────────────────────
servers = {
    "Server-1": {
        "id": "i-06fc40f23fcfd836d",
        "region": "ap-south-2",
        "allocated_cpu": 8,
        "allocated_ram": 32,
        "is_real_aws": True,
        "active_warning": False,
        "level": None,
        "waste": 0,
        "low_cycles": 0,
        "money_saved": 120,
        "cpu_history": [],
    },
    "Server-2": {
        "id": "i-2891xdef",
        "region": "us-east-1",
        "allocated_cpu": 4,
        "allocated_ram": 16,
        "is_real_aws": False,
        "active_warning": False,
        "level": None,
        "waste": 0,
        "low_cycles": 0,
        "money_saved": 80,
        "cpu_history": [],
    },
    "Server-3": {
        "id": "i-3754xghi",
        "region": "eu-west-1",
        "allocated_cpu": 2,
        "allocated_ram": 8,
        "is_real_aws": False,
        "active_warning": False,
        "level": None,
        "waste": 0,
        "low_cycles": 0,
        "money_saved": 200,
        "cpu_history": [],
    },
    "Server-4": {
        "id": "i-4623xjkl",
        "region": "ap-south-1",
        "allocated_cpu": 1,
        "allocated_ram": 4,
        "is_real_aws": False,
        "active_warning": False,
        "level": None,
        "waste": 0,
        "low_cycles": 0,
        "money_saved": 60,
        "cpu_history": [],
    },
}

# ── Helper: get CPU for a server ───────────────────────────────────────────
def get_cpu_for_server(state: dict) -> float:
    global aws_cache

    if state["is_real_aws"] and AWS_AVAILABLE:
        now = time.time()
        if now - aws_cache["last_fetched"] > 300 or aws_cache["cpu"] is None:
            try:
                cpu = aws_get_cpu()
                if cpu is not None:
                    aws_cache["cpu"] = float(cpu)
                    aws_cache["last_fetched"] = now
                    print(f"🌐 Fresh AWS CPU fetched: {cpu}%")
                else:
                    print("⚠️  AWS returned None, using cached/dummy value")
            except Exception as e:
                print(f"⚠️  AWS fetch failed, using cached/dummy. Error: {e}")

        if aws_cache["cpu"] is not None:
            print(f"📦 Using cached AWS CPU: {aws_cache['cpu']}%")
            return aws_cache["cpu"]

    return float(random.randint(1, 20))


# ── /servers endpoint ──────────────────────────────────────────────────────
@app.get("/servers")
def get_all_servers():
    results = []

    for name, state in servers.items():

        if state["active_warning"]:
            level = state["level"]
            countdown_map = {"low": 30, "medium": 20, "high": 10}
            results.append({
                "name": name,
                "id": state["id"],
                "region": state["region"],
                "cpu": 2,
                "status": "idle",
                "action": "Waiting for user decision...",
                "money": state["money_saved"],
                "warning": f"{level.upper()} WASTE detected",
                "level": level,
                "user_action_required": True,
                "countdown": countdown_map[level],
                "source": "aws" if state["is_real_aws"] and AWS_AVAILABLE else "simulated",
            })
            continue

        cpu   = get_cpu_for_server(state)
        hours = random.randint(5, 20)
        cost  = 10

        state["cpu_history"].append(cpu)
        if len(state["cpu_history"]) > 10:
            state["cpu_history"].pop(0)

        source_label = "aws" if state["is_real_aws"] and AWS_AVAILABLE else "simulated"

        # ── ML based idle detection ────────────────────────────────────────
        if combine1.is_idle_ml(cpu, name):
            waste = combine1.calculate_waste(hours, cost)
            level = combine1.classify_waste(waste)

            if level == "low":
                state["low_cycles"] += 1
                results.append({
                    "name": name,
                    "id": state["id"],
                    "region": state["region"],
                    "cpu": cpu,
                    "status": "idle",
                    "action": "Monitoring...",
                    "money": state["money_saved"],
                    "warning": "Low waste - monitoring",
                    "level": "low",
                    "user_action_required": False,
                    "countdown": 0,
                    "source": source_label,
                })
            else:
                state["active_warning"] = True
                state["level"] = level
                state["waste"] = waste
                results.append({
                    "name": name,
                    "id": state["id"],
                    "region": state["region"],
                    "cpu": cpu,
                    "status": "idle",
                    "action": "Waiting for user decision...",
                    "money": state["money_saved"],
                    "warning": f"{level.upper()} WASTE detected",
                    "level": level,
                    "user_action_required": True,
                    "countdown": 10 if level == "high" else 20,
                    "source": source_label,
                })
        else:
            state["low_cycles"] = 0
            results.append({
                "name": name,
                "id": state["id"],
                "region": state["region"],
                "cpu": cpu,
                "status": "normal",
                "action": "No action needed",
                "money": state["money_saved"],
                "warning": "Running normally",
                "level": "none",
                "user_action_required": False,
                "countdown": 0,
                "source": source_label,
            })

    return {"servers": results}


# ── /stop endpoint ─────────────────────────────────────────────────────────
@app.get("/stop/{server_name}")
def stop_server(server_name: str):
    state = servers.get(server_name)
    if state and state["active_warning"]:
        state["money_saved"] += state["waste"]
        state["active_warning"] = False
        state["level"] = None
        state["waste"] = 0
        return {"message": f"{server_name} stopped. Cost saved updated."}
    return {"message": "No active warning for this server."}


# ── /cancel endpoint ───────────────────────────────────────────────────────
@app.get("/cancel/{server_name}")
def cancel_server(server_name: str):
    state = servers.get(server_name)
    if state:
        state["active_warning"] = False
        state["level"] = None
        state["waste"] = 0
        return {"message": f"{server_name} kept running."}
    return {"message": "Server not found."}


# ── /overprovision endpoint ────────────────────────────────────────────────
@app.get("/overprovision")
def check_overprovision():
    results = []
    for name, state in servers.items():
        actual_cpu = random.randint(1, max(1, int(state["allocated_cpu"] * 0.2)))
        actual_ram = round(state["allocated_ram"] * random.uniform(0.05, 0.2), 1)

        result = combine.check_overprovisioning(
            actual_cpu,
            state["allocated_cpu"],
            actual_ram,
            state["allocated_ram"],
        )
        result["name"] = name
        results.append(result)

    return {"servers": results}


# ── /aws-status endpoint ───────────────────────────────────────────────────
@app.get("/aws-status")
def aws_status():
    return {
        "aws_connected": AWS_AVAILABLE,
        "real_server": "Server-1",
        "instance_id": servers["Server-1"]["id"],
        "region": servers["Server-1"]["region"],
    }


# ── /ml-status endpoint ────────────────────────────────────────────────────
@app.get("/ml-status")
def ml_status():
    return {
        "ml_connected": combine.ML_AVAILABLE,
        "model": "Random Forest Classifier",
        "trained_on": "30 days historical data",
        "features": ["cpu", "hour", "weekday", "server"],
    }