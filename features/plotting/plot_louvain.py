import networkx as nx
import matplotlib.pyplot as plt
import pickle
import os
import sys

# ==========================================
#        USER CONFIGURATION
# ==========================================

# File Paths
INPUT_PICKLE_PATH = "data/output/louvain_annotated_graph.pkl"
OUTPUT_PLOT_DIR = "data/output/plots"

# Visualization Settings
TARGET_NODE_COLOR = "black"
CLUSTER_NODE_COLOR = "#3b5b92"  # Medium Dark Blue
TARGET_EDGE_WIDTH = 3.0         # Fat edges for target
NORMAL_EDGE_WIDTH = 0.5         # Thin edges for others
NODE_SIZE = 300
FONT_SIZE = 8
LABEL_OFFSET_Y = 0.06           # How far under the node to push the label

def plot_cluster(protein_name):
    print(f"--- Visualizing Cluster for: {protein_name} ---")

    # 1. Check Input File
    if not os.path.exists(INPUT_PICKLE_PATH):
        print(f"Error: Pickle file not found at {INPUT_PICKLE_PATH}")
        print("Please run 'run_louvain_graph.py' first.")
        return

    # 2. Load Graph Object (Unpickling)
    print("Loading graph object...")
    try:
        with open(INPUT_PICKLE_PATH, "rb") as f:
            G = pickle.load(f)
    except Exception as e:
        print(f"Error loading graph: {e}")
        return

    # 3. Validate Target Protein
    if protein_name not in G.nodes:
        print(f"Error: Protein '{protein_name}' not found in the dataset.")
        return

    # 4. Extract Cluster
    # Get the cluster ID stored in the target node's attributes
    target_cluster_id = G.nodes[protein_name].get('cluster_id')
    
    if target_cluster_id is None:
        print("Error: Node found, but it has no cluster_id. Did you run the Louvain script?")
        return

    print(f"Protein found in Cluster ID: {target_cluster_id}")

    # Find all nodes belonging to this cluster
    cluster_nodes = [n for n, attrs in G.nodes(data=True) 
                     if attrs.get('cluster_id') == target_cluster_id]
    
    print(f"Extracting subgraph with {len(cluster_nodes)} nodes...")
    
    # Create the subgraph
    H = G.subgraph(cluster_nodes)

    # 5. Define Visual Styles
    print("Applying visual styles...")
    
    # --- Node Colors ---
    node_colors = []
    for node in H.nodes():
        if node == protein_name:
            node_colors.append(TARGET_NODE_COLOR)
        else:
            node_colors.append(CLUSTER_NODE_COLOR)

    # --- Edge Widths ---
    edge_widths = []
    edge_colors = []
    
    for u, v in H.edges():
        # Check if edge connects to target
        if u == protein_name or v == protein_name:
            edge_widths.append(TARGET_EDGE_WIDTH)
            edge_colors.append("black") # Make lines connected to target black
        else:
            edge_widths.append(NORMAL_EDGE_WIDTH)
            edge_colors.append("lightgray") # Background edges lighter

    # 6. Calculate Layout
    # spring_layout positions nodes based on edge attraction (physics simulation)
    pos = nx.spring_layout(H, seed=42, k=0.5) # k regulates distance between nodes

    # 7. Create Label Positions (Shifted Down)
    pos_labels = {}
    for node, coords in pos.items():
        # Keep X the same, subtract from Y to move label under node
        pos_labels[node] = (coords[0], coords[1] - LABEL_OFFSET_Y)

    # 8. Plotting
    plt.figure(figsize=(12, 10))
    
    # Draw Edges
    nx.draw_networkx_edges(
        H, pos, 
        width=edge_widths, 
        edge_color=edge_colors, 
        alpha=0.7
    )

    # Draw Nodes
    nx.draw_networkx_nodes(
        H, pos, 
        node_color=node_colors, 
        node_size=NODE_SIZE,
        edgecolors="white", # Thin white border around nodes for clarity
        linewidths=1.0
    )

    # Draw Labels (Under the nodes)
    nx.draw_networkx_labels(
        H, pos_labels, 
        font_size=FONT_SIZE, 
        font_color="black",
        font_weight="bold" if len(cluster_nodes) < 50 else "normal"
    )

    # Final Styling
    plt.title(f"Cluster {target_cluster_id} containing {protein_name}", fontsize=14)
    plt.axis("off") # Turn off X/Y axis numbers

    # 9. Save Plot
    os.makedirs(OUTPUT_PLOT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_PLOT_DIR, f"cluster_plot_{protein_name}.png")
    
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Plot saved successfully to: {output_path}")
    
    # Show interactive window
    plt.show()


    # Default protein if none provided
target_protein = "CHMP2B"
    
    # Allow running via command line: python plot_louvain.py SNCA
if len(sys.argv) > 1:
    target_protein = sys.argv[1]
        
plot_cluster(target_protein)