import pandas as pd
import networkx as nx
import pickle
import time
import os
import sys
import scipy.sparse
from networkx.algorithms.community import modularity

# Try importing markov_clustering
try:
    import markov_clustering as mc
except ImportError:
    print("❌ Error: 'markov_clustering' library not installed.")
    print("   Please run: pip install markov_clustering")
    sys.exit(1)

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_CSV_PATH = "data/cleaned_data.csv"
OUTPUT_DIR = "data/output"
OUTPUT_PICKLE_NAME = "mcl_data.pkl"

# MCL Parameters
MCL_INFLATION = 2.0       # Controls granularity (1.4 = coarse, 4.0 = fine)
MCL_EXPANSION = 2         # Power parameter (usually 2)
MCL_PRUNING_THRESHOLD = 0.001 # Prune weak connections for speed

def main():
    # 1. Setup
    start_total = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_PICKLE_NAME)

    print(f"--- 🚀 Starting MCL Clustering ---")
    print(f"    Input: {INPUT_CSV_PATH}")
    print(f"    Output: {output_path}")
    print(f"    Inflation: {MCL_INFLATION}")

    # 2. Load Data & Normalize
    if not os.path.exists(INPUT_CSV_PATH):
        print(f"❌ Error: Input file not found at {INPUT_CSV_PATH}")
        return

    print("[1/5] Loading data...")
    df = pd.read_csv(INPUT_CSV_PATH)
    
    # NORMALIZATION: MCL works best with weights between 0.0 and 1.0
    # We assume 'combined_score' is 0-1000 (standard StringDB format)
    df['combined_score'] = df['combined_score'] / 1000.0

    # 3. Build Graph
    print("[2/5] Building NetworkX graph...")
    G = nx.Graph()
    # Efficiently add edges
    for p1, p2, score in zip(df['protein1'], df['protein2'], df['combined_score']):
        G.add_edge(p1, p2, weight=score)

    nodes_list = list(G.nodes())
    print(f"      Nodes: {G.number_of_nodes()}")
    print(f"      Edges: {G.number_of_edges()}")

    # 4. Convert to Matrix for MCL
    print("[3/5] Converting to sparse matrix...")
    # Convert to scipy sparse array (compatible with modern NetworkX)
    matrix = nx.to_scipy_sparse_array(G, nodelist=nodes_list)
    # Ensure it is a CSR matrix for the library
    matrix = scipy.sparse.csr_matrix(matrix)

    # 5. Run MCL Algorithm
    print("[4/5] Running Markov Clustering (this may take time)...")
    t0 = time.time()
    
    result = mc.run_mcl(
        matrix, 
        inflation=MCL_INFLATION, 
        expansion=MCL_EXPANSION, 
        pruning_threshold=MCL_PRUNING_THRESHOLD
    )
    
    # Get clusters (returns list of tuples containing indices)
    clusters_indices = mc.get_clusters(result)
    t1 = time.time()
    print(f"      MCL finished in {t1-t0:.2f} seconds.")

    # 6. Process & Format Data
    print("[5/5] Processing results...")
    
    # Sort clusters by size (Largest first)
    clusters_indices.sort(key=len, reverse=True)
    
    communities = []
    node2cluster = {}
    
    # Map numerical indices back to Protein Names
    for cid, indices in enumerate(clusters_indices):
        # Create a set of names for this cluster
        members = {nodes_list[i] for i in indices}
        communities.append(members)
        
        # Populate lookup dictionary
        for member in members:
            node2cluster[member] = cid

    # Calculate Modularity (Useful for comparison with Louvain)
    print("      Calculating modularity score...")
    try:
        mod_score = modularity(G, communities, weight='weight')
    except:
        mod_score = 0.0

    # Bundle data into the standard format expected by analysis modules
    data_bundle = {
        "graph": G,
        "communities": communities,
        "node2cluster": node2cluster,
        "modularity": mod_score,
        "params": {
            "algorithm": "MCL",
            "inflation": MCL_INFLATION,
            "expansion": MCL_EXPANSION
        }
    }

    # 7. Save to Pickle
    print(f"      Saving to {output_path}...")
    with open(output_path, "wb") as f:
        pickle.dump(data_bundle, f)

    print("-" * 30)
    print(f"✅ DONE! Total clusters found: {len(communities)}")
    print(f"   Total runtime: {time.time() - start_total:.2f}s")
    print(f"   You can now analyze this file using: mcl_data.pkl")

if __name__ == "__main__":
    main()