import networkx as nx
from pyvis.network import Network
import pickle
import os
import sys

# ==========================================
#        USER CONFIGURATION
# ==========================================

# File Paths
INPUT_PICKLE_PATH = "data/output/louvain_annotated_graph.pkl"
OUTPUT_DIR = "data/output/plots"

# Visual Settings
TARGET_COLOR = "#000000"        # Black
CLUSTER_COLOR = "#3b5b92"       # Medium Dark Blue
TARGET_EDGE_COLOR = "#000000"   # Black edges for target
BACKGROUND_EDGE_COLOR = "#cccccc" # Light gray for others

# Sizes (PyVis uses different scales than Matplotlib)
TARGET_SIZE = 25
NODE_SIZE = 15
TARGET_EDGE_WIDTH = 4
NORMAL_EDGE_WIDTH = 1

def create_interactive_plot(protein_name):
    print(f"--- Generating Interactive Graph for: {protein_name} ---")

    # 1. Load Data
    if not os.path.exists(INPUT_PICKLE_PATH):
        print("Error: Pickle file not found. Run 'run_louvain_graph.py' first.")
        return

    try:
        with open(INPUT_PICKLE_PATH, "rb") as f:
            G_full = pickle.load(f)
    except Exception as e:
        print(f"Error loading graph: {e}")
        return

    # 2. Validate Protein
    if protein_name not in G_full.nodes:
        print(f"Error: Protein '{protein_name}' not found in dataset.")
        return

    # 3. Extract Cluster
    target_cluster_id = G_full.nodes[protein_name].get('cluster_id')
    if target_cluster_id is None:
        print("Error: No cluster ID found on node.")
        return

    print(f"Extracting Cluster {target_cluster_id}...")
    cluster_nodes = [n for n, attrs in G_full.nodes(data=True) 
                     if attrs.get('cluster_id') == target_cluster_id]
    
    # Create NetworkX Subgraph
    nx_subgraph = G_full.subgraph(cluster_nodes)

    # 4. Initialize PyVis Network
    # height/width: 100% fills the browser window
    # bgcolor: White background
    # font_color: Label color
    net = Network(height="90vh", width="100%", bgcolor="#ffffff", font_color="black")
    
    # 5. Translate NetworkX data to PyVis with Custom Styling
    print("Applying styles...")

    # --- Add Nodes ---
    for node in nx_subgraph.nodes():
        if node == protein_name:
            # Target Protein Styling
            net.add_node(
                node, 
                label=node, 
                title=f"TARGET: {node}", # Tooltip on hover
                color=TARGET_COLOR, 
                size=TARGET_SIZE,
                borderWidth=2,
                borderWidthSelected=4,
                font={'size': 20, 'face': 'arial', 'vadjust': 5} # Push label down
            )
        else:
            # Cluster Member Styling
            net.add_node(
                node, 
                label=node, 
                title=f"Cluster Member: {node}",
                color=CLUSTER_COLOR, 
                size=NODE_SIZE,
                font={'size': 14, 'vadjust': 5} # Push label down
            )

    # --- Add Edges ---
    for u, v, data in nx_subgraph.edges(data=True):
        weight = data.get('weight', 1.0)
        
        # Check if this edge touches the target protein
        if u == protein_name or v == protein_name:
            net.add_edge(
                u, v, 
                width=TARGET_EDGE_WIDTH, 
                color=TARGET_EDGE_COLOR,
                title=f"Score: {weight}" # Hover text on line
            )
        else:
            net.add_edge(
                u, v, 
                width=NORMAL_EDGE_WIDTH, 
                color=BACKGROUND_EDGE_COLOR,
                title=f"Score: {weight}"
            )

    # 6. Physics Settings (The "Zoom/Scroll" Logic)
    # barnes_hut is the algorithm used to space nodes out. 
    # spring_length: how long edges try to be.
    # spring_strength: how strong the pull is.
    # damping: how fast nodes stop moving.
    net.force_atlas_2based(
        gravity=-50, 
        central_gravity=0.01, 
        spring_length=100, 
        spring_strength=0.08, 
        damping=0.4, 
        overlap=0
    )
    
    # You can also show control sliders in the HTML to adjust live
    # net.show_buttons(filter_=['physics']) 

    # 7. Save Output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"interactive_{protein_name}.html")
    
    # We explicitly turn off physics simulation after stabilization to prevent 
    # nodes from jittering endlessly, but they remain draggable.
    net.toggle_physics(True)
    
    print(f"Saving HTML to: {output_path}")
    net.write_html(output_path)
    
    # Automatically open in browser (Works on Windows/Mac/Linux)
    try:
        import webbrowser
        # Get absolute path for browser
        abs_path = "file://" + os.path.abspath(output_path)
        webbrowser.open(abs_path)
        print("Opened in default web browser.")
    except:
        print(f"Could not auto-open browser. Please open {output_path} manually.")


# Default
target = "CHMP2B"
    
# Command line argument override
if len(sys.argv) > 1:
    target = sys.argv[1]
        
create_interactive_plot(target)