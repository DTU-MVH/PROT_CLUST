"""
Module: cluster_overview.py
Description: 
    Provides functions to inspect the general properties of the graph clustering.
    1. Summary of the whole network (modularity, sizes) - Displays all.
    2. Detailed statistics table for every cluster - Displays Top 20.
    3. Extraction of protein lists from specific clusters - Displays Top 50.
"""

import pandas as pd
import networkx as nx
import numpy as np
import pickle
import os
from IPython.display import display

def _load_pickle_data(pickle_path):
    """Helper function to load data safely."""
    if not os.path.exists(pickle_path):
        return None, f"File not found: {pickle_path}"
    
    try:
        with open(pickle_path, "rb") as f:
            data = pickle.load(f)
        return data, None
    except Exception as e:
        return None, str(e)

def get_clustering_summary(pickle_path):
    """
    1. Creates and DISPLAYS a high-level summary table of the clustering results.

    Parameters:
        pickle_path (str): Path to the .pkl file containing the graph object.

    Returns:
        pd.DataFrame: A single-row DataFrame containing key metrics.
    """
    print(f"\n[OVERVIEW] Generating global network summary...")
    
    data, error = _load_pickle_data(pickle_path)
    if error:
        print(f"❌ Error: {error}")
        return None

    communities = data['communities']
    modularity_score = data.get('modularity', 0.0)

    # Calculate size statistics
    cluster_sizes = [len(c) for c in communities]
    
    summary_data = {
        "Total Clusters": [len(communities)],
        "Avg Cluster Size": [round(np.mean(cluster_sizes), 2)],
        "Median Cluster Size": [np.median(cluster_sizes)],
        "Largest Cluster": [np.max(cluster_sizes)],
        "Smallest Cluster": [np.min(cluster_sizes)],
        "Modularity Score": [round(modularity_score, 4)]
    }

    df_summary = pd.DataFrame(summary_data)
    
    # DISPLAY OUTPUT
    print("\n--- Network Summary ---")
    display(df_summary.style.hide(axis='index'))
    
    return df_summary

def generate_cluster_stats_table(pickle_path, output_filename, output_dir="data/output"):
    """
    2. Calculates stats for ALL clusters, saves to CSV, and DISPLAYS Top 20.

    Parameters:
        pickle_path (str): Path to the .pkl file.
        output_filename (str): Name of the CSV file to create.
        output_dir (str): Folder to save the CSV.

    Returns:
        pd.DataFrame: The full dataframe.
    """
    print(f"\n[OVERVIEW] Calculating statistics for all clusters...")
    
    data, error = _load_pickle_data(pickle_path)
    if error:
        print(f"❌ Error: {error}")
        return None

    G = data['graph']
    communities = data['communities']
    
    stats_rows = []

    for cluster_id, nodes in enumerate(communities):
        subG = G.subgraph(nodes)
        
        num_nodes = subG.number_of_nodes()
        num_edges = subG.number_of_edges()
        density = nx.density(subG)
        
        try:
            avg_clust = nx.average_clustering(subG, weight="weight")
        except:
            avg_clust = 0.0

        stats_rows.append({
            "Cluster ID": cluster_id,
            "Size (Nodes)": num_nodes,
            "Edges": num_edges,
            "Density": round(density, 4),
            "Avg Clustering": round(avg_clust, 4)
        })

    # Sort by Size
    df = pd.DataFrame(stats_rows).sort_values(by="Size (Nodes)", ascending=False).reset_index(drop=True)

    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, output_filename)
    df.to_csv(full_path, index=False)
    print(f"   ✅ Stats saved to: {full_path}")

    # DISPLAY OUTPUT (Top 20)
    print("\n--- Top 20 Largest Clusters ---")
    display(df.head(20).style.format({"Density": "{:.4f}", "Avg Clustering": "{:.4f}"}).background_gradient(subset=["Size (Nodes)"], cmap="Blues"))
    
    return df

def get_proteins_in_cluster(pickle_path, cluster_id, output_filename, output_dir="data/output"):
    """
    3. Extracts proteins from a cluster, saves to file, and DISPLAYS Top 50.

    Parameters:
        pickle_path (str): Path to the .pkl file.
        cluster_id (int): The ID of the cluster.
        output_filename (str): Name of the text file to save.
        output_dir (str): Folder to save the file.

    Returns:
        list: The list of proteins.
    """
    print(f"\n[OVERVIEW] Fetching proteins for Cluster ID {cluster_id}...")

    data, error = _load_pickle_data(pickle_path)
    if error:
        print(f"❌ Error: {error}")
        return None

    communities = data['communities']

    if cluster_id < 0 or cluster_id >= len(communities):
        print(f"❌ Error: Cluster ID {cluster_id} invalid.")
        return None

    protein_list = sorted(list(communities[cluster_id]))
    
    # Save to file
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, output_filename)
    
    with open(full_path, "w") as f:
        for protein in protein_list:
            f.write(f"{protein}\n")

    print(f"   ✅ Saved list to: {full_path}")

    # DISPLAY OUTPUT (Top 50)
    top_50 = protein_list[:50]
    total_count = len(protein_list)
    
    print(f"\n--- Proteins in Cluster {cluster_id} (Showing top 50 of {total_count}) ---")
    
    # Print as a nice comma-separated block for readability
    print(", ".join(top_50))
    
    if total_count > 50:
        print(f"... and {total_count - 50} more.")
    
    return protein_list