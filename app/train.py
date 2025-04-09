import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import pickle

# Step 1: Load dataset
df = pd.read_csv("sample_land_dataset.csv")

# Step 2: Define features and target
feature_cols = ["land_size", "latitude", "longitude", "distance_bts", "distance_mrt"]
X = df[feature_cols]
y = df["price_per_sqm"]

# Step 3: Split data into training and test sets (optional but good practice)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 4: Train the model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Step 5: Save the trained model to a pickle file
with open("land_price_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Model trained and saved as 'land_price_model.pkl'")
