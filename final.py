import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import time

# Page setup with custom title and layout
st.set_page_config(page_title="Emergency Vehicle Route Optimization", layout="wide")
st.markdown(
    "<h1 style='text-align: center; color: #4CAF50;'>🚑 Emergency Vehicle Route Optimization</h1>",
    unsafe_allow_html=True,
)

# Step 1: Load map data
try:
    G = ox.load_graphml("bengaluru_map.graphml")
    st.success("🗺️ Map successfully loaded!")
except FileNotFoundError:
    st.warning("Fetching map data from OpenStreetMap...")
    G = ox.graph_from_bbox(north=13.2, south=12.0, east=77.8, west=76.5, network_type='drive')
    ox.save_graphml(G, "bengaluru_map.graphml")
    st.success("🗺️ Map fetched and saved!")

# Sidebar with icons for inputs
st.sidebar.header("Input Destination Coordinates")
st.sidebar.markdown(
    """
    <style>
    .icon { font-size: 20px; margin-right: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Starting point
st.sidebar.markdown("<div class='icon'>📍 **Starting Point:**</div>", unsafe_allow_html=True)
st.sidebar.markdown(f"Latitude: 12.972442, Longitude: 77.580643 (Bangalore)")

# Form for destination inputs
with st.sidebar.form("coordinate_form"):
    st.markdown("<div class='icon'>🏥 **Destination Point:**</div>", unsafe_allow_html=True)
    end_lat = st.number_input("Enter Destination Latitude:", min_value=10.0, max_value=15.0, step=0.0001)
    end_lon = st.number_input("Enter Destination Longitude:", min_value=75.0, max_value=80.0, step=0.0001)
    algorithm = st.selectbox(
        "Select Algorithm",
        ["A*", "Best-First Search", "Iterative DFS", "Compare All Algorithms"],
    )
    submitted = st.form_submit_button("Find Optimized Route 🚗")

if submitted:
    st.markdown(
        "<h3 style='text-align: center;'>🚦 Processing route...</h3>",
        unsafe_allow_html=True,
    )

    try:
        start_node = ox.distance.nearest_nodes(G, 77.580643, 12.972442)
        end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

    def calculate_distance(graph, path):
        return sum(graph[path[i]][path[i + 1]][0]['length'] for i in range(len(path) - 1))

    algorithms = {
        "A*": {
            "func": lambda g, s, e: nx.astar_path(g, s, e, weight="length"),
            "time_complexity": "O(E + V log V)",
            "space_complexity": "O(V)"
        },
        "Best-First Search": {
            "func": lambda g, s, e: nx.shortest_path(g, s, e, weight="length"),
            "time_complexity": "O(E + V log V)",
            "space_complexity": "O(V)"
        },
        "Iterative DFS": {
            "func": lambda g, s, e: iterative_dfs(g, s, e),
            "time_complexity": "O(V + E)",
            "space_complexity": "O(V)"
        },
    }

    def iterative_dfs(graph, start, goal):
        stack = [(start, [start])]
        visited = set()
        while stack:
            (node, path) = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            if node == goal:
                return path
            stack.extend((neighbor, path + [neighbor]) for neighbor in graph[node])
        return []

    if algorithm == "Compare All Algorithms":
        results = {}
        for algo_name, algo_info in algorithms.items():
            start_time = time.time()
            try:
                path = algo_info["func"](G, start_node, end_node)
                execution_time = time.time() - start_time
                distance = calculate_distance(G, path) if path else None
                results[algo_name] = {
                    "Time Complexity": algo_info["time_complexity"],
                    "Space Complexity": algo_info["space_complexity"],
                    "Distance (km)": distance / 1000 if distance else None,
                    "Execution Time (s)": execution_time,
                    "Path": path
                }
            except Exception as e:
                results[algo_name] = {
                    "Time Complexity": algo_info["time_complexity"],
                    "Space Complexity": algo_info["space_complexity"],
                    "Distance (km)": None,
                    "Execution Time (s)": None,
                    "Path": None
                }

        # Display comparison table (exclude the Path column)
        st.markdown("<h3>🔍 Algorithm Comparison Table</h3>", unsafe_allow_html=True)
        df = pd.DataFrame(results).T.drop(columns=["Path"]).reset_index()
        df.columns = ["Algorithm", "Time Complexity", "Space Complexity", "Distance (km)", "Execution Time (s)"]
        st.dataframe(df)

        # Find the best algorithm (shortest distance or fastest time if tie)
        best_algo = min(results, key=lambda x: (results[x]["Distance (km)"], results[x]["Execution Time (s)"]))
        st.success(f"🏆 Best Algorithm: {best_algo}")

        # Visualize the best algorithm's route
        best_path = results[best_algo]["Path"]
        if best_path:
            st.markdown("<h3>🚗 Best Route Visualization</h3>", unsafe_allow_html=True)
            fig, ax = ox.plot_graph_route(
                G, best_path, route_linewidth=4, node_size=0, bgcolor="white", show=False, close=True
            )
            st.pyplot(fig)
        else:
            st.error("❌ No route found for the best algorithm.")

    else:
        # Single algorithm mode
        algo_info = algorithms[algorithm]
        start_time = time.time()
        try:
            path = algo_info["func"](G, start_node, end_node)
            execution_time = time.time() - start_time
            distance = calculate_distance(G, path) if path else None
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

        if path:
            st.success(f"🚀 Algorithm: {algorithm}")
            st.metric("Total Distance (km)", round(distance / 1000, 2))
            st.metric("Execution Time (s)", round(execution_time, 4))
            st.markdown("<h3>🚗 Route Visualization</h3>", unsafe_allow_html=True)
            fig, ax = ox.plot_graph_route(
                G, path, route_linewidth=4, node_size=0, bgcolor="white", show=False, close=True
            )
            st.pyplot(fig)
        else:
            st.error("❌ No route found.")

# Footer with icons
st.markdown("<hr style='border:1px solid #4CAF50;'>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align: center;'>🚑 Designed for Efficient Emergency Vehicle Routing</p>",
    unsafe_allow_html=True,
)
