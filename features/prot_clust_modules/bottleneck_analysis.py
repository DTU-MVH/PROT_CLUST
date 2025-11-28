"""
Module: bottleneck.py
Description: 
    Contains functions to analyze a specific target protein within the network.
    It locates the protein's community, calculates bottleneck metrics,
    and generates static and interactive visualizations.
"""

import networkx as nx
import pandas as pd
import pickle
import os
import matplotlib.pyplot as plt
import time
import sys

# Try importing PyVis for interactive visualization
try:
    from pyvis.network import Network
    PYVIS_AVAILABLE = True
except ImportError:
    PYVIS_AVAILABLE = False

def get_ranks(metric_dict, ascending=False):
    """
    Helper: Converts a dictionary of values {node: value} into rankings {node: rank}.
    Rank 1 is the 'best' based on the sorting order.
    """
    sorted_items = sorted(metric_dict.items(), key=lambda x: x[1], reverse=not ascending)
    return {node: rank+1 for rank, (node, val) in enumerate(sorted_items)}

def btl_anal(
    target_protein, 
    pickle_path, 
    output_dir, 
    top_n=20, 
    large_cluster_limit=500
):
    """
    Main function to investigate a target protein's cluster.

    Parameters:
        target_protein (str): The name of the protein to analyze (e.g., "SNCAIP").
        pickle_path (str): Path to the .pkl file containing the graph and communities.
        output_dir (str): Directory where CSV reports and Images will be saved.
        top_n (int): Number of top bottleneck candidates to return/display.
        large_cluster_limit (int): If a cluster is larger than this, use approximate 
                                   Betweenness Centrality to save time.

    Returns:
        dict: A dictionary containing:
            - "dataframe": Pandas DataFrame of the rankings.
            - "html_path": Absolute path to the interactive HTML file.
            - "png_path": Absolute path to the static PNG file.
            - "cluster_id": The ID of the found cluster.
            - "error": Error message string if something failed (None if success).
    """
    
    # --- 1. Setup Directories ---
    img_dir = os.path.join(output_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    print(f"\n--- 🔍 Analyzing Target: {target_protein} ---")

    # --- 2. Load Pickle ---
    if not os.path.exists(pickle_path):
        return {"error": f"Pickle file not found at {pickle_path}"}

    try:
        with open(pickle_path, "rb") as f:
            data = pickle.load(f)
        G = data['graph']
        communities = data['communities']
    except Exception as e:
        return {"error": f"Failed to load pickle: {e}"}

    # --- 3. Locate Target ---
    # Build node -> cluster mapping
    node2cluster = {}
    for cid, comm in enumerate(communities):
        for n in comm:
            node2cluster[n] = cid

    if target_protein not in node2cluster:
        return {"error": f"Protein '{target_protein}' not found in the graph."}

    cluster_id = node2cluster[target_protein]
    target_nodes = communities[cluster_id]
    
    print(f"[INFO] Found in Cluster #{cluster_id} (Size: {len(target_nodes)} nodes)")

    # --- 4. Subgraph & Metrics ---
    # Create subgraph
    subG = G.subgraph(target_nodes).copy()

    print("[INFO] Calculating network metrics (Degree, Betweenness, Clustering)...")
    t0 = time.time()

    # Metrics
    deg = dict(subG.degree())
    clust = nx.clustering(subG, weight="weight")

    # Betweenness Optimization
    if len(subG) > large_cluster_limit:
        print(f"   > Cluster > {large_cluster_limit} nodes. Using k-approximation for speed.")
        k_sample = int(len(subG) * 0.20) # Sample 20%
        bc = nx.betweenness_centrality(subG, k=k_sample, weight="weight", normalized=True, seed=42)
    else:
        bc = nx.betweenness_centrality(subG, weight="weight", normalized=True)
    
    print(f"   > Metrics computed in {time.time() - t0:.2f}s")

    # --- 5. Ranking (Bottleneck Score) ---
    # Rule: High BC + High Degree + Low Clustering = Good Bottleneck
    rank_bc = get_ranks(bc, ascending=False)
    rank_deg = get_ranks(deg, ascending=False)
    rank_clust = get_ranks(clust, ascending=True)

    results = []
    for node in subG.nodes():
        score = rank_bc[node] + rank_deg[node] + rank_clust[node]
        results.append({
            "Protein": node,
            "Total_Score": score,
            "BC": bc[node],
            "Degree": deg[node],
            "Clustering": clust[node]
        })

    df = pd.DataFrame(results).sort_values("Total_Score").reset_index(drop=True)
    
    # Save CSV
    csv_path = os.path.join(output_dir, f"bottlenecks_cluster_{cluster_id}.csv")
    df.to_csv(csv_path, index=False)

    # Get top candidates for highlighting
    top_candidates = df.head(top_n)["Protein"].tolist()

    # --- 6. Static Plot (Matplotlib) ---
    print("[INFO] Generating static PNG...")
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(subG, seed=42)
    
    # Draw Background
    nx.draw_networkx_nodes(subG, pos, node_size=50, node_color='lightgrey', alpha=0.6)
    nx.draw_networkx_edges(subG, pos, alpha=0.1, edge_color='grey')

    # Draw Target (Red)
    nx.draw_networkx_nodes(subG, pos, nodelist=[target_protein], node_color='red', node_size=250, label="Target")

    # Draw Bottlenecks (Blue) - Exclude target if it's in the list
    bottlenecks_draw = [x for x in top_candidates if x != target_protein]
    nx.draw_networkx_nodes(subG, pos, nodelist=bottlenecks_draw, node_color='blue', node_size=150, label="Bottlenecks")

    # Labels
    labels = {n: n for n in top_candidates}
    labels[target_protein] = target_protein
    nx.draw_networkx_labels(subG, pos, labels=labels, font_size=8, font_weight='bold')

    plt.title(f"Cluster {cluster_id}: {target_protein}")
    plt.axis("off")
    plt.legend()
    
    png_path = os.path.join(img_dir, f"cluster_{cluster_id}_static.png")
    plt.savefig(png_path, dpi=150)
    plt.close() # Close plot to prevent it printing twice in notebooks

    # --- 7. Interactive HTML (PyVis) ---
    html_path = None
    if PYVIS_AVAILABLE:
        print("[INFO] Generating interactive HTML...")
        
        # cdn_resources='remote' ensures it loads correctly in Notebooks
        nt = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black", cdn_resources='remote')
        
        # Physics tweak for larger graphs
        if len(subG) > 200:
            nt.barnes_hut(gravity=-2000, central_gravity=0.3, spring_length=150)
        else:
            nt.force_atlas_2based()

        for node in subG.nodes():
            # Tooltip
            title_str = (f"<b>{node}</b><br>"
                         f"Score: {df.loc[df['Protein']==node, 'Total_Score'].values[0]}<br>"
                         f"BC: {bc[node]:.4f}<br>"
                         f"Deg: {deg[node]}")
            
            # Color Logic
            color = "#97c2fc" # Default blue
            size = 10
            
            if node == target_protein:
                color = "#ff0000"; size = 30; title_str += "<br>(TARGET)"
            elif node in top_candidates:
                color = "#00ff00"; size = 20; title_str += "<br>(BOTTLENECK)"

            nt.add_node(node, title=title_str, color=color, size=size)

        for u, v in subG.edges():
            nt.add_edge(u, v, color="#cccccc")

        html_path = os.path.join(img_dir, f"cluster_{cluster_id}_interactive.html")
        nt.save_graph(html_path)
    
    print(f"[SUCCESS] Analysis finished for {target_protein}.")
    
    # Return dictionary for Notebook use
    return {
        "dataframe": df,
        "html_path": os.path.abspath(html_path) if html_path else None,
        "png_path": os.path.abspath(png_path),
        "cluster_id": cluster_id,
        "error": None
    }