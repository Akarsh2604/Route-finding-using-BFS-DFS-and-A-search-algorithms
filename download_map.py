import osmnx as ox

# Fetch map data for Bengaluru and surrounding regions
print("Fetching map data...")
G = ox.graph_from_bbox(north=13.2, south=12.0, east=77.8, west=76.5, network_type='drive')

# Save the map data as a GraphML file
ox.save_graphml(G, "bengaluru_map.graphml")
print("Map data successfully saved as 'bengaluru_map.graphml'.")
