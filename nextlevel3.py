import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import math
import time

# Set page config for better visuals
st.set_page_config(
    page_title="Emergency Vehicle Route Optimizer",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load pre-downloaded map data or fetch dynamically if unavailable
try:
    G = ox.load_graphml("bengaluru_map.graphml")
    st.write("✅ **Map loaded successfully!**")
except FileNotFoundError:
    st.warning("❌ Map file not found. Fetching data from OpenStreetMap...")
    G = ox.graph_from_bbox(north=13.0, south=12.1, east=77.7, west=76.6, network_type="drive")
    ox.save_graphml(G, "bengaluru_map.graphml")
    st.write("✅ **Map fetched and saved!**")

# Starting and Destination Points
start_lat = 12.972442  # Bengaluru
start_lon = 77.580643
st.title("🚑 Emergency Vehicle Route Optimizer")
st.markdown(f"📍 Starting Point: Bengaluru ({start_lat}, {start_lon})")

# Input Form
with st.form("coordinate_form"):
    st.markdown("### Enter Destination Coordinates")
    end_lat = st.number_input("Latitude", min_value=10.0, max_value=15.0, step=0.0001)
    end_lon = st.number_input("Longitude", min_value=75.0, max_value=80.0, step=0.0001)
    submitted = st.form_submit_button("Find Optimized Routes")

if submitted:
    st.markdown(f"🚩 Destination Point: {end_lat}, {end_lon}")

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

    # Run All Algorithms
    results = {}
    algorithms = {
        "A*": a_star_search,
        "Best-First Search": best_first_search,
        "Iterative DFS": iterative_dfs,
    }

    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()

    def calculate_time_complexity(algorithm, num_nodes, num_edges):
        if algorithm in ["A*", "Best-First Search"]:
            return num_edges + (num_nodes * math.log2(num_nodes))
        elif algorithm == "Iterative DFS":
            return num_nodes + num_edges
        else:
            return None

    for name, func in algorithms.items():
        path, exec_time = func(G, start_node, end_node)
        numerical_time_complexity = calculate_time_complexity(name, num_nodes, num_edges)
        space_complexity = "O(V)"
        if name == "Iterative DFS":
            space_complexity = "O(h) (Stack Depth)"

        results[name] = {
            "Path": path,
            "Distance (meters)": calculate_distance(G, path) if path else None,
            "Execution Time (seconds)": exec_time,
            "Numerical Time Complexity": numerical_time_complexity,
            "Space Complexity": space_complexity,
        }

    # Tabulate Results
    st.markdown("### Algorithm Performance Table")
    df = pd.DataFrame(results).T[
        ["Distance (meters)", "Execution Time (seconds)", "Numerical Time Complexity", "Space Complexity"]
    ]
    st.dataframe(df.style.format(
        {
            "Distance (meters)": "{:.2f}",
            "Execution Time (seconds)": "{:.2f}",
            "Numerical Time Complexity": "{:.2f}",
        }
    ))
