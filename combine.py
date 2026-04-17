import pickle
import datetime

# ── Original Constants ─────────────────────────────────────────────────────
IDLE_CPU_THRESHOLD = 10
HIGH_WASTE_THRESHOLD = 100
MEDIUM_WASTE_THRESHOLD = 50
LOW_WASTE_CYCLES_BEFORE_WARN = 5
OVERPROVISION_THRESHOLD = 0.40

INSTANCE_MAP = {
    (8, 32): {
        "current": "t2.2xlarge",
        "recommended": "t2.large",
        "current_cost": 2400,
        "recommended_cost": 1200
    },
    (4, 16): {
        "current": "t2.xlarge",
        "recommended": "t2.medium",
        "current_cost": 1200,
        "recommended_cost": 600
    },
    (2, 8): {
        "current": "t2.large",
        "recommended": "t2.small",
        "current_cost": 600,
        "recommended_cost": 300
    },
    (1, 4): {
        "current": "t2.medium",
        "recommended": "t2.micro",
        "current_cost": 300,
        "recommended_cost": 120
    },
}

# ── Load ML Model ──────────────────────────────────────────────────────────
try:
    with open('ml_model.pkl', 'rb') as f:
        ml_model = pickle.load(f)
    with open('label_encoder.pkl', 'rb') as f:
        label_encoder = pickle.load(f)
    ML_AVAILABLE = True
    print("✅ ML Model loaded successfully")
except Exception as e:
    ML_AVAILABLE = False
    print(f"⚠️  ML Model not found, using rule based logic. Reason: {e}")


# ── Idle Detection ─────────────────────────────────────────────────────────
def is_idle(cpu):
    # Simple rule based fallback
    return cpu < IDLE_CPU_THRESHOLD


def is_idle_ml(cpu, server_name):
    # ML based detection
    if ML_AVAILABLE:
        try:
            hour = datetime.datetime.now().hour
            weekday = datetime.datetime.now().weekday()
            server_num = label_encoder.transform([server_name])[0]
            prediction = ml_model.predict([[cpu, hour, weekday, server_num]])
            return prediction[0] == 1
        except Exception as e:
            print(f"⚠️  ML prediction failed, using rule based. Error: {e}")
    # Fallback to rule based
    return cpu < IDLE_CPU_THRESHOLD


# ── Waste Calculation ──────────────────────────────────────────────────────
def calculate_waste(hours, cost):
    return hours * cost


def classify_waste(waste):
    if waste >= HIGH_WASTE_THRESHOLD:
        return "high"
    elif waste >= MEDIUM_WASTE_THRESHOLD:
        return "medium"
    else:
        return "low"


# ── Over Provisioning ──────────────────────────────────────────────────────
def check_overprovisioning(actual_cpu_avg, allocated_cpu, actual_ram, allocated_ram):
    cpu_utilization = actual_cpu_avg / allocated_cpu if allocated_cpu > 0 else 0
    ram_utilization = actual_ram / allocated_ram if allocated_ram > 0 else 0

    is_over = (
        cpu_utilization < OVERPROVISION_THRESHOLD and
        ram_utilization < OVERPROVISION_THRESHOLD
    )

    instance_info = INSTANCE_MAP.get(
        (allocated_cpu, allocated_ram),
        {
            "current": f"custom-{allocated_cpu}cpu",
            "recommended": f"custom-{max(1, allocated_cpu//2)}cpu",
            "current_cost": allocated_cpu * 300,
            "recommended_cost": (allocated_cpu // 2) * 300
        }
    )

    if is_over:
        monthly_savings = instance_info["current_cost"] - instance_info["recommended_cost"]
        recommendation = (
            f"Downsize from {instance_info['current']} → {instance_info['recommended']}. "
            f"Save ₹{monthly_savings}/month."
        )
        severity = get_overprovision_severity(cpu_utilization, ram_utilization)
    else:
        monthly_savings = 0
        recommendation = f"Instance {instance_info['current']} is appropriately sized."
        severity = "ok"

    return {
        "is_overprovisioned": is_over,
        "severity": severity,
        "cpu_utilization_pct": round(cpu_utilization * 100, 1),
        "ram_utilization_pct": round(ram_utilization * 100, 1),
        "actual_cpu": actual_cpu_avg,
        "allocated_cpu": allocated_cpu,
        "actual_ram_gb": round(actual_ram, 1),
        "allocated_ram_gb": allocated_ram,
        "current_instance": instance_info["current"],
        "recommended_instance": instance_info["recommended"] if is_over else None,
        "current_monthly_cost": instance_info["current_cost"],
        "recommended_monthly_cost": instance_info["recommended_cost"] if is_over else instance_info["current_cost"],
        "estimated_monthly_savings": monthly_savings,
        "recommendation": recommendation
    }


def get_overprovision_severity(cpu_util, ram_util):
    avg_util = (cpu_util + ram_util) / 2
    if avg_util < 0.15:
        return "critical"
    elif avg_util < 0.25:
        return "high"
    else:
        return "medium"