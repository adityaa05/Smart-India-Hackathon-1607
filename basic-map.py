import folium

# Step 2: Define the location
my_location = [19.214313972602916, 73.09111140864862]  # Phadke Watch Centre

# Step 3: Create a map centered at the location
my_map = folium.Map(location=my_location, zoom_start=14)

# Step 4: Add a marker (optional)
folium.Marker(my_location, popup="Phadke Watch Centre").add_to(my_map)

# Step 5: Save the map as an HTML file
my_map.save('my_map.html')

# Print confirmation
print("Map has been created and saved as 'my_map.html'.")
