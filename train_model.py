import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pickle

# Load dummy data
df = pd.read_csv('server_data.csv')

# Convert server names to numbers
le = LabelEncoder()
df['server'] = le.fit_transform(df['server'])

# Features and target
X = df[['cpu', 'hour', 'weekday', 'server']]
y = df['stopped']

# Train model
model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# Save model
with open('ml_model.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

print("✅ ML Model trained and saved!")