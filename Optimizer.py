import boto3
import boto3.session
from datetime import datetime, timezone, timedelta

cloudwatch = boto3.client(
    'cloudwatch',
    region_name='ap-south-2',
    config=boto3.session.Config(
        connect_timeout=3,
        read_timeout=3,
        retries={'max_attempts': 0}
    )
)
INSTANCE_ID = 'i-06fc40f23fcfd836d'
CPU_THRESHOLD = 10.0
COST_PER_HOUR = 0.0116

def get_cpu_usage():
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[{'Name': 'InstanceId', 'Value': INSTANCE_ID}],
        StartTime=datetime.now(timezone.utc) - timedelta(hours=24),
        EndTime=datetime.now(timezone.utc),
        Period=3600,
        Statistics=['Average']
    )
    
    print(f"Raw response: {response['Datapoints']}")
    
    datapoints = response['Datapoints']
    if not datapoints:
        return None
    
    avg_cpu = sum(d['Average'] for d in datapoints) / len(datapoints)
    return round(avg_cpu, 4)

def calculate_waste(idle_minutes):
    waste = (idle_minutes / 60) * COST_PER_HOUR
    return round(waste, 6)

def classify_priority(waste_cost):
    if waste_cost < 0.01:
        return 'LOW'
    elif waste_cost < 0.05:
        return 'MEDIUM'
    else:
        return 'HIGH'

def check_idle():
    cpu = get_cpu_usage()
    
    if cpu is None:
        print("No data available yet")
        return
    
    print(f"Current CPU: {cpu}%")
    
    if cpu < CPU_THRESHOLD:
        idle_minutes = 15
        waste = calculate_waste(idle_minutes)
        priority = classify_priority(waste)
        
        print(f"Status: IDLE")
        print(f"Cost being wasted: ${waste}/15mins")
        print(f"Priority: {priority}")
        print(f"Action: Sending alert...")
        
        if priority == 'HIGH':
            print("WARNING: High waste detected! Stopping in 5 minutes unless cancelled.")
        elif priority == 'MEDIUM':
            print("WARNING: Medium waste detected! Stopping in 10 minutes unless cancelled.")
        else:
            print("INFO: Low waste. Monitoring continues. Will stop after 30 mins.")
    else:
        print(f"Status: ACTIVE — no action needed")

check_idle()