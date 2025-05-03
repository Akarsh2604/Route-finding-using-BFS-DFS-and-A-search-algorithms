import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import time

# Step 1: Retrieve map data from OpenStreetMap for a larger bounding box
G = ox.graph_from_bbox(north=13.2, south=12.0, east=77.8, west=76.5, network_type='drive')  # Ensure both cities are covered

# Define start and end locations (latitude, longitude)
start_location = (12.972442, 77.580643)  # Bengaluru city center
end_location = (12.295810, 76.639381)    # Mysore city center

# Get the nearest nodes in the graph to the specified locations
start_node = ox.distance.nearest_nodes(G, start_location[1], start_location[0])
end_node = ox.distance.nearest_nodes(G, end_location[1], end_location[0])

# Function to calculate distance in meters using the 'length' attribute
def calculate_distance(graph, path):
    total_distance = 0
    for i in range(len(path) - 1):
        total_distance += graph[path[i]][path[i + 1]][0]['length']  # Use edge length directly
    return total_distance

# A* Search Algorithm
def a_star_search(graph, start, goal):
    start_time = time.time()
    path = nx.astar_path(graph, start, goal, weight='length')
    end_time = time.time()
    return path, end_time - start_time

# Best-First Search Algorithm
def best_first_search(graph, start, goal):
    start_time = time.time()
    path = nx.shortest_path(graph, source=start, target=goal, method='dijkstra', weight='length')
    end_time = time.time()
    return path, end_time - start_time

# Iterative DFS Algorithm
def iterative_dfs(graph, start, goal):
    start_time = time.time()
    stack = [(start, [start])]
    visited = set()
    while stack:
        (node, path) = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        if node == goal:
            end_time = time.time()
            return path, end_time - start_time
        for neighbor in graph[node]:
            if neighbor not in visited:
                stack.append((neighbor, path + [neighbor]))
    end_time = time.time()
    return None, end_time - start_time

# Run all algorithms and calculate metrics
results = {}
algorithms = {
    "A*": a_star_search,
    "Best-First Search": best_first_search,
    "Iterative DFS": iterative_dfs
}

for algo_name, algo_func in algorithms.items():
    try:
        path, execution_time = algo_func(G, start_node, end_node)
        distance = calculate_distance(G, path) if path else None

        # Calculate time and space complexity dynamically
        if algo_name in ["A*", "Best-First Search"]:
            time_complexity = f"O(E + V log V) = O({G.number_of_edges()} + {G.number_of_nodes()} log {G.number_of_nodes()})"
            space_complexity = f"O(V) = O({G.number_of_nodes()})"
        elif algo_name == "Iterative DFS":
            time_complexity = f"O(V + E) = O({G.number_of_nodes()} + {G.number_of_edges()})"
            space_complexity = f"O(V) = O({G.number_of_nodes()})"
        else:
            time_complexity = space_complexity = "N/A"

        # Store results
        results[algo_name] = {
            "Path": path,
            "Distance (meters)": distance,
            "Distance (kilometers)": distance / 1000 if distance else None,
            "Execution Time (seconds)": execution_time,
            "Time Complexity": time_complexity,
            "Space Complexity": space_complexity
        }
    except Exception as e:
        results[algo_name] = {
            "Path": None,
            "Distance (meters)": None,
            "Distance (kilometers)": None,
            "Execution Time (seconds)": None,
            "Time Complexity": "N/A",
            "Space Complexity": "N/A"
        }

# Create a DataFrame for the table
table_data = {
    "Algorithm": [],
    "Distance (meters)": [],
    "Distance (kilometers)": [],
    "Execution Time (seconds)": [],
    "Time Complexity": [],
    "Space Complexity": []
}
for algo, metrics in results.items():
    table_data["Algorithm"].append(algo)
    table_data["Distance (meters)"].append(metrics["Distance (meters)"])
    table_data["Distance (kilometers)"].append(metrics["Distance (kilometers)"])
    table_data["Execution Time (seconds)"].append(metrics["Execution Time (seconds)"])
    table_data["Time Complexity"].append(metrics["Time Complexity"])
    table_data["Space Complexity"].append(metrics["Space Complexity"])
df = pd.DataFrame(table_data)

# Streamlit UI
st.title("Algorithm Comparison for Route Optimization")
st.write("This app compares the performance of three algorithms (A*, Best-First Search, and Iterative DFS) for route optimization.")

# Display the table
st.subheader("Algorithm Performance Table")
st.dataframe(df)

# Plot comparison graphs
st.subheader("Distance Comparison Graph")
distances_km = [results[algo]["Distance (kilometers)"] for algo in algorithms if results[algo]["Distance (kilometers)"] is not None]
plt.figure(figsize=(8, 4))
plt.bar(algorithms.keys(), distances_km, color=['blue', 'orange', 'green'])
plt.title("Algorithm Distance Comparison")
plt.ylabel("Distance (kilometers)")
plt.xlabel("Algorithm")
st.pyplot(plt)

st.subheader("Time Comparison Graph")
execution_times = [results[algo]["Execution Time (seconds)"] for algo in algorithms if results[algo]["Execution Time (seconds)"] is not None]
plt.figure(figsize=(8, 4))
plt.bar(algorithms.keys(), execution_times, color=['blue', 'orange', 'green'])
plt.title("Algorithm Time Comparison")
plt.ylabel("Time (seconds)")
plt.xlabel("Algorithm")
st.pyplot(plt)

# Visualize the best algorithm's path
st.subheader("Best Algorithm's Path")
valid_results = {algo: metrics for algo, metrics in results.items() if metrics["Path"] is not None}
if valid_results:
    best_algo = min(valid_results, key=lambda algo: valid_results[algo]["Distance (meters)"])
    best_path = valid_results[best_algo]["Path"]
    st.write(f"Best Algorithm: {best_algo}")
    fig, ax = ox.plot_graph_route(
        G, best_path, route_linewidth=4, node_size=0, bgcolor='white', show=False, close=True
    )
    st.pyplot(fig)
else:
    st.write("No valid paths found for any algorithm.")
