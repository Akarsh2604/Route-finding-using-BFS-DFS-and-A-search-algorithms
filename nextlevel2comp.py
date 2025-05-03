import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import time

# Load pre-downloaded map data or fetch it dynamically if unavailable
try:
    G = ox.load_graphml("bengaluru_map.graphml")
    st.write("✅ Map loaded successfully!")
except FileNotFoundError:
    st.warning("Map file not found. Fetching a smaller dataset for testing...")
    G = ox.graph_from_bbox(north=13.0, south=12.1, east=77.7, west=76.6, network_type="drive")
    ox.save_graphml(G, "bengaluru_map.graphml")
    st.write("✅ Map fetched and saved!")

# Starting and Destination Points
start_lat = 12.972442  # Bengaluru
start_lon = 77.580643

st.title("Optimized Route Finder")
st.write("🌍 Compare algorithms for finding optimized routes.")

# Input Form
with st.form("coordinate_form"):
    st.markdown("### Enter Destination Coordinates")
    end_lat = st.number_input("Latitude", min_value=10.0, max_value=15.0, step=0.0001)
    end_lon = st.number_input("Longitude", min_value=75.0, max_value=80.0, step=0.0001)
    algorithm = st.selectbox("Select Algorithm", ["A*", "Best-First Search", "Iterative DFS"])
    submitted = st.form_submit_button("Find Optimized Route")

if submitted:
    st.write(f"Starting Point: {start_lat}, {start_lon}")
    st.write(f"Destination Point: {end_lat}, {end_lon}")

    # Find nearest nodes
    try:
        start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
        end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
    except Exception as e:
        st.error(f"Error finding nodes: {e}")
        st.stop()

    # Helper Functions
    def calculate_distance(graph, path):
        return sum(graph[path[i]][path[i + 1]][0]["length"] for i in range(len(path) - 1))

    def a_star_search(graph, start, goal):
        start_time = time.time()
        path = nx.astar_path(graph, start, goal, weight="length")
        return path, time.time() - start_time

    def best_first_search(graph, start, goal):
        start_time = time.time()
        path = nx.shortest_path(graph, source=start, target=goal, method="dijkstra", weight="length")
        return path, time.time() - start_time

    def iterative_dfs(graph, start, goal):
        stack, visited = [(start, [start])], set()
        start_time = time.time()
        while stack:
            node, path = stack.pop()
            if node == goal:
                return path, time.time() - start_time
            if node not in visited:
                visited.add(node)
                stack.extend((neighbor, path + [neighbor]) for neighbor in graph[node] if neighbor not in visited)
        return None, time.time() - start_time

    # Run the selected algorithm
    st.write(f"Running {algorithm}...")
    if algorithm == "A*":
        path, exec_time = a_star_search(G, start_node, end_node)
        time_complexity = f"O(E + V log V) = O({G.number_of_edges()} + {G.number_of_nodes()} log {G.number_of_nodes()})"
        space_complexity = f"O(V) = O({G.number_of_nodes()})"
    elif algorithm == "Best-First Search":
        path, exec_time = best_first_search(G, start_node, end_node)
        time_complexity = f"O(E + V log V) = O({G.number_of_edges()} + {G.number_of_nodes()} log {G.number_of_nodes()})"
        space_complexity = f"O(V) = O({G.number_of_nodes()})"
    elif algorithm == "Iterative DFS":
        path, exec_time = iterative_dfs(G, start_node, end_node)
        time_complexity = f"O(V + E) = O({G.number_of_nodes()} + {G.number_of_edges()})"
        space_complexity = f"O(V) = O({G.number_of_nodes()})"

    # Calculate Results
    distance = calculate_distance(G, path) if path else None
    st.write(f"**Execution Time:** {exec_time:.2f} seconds")
    st.write(f"**Distance:** {distance:.2f} meters" if distance else "No path found.")

    # Create Results Table
    table_data = {
        "Algorithm": [algorithm],
        "Distance (meters)": [distance],
        "Execution Time (seconds)": [exec_time],
        "Time Complexity": [time_complexity],
        "Space Complexity": [space_complexity],
    }
    df = pd.DataFrame(table_data)
    st.markdown("### Algorithm Performance")
    st.dataframe(df.style.format({"Distance (meters)": "{:.2f}", "Execution Time (seconds)": "{:.2f}"}))

    # Visualizations
    st.markdown("### Visualizations")
    if path:
        fig, ax = ox.plot_graph_route(G, path, route_linewidth=4, node_size=0, bgcolor="white", show=False, close=True)
        st.pyplot(fig)
    else:
        st.write("No path visualization available.")
