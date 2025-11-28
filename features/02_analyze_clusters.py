import pandas as pd
import networkx as nx
import pickle
import os
import collections
import numpy as np

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_PICKLE_PATH = "data/output/louvain_clust_julle.pkl"
OUTPUT_DIR = "data/output"
OUTPUT_STATS_CSV = "cluster_statistics.csv"

# How many top clusters to display in the notebook output? (Set to None for all)
DISPLAY_TOP_N_ROWS = 20 

def main():
    # ---------------------------------------------------------
    # 1. Setup and Loading
    # ---------------------------------------------------------
    print(f"[INFO] Loading pickle from {INPUT_PICKLE_PATH}...")
    
    if not os.path.exists(INPUT_PICKLE_PATH):
        print(f"[ERROR] Pickle file not found at {INPUT_PICKLE_PATH}")
        print("[HINT] Please run Script 1 (01_run_louvain.py) first.")
        return

    with open(INPUT_PICKLE_PATH, "rb") as f:
        data = pickle.load(f)

    G = data['graph']
    communities = data['communities']

    # ---------------------------------------------------------
    # 2. Process Communities
    # ---------------------------------------------------------
    print("[INFO] Processing community data...")
    
    # Create Node-to-Cluster Dictionary
    node2cluster_id = {}
    for cluster_id, comm in enumerate(communities):
        for n in comm:
            node2cluster_id[n] = cluster_id

    # Calculate Global Stats
    sizes = collections.Counter(node2cluster_id.values())
    median_size = np.median(list(sizes.values()))
    
    print("-" * 40)
    print(f"[STATS] Total Nodes Clustered: {len(node2cluster_id)}")
    print(f"[STATS] Total Communities Detected: {len(communities)}")
    print(f"[STATS] Median cluster size: {median_size:.1f}")
    print("-" * 40)

    # ---------------------------------------------------------
    # 3. Detailed Cluster Analysis
    # ---------------------------------------------------------
    print("[INFO] Calculating detailed statistics per cluster (Density, Clustering Coeff)...")
    
    rows = []
    for cluster_id, comm in enumerate(communities):
        # Create a subgraph for the specific community to calculate internal metrics
        H = G.subgraph(comm)
        
        # Calculate Average Clustering 
        # (Handle single nodes where clustering is undefined/0)
        avg_clust = 0.0
        if H.number_of_nodes() > 1:
            try:
                avg_clust = nx.average_clustering(H, weight="weight")
            except:
                avg_clust = 0.0

        rows.append({
            "Cluster ID": cluster_id,
            "Size (Nodes)": H.number_of_nodes(),
            "Edges": H.number_of_edges(),
            "Density": nx.density(H),
            "Avg Clustering": avg_clust
        })

    # Create DataFrame
    df_clusters = pd.DataFrame(rows)
    
    # Sort by Size (Largest to Smallest)
    df_clusters = df_clusters.sort_values(by="Size (Nodes)", ascending=False).reset_index(drop=True)

    # ---------------------------------------------------------
    # 4. Save to CSV
    # ---------------------------------------------------------
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_csv_path = os.path.join(OUTPUT_DIR, OUTPUT_STATS_CSV)
    df_clusters.to_csv(output_csv_path, index=False)
    print(f"[INFO] Full cluster statistics saved to: {output_csv_path}")

    # ---------------------------------------------------------
    # 5. Display Table for Jupyter Notebook
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print(f"CLUSTER STATISTICS TABLE (Top {DISPLAY_TOP_N_ROWS if DISPLAY_TOP_N_ROWS else 'All'})")
    print("="*60)
    
    # Adjust pandas display settings for this printout to make it pretty
    pd.set_option('display.max_rows', DISPLAY_TOP_N_ROWS)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.float_format', '{:.4f}'.format)
    
    # Print the dataframe as a string (looks like a table)
    if DISPLAY_TOP_N_ROWS:
        print(df_clusters.head(DISPLAY_TOP_N_ROWS).to_string(index=False))
    else:
        print(df_clusters.to_string(index=False))
        
    print("="*60 + "\n")
    print("[DONE] Analysis complete.")

if __name__ == "__main__":
    main()