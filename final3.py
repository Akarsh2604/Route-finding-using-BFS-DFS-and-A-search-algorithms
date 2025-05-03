import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import time

# Page setup
st.set_page_config(page_title="Emergency Vehicle Route Optimization", layout="wide")
st.markdown(
    "<h1 style='text-align: center; color: #4CAF50;'>🚑 Emergency Vehicle Route Optimization</h1>",
    unsafe_allow_html=True,
)

# Load or fetch the map data
try:
    G = ox.load_graphml("bengaluru_map.graphml")
    st.success("🗺️ Map successfully loaded!")
except FileNotFoundError:
    st.warning("Fetching map data from OpenStreetMap...")
    G = ox.graph_from_bbox(north=13.2, south=12.0, east=77.8, west=76.5, network_type='drive')
    ox.save_graphml(G, "bengaluru_map.graphml")
    st.success("🗺️ Map fetched and saved!")

# Sidebar inputs
st.sidebar.header("Input Destination Coordinates")
start_lat = 12.972442  # Starting point latitude (Bangalore)
start_lon = 77.580643  # Starting point longitude (Bangalore)
st.sidebar.markdown(f"📍 **Starting Point:** Latitude: {start_lat}, Longitude: {start_lon}")

with st.sidebar.form("coordinate_form"):
    end_lat = st.number_input("Enter Destination Latitude:", min_value=10.0, max_value=15.0, step=0.0001)
    end_lon = st.number_input("Enter Destination Longitude:", min_value=75.0, max_value=80.0, step=0.0001)
    algorithm = st.selectbox(
        "Select Algorithm",
        ["A*", "Best-First Search", "Iterative DFS", "Compare All Algorithms"],
    )
    submitted = st.form_submit_button("Run Algorithm")

if submitted:
    st.markdown(
        "<h3 style='text-align: center;'>🚦 Processing your request...</h3>",
        unsafe_allow_html=True,
    )

    try:
        start_node = ox.distance.nearest_nodes(G, start_lon, start_lat)
        end_node = ox.distance.nearest_nodes(G, end_lon, end_lat)
    except Exception as e:
        st.error(f"Error finding nodes: {e}")
        st.stop()

    def calculate_distance(graph, path):
        return sum(graph[path[i]][path[i + 1]][0]['length'] for i in range(len(path) - 1))

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
            "space_complexity": "O(d)"
        },
    }

    if algorithm == "Compare All Algorithms":
        results = {}
        for algo_name, algo_info in algorithms.items():
            start_time = time.time()
            try:
                path = algo_info["func"](G, start_node, end_node)
                execution_time = time.time() - start_time
                distance = calculate_distance(G, path) if path else None

                actual_time_complexity = f"O({G.number_of_edges()} + {G.number_of_nodes()} log {G.number_of_nodes()})" if algo_name != "Iterative DFS" else f"O({G.number_of_nodes()} + {G.number_of_edges()})"
                actual_space_complexity = f"O({G.number_of_nodes()})" if algo_name != "Iterative DFS" else f"O(d)"

                results[algo_name] = {
                    "Time Complexity": actual_time_complexity,
                    "Space Complexity": actual_space_complexity,
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

        # Display comparison table
        st.markdown("<h3>🔍 Algorithm Comparison Table</h3>", unsafe_allow_html=True)

        df = pd.DataFrame(results).T.reset_index()
        df.columns = ["Algorithm"] + list(df.columns[1:])  # Dynamically adjust columns
        st.dataframe(df)

        # Plot comparison graphs
        distances = [res["Distance (km)"] for res in results.values() if res["Distance (km)"] is not None]
        execution_times = [res["Execution Time (s)"] for res in results.values() if res["Execution Time (s)"] is not None]

        st.markdown("<h3>📊 Distance Comparison</h3>", unsafe_allow_html=True)
        plt.figure(figsize=(8, 4))
        plt.bar(results.keys(), distances, color=["blue", "orange", "green"])
        plt.title("Distance Comparison")
        plt.ylabel("Distance (km)")
        plt.xlabel("Algorithm")
        st.pyplot(plt)

        st.markdown("<h3>⏱️ Execution Time Comparison</h3>", unsafe_allow_html=True)
        plt.figure(figsize=(8, 4))
        plt.bar(results.keys(), execution_times, color=["blue", "orange", "green"])
        plt.title("Execution Time Comparison")
        plt.ylabel("Time (s)")
        plt.xlabel("Algorithm")
        st.pyplot(plt)

        # Highlight the best algorithm
        best_algo = min(results, key=lambda x: (results[x]["Distance (km)"], results[x]["Execution Time (s)"]))
        st.success(f"🏆 Best Algorithm: {best_algo}")

        # Visualize the best algorithm's route
        best_path = results[best_algo].get("Path", None)
        if best_path:
            st.markdown("<h3>🚗 Best Route Visualization</h3>", unsafe_allow_html=True)
            fig, ax = ox.plot_graph_route(
                G, best_path, route_linewidth=4, node_size=0, bgcolor="white", show=False, close=True
            )
            st.pyplot(fig)
        else:
            st.error("❌ No route found for the best algorithm.")

    else:
        # Single algorithm execution
        algo_info = algorithms[algorithm]
        start_time = time.time()
        try:
            path = algo_info["func"](G, start_node, end_node)
            execution_time = time.time() - start_time
            distance = calculate_distance(G, path) if path else None

            # Display individual algorithm results
            st.markdown(f"<h3>🔍 Results for {algorithm}</h3>", unsafe_allow_html=True)
            st.metric("Distance (km)", round(distance / 1000, 2) if distance else "N/A")
            st.metric("Execution Time (s)", round(execution_time, 4) if execution_time else "N/A")
            st.metric("Time Complexity", algo_info["time_complexity"])
            st.metric("Space Complexity", algo_info["space_complexity"])

            # Visualize the path
            if path:
                st.markdown("<h3>🚗 Route Visualization</h3>", unsafe_allow_html=True)
                fig, ax = ox.plot_graph_route(
                    G, path, route_linewidth=4, node_size=0, bgcolor="white", show=False, close=True
                )
                st.pyplot(fig)
            else:
                st.error("❌ No route found.")
        except Exception as e:
            st.error(f"Error running {algorithm}: {e}")
