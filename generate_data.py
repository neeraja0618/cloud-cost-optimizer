import pandas as pd
import random

data = []
for day in range(30):
    for hour in range(24):
        for server in ['Server-1', 'Server-2', 'Server-3', 'Server-4']:
            if hour >= 2 and hour <= 4:
                cpu = random.uniform(1, 5)
                stopped = 1
            elif hour >= 9 and hour <= 18:
                cpu = random.uniform(40, 90)
                stopped = 0
            else:
                cpu = random.uniform(5, 30)
                stopped = random.choice([0, 1])

            data.append([server, hour, day % 7, cpu, stopped])

df = pd.DataFrame(data, columns=['server', 'hour', 'weekday', 'cpu', 'stopped'])
df.to_csv('server_data.csv', index=False)
print("✅ Dummy data generated! 2880 rows created.")