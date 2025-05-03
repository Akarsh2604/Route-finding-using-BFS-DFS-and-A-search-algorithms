import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import time

# Set page config for better visuals
st.set_page_config(
    page_title="Route Optimization App",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS for styling
st.markdown(
    """
    <style>
        /* Center the title and content */
        .main { background-color: #f4f4f4; }
        h1 {
            color: #4CAF50;
            text-align: center;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .stButton button:hover {
            background-color: #45a049;
        }
        .stDataFrame {
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }
        .stForm {
            background: #ffffff;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #ddd;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
        }
        .metrics {
            font-size: 16px;
            font-weight: bold;
            text-align: center;
            margin-top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Load map data or fetch dynamically if unavailable
st.markdown("<h1>Route Optimization App</h1>", unsafe_allow_html=True)
st.write("🌍 Compare different algorithms (A*, Best-First Search, Iterative DFS) for route optimization.")

try:
    G = ox.load_graphml("bengaluru_map.graphml")
    st.write("✅ **Map loaded successfully!**")
except FileNotFoundError:
    st.warning("❌ Map file not found. Fetching data from OpenStreetMap (this may take time)...")
    G = ox.graph_from_bbox(north=13.2, south=12.0, east=77.8, west=76.5, network_type='drive')
    ox.save_graphml(G, "bengaluru_map.graphml")
    st.write("✅ **Map fetched and saved as 'bengaluru_map.graphml'!**")

# Starting point
start_lat = 12.972442
start_lon = 77.580643
st.markdown("<div class='metrics'>📍 Starting Point: Bengaluru</div>", unsafe_allow_html=True)

# Form for destination input
with st.form("coordinate_form"):
    st.markdown("<h3>Enter Your Destination Coordinates</h3>", unsafe_allow_html=True)
    end_lat = st.number_input("Latitude", min_value=10.0, max_value=15.0, step=0.0001, help="Enter latitude of the destination")
    end_lon = st.number_input("Longitude", min_value=75.0, max_value=80.0, step=0.0001, help="Enter longitude of the destination")
    submitted = st.form_submit_button("Find Optimized Route")

if submitted:
    st.markdown(f"<div class='metrics'>🚩 Destination Point: {end_lat}, {end_lon}</div>", unsafe_allow_html=True)

    # Find nearest nodes
    try:
        start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
        end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
        st.markdown(f"<div class='metrics'>🛤️ Nodes: Start = {start_node}, End = {end_node}</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error finding nodes: {e}")
        st.stop()

    # Helper functions
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

    # Run all algorithms
    results = {}
    algorithms = {"A*": a_star_search, "Best-First Search": best_first_search, "Iterative DFS": iterative_dfs}
    for name, func in algorithms.items():
        path, exec_time = func(G, start_node, end_node)
        results[name] = {
            "Path": path,
            "Distance (meters)": calculate_distance(G, path) if path else None,
            "Time Taken (seconds)": exec_time,
        }

    # Create a DataFrame
    df = pd.DataFrame(results).T[["Distance (meters)", "Time Taken (seconds)"]]
    st.markdown("<h3>Algorithm Performance</h3>", unsafe_allow_html=True)
    st.dataframe(df.style.format({"Distance (meters)": "{:.2f}", "Time Taken (seconds)": "{:.2f}"}))

    # Visualizations
    st.markdown("<h3>Performance Comparison</h3>", unsafe_allow_html=True)
    distances = [result["Distance (meters)"] for result in results.values()]
    times = [result["Time Taken (seconds)"] for result in results.values()]

    # Distance Graph
    plt.figure(figsize=(8, 4))
    plt.bar(results.keys(), distances, color=["#4CAF50", "#FF9800", "#2196F3"])
    plt.title("Distance Comparison")
    plt.ylabel("Distance (meters)")
    plt.xlabel("Algorithm")
    st.pyplot(plt)

    # Time Graph
    plt.figure(figsize=(8, 4))
    plt.bar(results.keys(), times, color=["#4CAF50", "#FF9800", "#2196F3"])
    plt.title("Execution Time Comparison")
    plt.ylabel("Time (seconds)")
    plt.xlabel("Algorithm")
    st.pyplot(plt)

    # Best Algorithm Path Visualization
    st.markdown("<h3>Best Algorithm's Path</h3>", unsafe_allow_html=True)
    best_algo = min(results, key=lambda x: results[x]["Distance (meters)"])
    best_path = results[best_algo]["Path"]
    st.markdown(f"<div class='metrics'>🏆 Best Algorithm: {best_algo}</div>", unsafe_allow_html=True)
    fig, ax = ox.plot_graph_route(G, best_path, route_linewidth=4, node_size=0, bgcolor="white", show=False, close=True)
    st.pyplot(fig)

