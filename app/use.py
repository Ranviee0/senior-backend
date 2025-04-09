import pickle
import pandas as pd

# Step 1: Load the saved model
with open("land_price_model.pkl", "rb") as f:
    model = pickle.load(f)

# Step 2: Prepare sample input data (must match the training features!)
sample_data = pd.DataFrame([{
    "land_size": 900,
    "latitude": 13.7500,
    "longitude": 100.5500,
    "distance_bts": 1.2,
    "distance_mrt": 0.9
}])

# Step 3: Make prediction
predicted_price = model.predict(sample_data)

print(f"💰 Predicted price per sqm: {predicted_price[0]:,.2f} THB")
