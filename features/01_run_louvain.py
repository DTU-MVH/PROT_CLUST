import pandas as pd
import networkx as nx
from networkx.algorithms.community import louvain_communities, modularity
import pickle
import time
import os

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_CSV_PATH = "data/cleaned_data.csv"
OUTPUT_DIR = "data/output"
OUTPUT_PICKLE_NAME = "louvain_clust_julle.pkl"
LOUVAIN_RESOLUTION = 1.0
RANDOM_SEED = 42

def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"[INFO] Loading data from {INPUT_CSV_PATH}...")
    try:
        # Load interaction data
        df_interactions = pd.read_csv(INPUT_CSV_PATH)
    except FileNotFoundError:
        print(f"[ERROR] Input file not found at {INPUT_CSV_PATH}")
        return

    # Build Weighted Graph
    print("[INFO] Building NetworkX graph...")
    G = nx.Graph()
    # Iterate efficiently using zip for speed over pandas rows
    for p1, p2, score in zip(df_interactions['protein1'], 
                             df_interactions['protein2'], 
                             df_interactions['combined_score']):
        G.add_edge(p1, p2, weight=score)

    print(f"[STATS] Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    # Run Louvain Clustering
    print(f"[INFO] Running Louvain clustering (Resolution={LOUVAIN_RESOLUTION})...")
    t0 = time.time()
    communities = louvain_communities(G, weight='weight', resolution=LOUVAIN_RESOLUTION, seed=RANDOM_SEED)
    t1 = time.time()
    
    # Calculate Modularity
    mod_score = modularity(G, communities, weight='weight')
    
    print(f"[RESULT] Detected {len(communities)} communities in {t1 - t0:.2f}s")
    print(f"[RESULT] Global Modularity: {mod_score:.4f}")

    # Prepare data for pickling
    # We save both the graph object and the communities list
    data_to_save = {
        "graph": G,
        "communities": communities,
        "modularity": mod_score,
        "parameters": {
            "resolution": LOUVAIN_RESOLUTION,
            "seed": RANDOM_SEED
        }
    }

    # Save to Pickle
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_PICKLE_NAME)
    print(f"[INFO] Saving results to {output_path}...")
    with open(output_path, "wb") as f:
        pickle.dump(data_to_save, f)
    
    print("[DONE] Script 1 completed successfully.")

if __name__ == "__main__":
    main()