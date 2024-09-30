import pandas as pd
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Load the historical data
data = pd.read_csv('vehicle_data.csv')

# Prepare features and target variable
X = data[['Timestamp']].values
y = data['Vehicle Count'].values

# Train a simple linear regression model
model = LinearRegression()
model.fit(X, y)

# Make predictions
predictions = model.predict(X)

# Plot the data and predictions
plt.figure()
plt.scatter(X, y, color='blue', label='Actual Data')
plt.plot(X, predictions, color='red', label='Predicted Data')
plt.xlabel('Timestamp')
plt.ylabel('Vehicle Count')
plt.title('Vehicle Count Prediction')
plt.legend()
plt.show()
