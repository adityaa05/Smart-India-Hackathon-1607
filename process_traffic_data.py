import pandas as pd

# Load the CSV file
traffic_data = pd.read_csv('/home/adityaa/Documents/0320122-America-New_York.csv-openLR')

# Display the first few rows of the dataset to understand its structure
print("First few rows of the dataset:")
print(traffic_data.head(10))  # Displaying more rows for better context

# Display all the column names to help identify latitude, longitude, and traffic condition columns
print("\nColumn names in the dataset:")
print(traffic_data.columns)

# Based on the data structure, update these variables with the correct column names
# For now, I'm leaving these as placeholders, you'll need to replace these with actual column names
latitude_column = 'latitude_placeholder'  # Replace with actual column name after inspecting the data
longitude_column = 'longitude_placeholder'  # Replace with actual column name after inspecting the data
traffic_condition_column = 'traffic_condition_placeholder'  # Replace with actual column name after inspecting the data

# Before extracting, let's check if the placeholder columns exist in the data
if latitude_column in traffic_data.columns and longitude_column in traffic_data.columns and traffic_condition_column in traffic_data.columns:
    # Extract relevant columns if they exist
    sample_data = traffic_data[[latitude_column, longitude_column, traffic_condition_column]]
    print("\nSample of relevant data:")
    print(sample_data.head())
else:
    print("\nThe specified columns do not exist in the dataset. Please check the column names and update them accordingly.")
