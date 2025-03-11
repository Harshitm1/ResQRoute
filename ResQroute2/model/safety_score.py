import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error
import joblib

# ----------------------------------------
# ✅ Load data
# ----------------------------------------
data = pd.read_csv('/Users/harshitmittal/Downloads/ResQroute2/data/safety_data.csv')

# Map Road_Type to numeric values
data['Road_Type'] = data['Road_Type'].map({
    'Highway': 3,
    'City Road': 2,
    'Local Road': 1
})

# Use ALL columns as input (since Safety_Score doesn't exist)
X = data

# Generate Random Safety Scores temporarily (since CSV has no Safety Score)
y = np.random.uniform(low=5, high=100, size=len(X))

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ----------------------------------------
# ✅ Hyperparameter Tuning with GridSearchCV
# ----------------------------------------
rf = RandomForestRegressor(random_state=42)

param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [10, 20, 30],
    'min_samples_split': [2, 5, 10]
}

grid_search = GridSearchCV(estimator=rf, param_grid=param_grid, 
                           cv=3, n_jobs=-1, verbose=2)

grid_search.fit(X_train_scaled, y_train)

# ✅ Get Best Model
best_rf_model = grid_search.best_estimator_

# ✅ Predict
y_pred = best_rf_model.predict(X_test_scaled)

# ✅ Evaluate
mse = mean_squared_error(y_test, y_pred)
print(f"✅ Model trained successfully with MSE: {mse:.2f}")

# ✅ Save the model
joblib.dump(best_rf_model, '/Users/harshitmittal/Downloads/ResQroute2/model/random_forest_model.pkl')
joblib.dump(scaler, '/Users/harshitmittal/Downloads/ResQroute2/model/scaler.pkl')

print("✅ Best Model and Scaler saved successfully.")

# ----------------------------------------
# ✅ Function to Predict Safety Score
# ----------------------------------------
def predict_safety_score(input_data):
    # Map Road_Type to numeric values
    input_data['Road_Type'] = input_data['Road_Type'].map({
        'Highway': 3,
        'City Road': 2,
        'Local Road': 1
    })

    # Scale the input data
    input_data_scaled = scaler.transform(input_data)

    # Predict Safety Score
    predicted_score = best_rf_model.predict(input_data_scaled)
    return predicted_score

# ----------------------------------------
# ✅ Test the Model
# ----------------------------------------
example_data = pd.DataFrame({
    'Traffic_Congestion': [5.5],
    'Accident_Reports': [2],
    'Weather_Conditions': [7.5],
    'Potholes': [4],
    'Road_Closures': [1],
    'Traffic_Patterns': [6.5],
    'Hospital_Proximity': [12],
    'Road_Type': ['City Road'],
    'Emergency_Response_Time': [15]
})

predicted_score = predict_safety_score(example_data)
print(f"✅ Predicted Safety Score: {predicted_score[0]:.2f}")

import joblib
import sklearn
from sklearn.ensemble import RandomForestRegressor

# Check your Scikit-learn version
print(f"Your current scikit-learn version: {sklearn.__version__}")

# Load the original model
model_path = "/Users/harshitmittal/Downloads/ResQroute2/model/random_forest_model.pkl"
model = joblib.load(model_path)

# Resave the model using Scikit-learn 1.1.3
joblib.dump(model, "/Users/harshitmittal/Downloads/ResQroute2/model/random_forest_model_compatible.pkl", protocol=4)

print("✅ Model successfully converted and saved as 'random_forest_model_compatible.pkl'")
