import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import time

# Step 1: Load pre-downloaded map data or fetch it dynamically if unavailable
st.write("Loading map data...")
try:
    # Load the pre-downloaded map file
    G = ox.load_graphml("bengaluru_map.graphml")
    st.write("Map successfully loaded!")
except FileNotFoundError:
    # If map file not found, fetch it from OpenStreetMap and save it
    st.warning("Map file not found. Fetching data from OpenStreetMap (this may take some time)...")
    G = ox.graph_from_bbox(north=13.2, south=12.0, east=77.8, west=76.5, network_type='drive')
    ox.save_graphml(G, "bengaluru_map.graphml")
    st.write("Map fetched and saved as 'bengaluru_map.graphml'!")

# UI for inputting destination coordinates
st.title("Algorithm Comparison for Route Optimization")
st.write("This app compares the performance of three algorithms (A*, Best-First Search, and Iterative DFS) for route optimization.")

# User inputs for starting and destination coordinates
start_lat = 12.972442  # Fixed starting point (Bangalore)
start_lon = 77.580643
st.write(f"Starting Point: Latitude = {start_lat}, Longitude = {start_lon} (Bangalore)")

# Input fields for destination coordinates
with st.form("coordinate_form"):
    end_lat = st.number_input("Enter Destination Latitude:", min_value=10.0, max_value=15.0, step=0.0001)
    end_lon = st.number_input("Enter Destination Longitude:", min_value=75.0, max_value=80.0, step=0.0001)
    submitted = st.form_submit_button("Find Optimized Route")

if submitted:
    st.write(f"Destination Point: Latitude = {end_lat}, Longitude = {end_lon}")

    # Get the nearest nodes in the graph to the specified locations
    try:
        start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
        end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
        st.write(f"Nearest nodes found. Start Node: {start_node}, End Node: {end_node}")
    except Exception as e:
        st.error(f"Error finding nodes: {e}")
        st.stop()

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
