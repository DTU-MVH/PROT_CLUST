import pandas as pd
import networkx as nx
import markov_clustering as mc
import networkx.algorithms.community as nx_comm
import scipy.sparse
import time
import sys

# ==========================================
#        USER CONFIGURATION VARIABLES
# ==========================================

INPUT_FILENAME = "data/cleaned_data.csv" # Make sure this path matches your folder structure
OUTPUT_CSV_NAME = "data/output/markov_clustered_results.csv"

# --- MCL Parameters for Large Datasets ---
MCL_INFLATION = 2.0
MCL_EXPANSION = 2
MCL_PRUNING_THRESHOLD = 0.001 

def run_large_scale_clustering():
    start_time = time.time()
    print(f"--- [1] Loading data from {INPUT_FILENAME} ---")
    
    try:
        df = pd.read_csv(INPUT_FILENAME)
        df['combined_score'] = df['combined_score'] / 1000.0
    except FileNotFoundError:
        print(f"Error: File {INPUT_FILENAME} not found.")
        sys.exit(1)

    print(f"--- [2] Building Graph ---")
    G = nx.Graph()
    edges_to_add = zip(df['protein1'], df['protein2'], df['combined_score'])
    G.add_weighted_edges_from(edges_to_add)
    
    print(f"    Graph created: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")

    print(f"--- [3] Converting to Sparse Matrix ---")
    # Get the modern sparse array from NetworkX
    matrix_array = nx.to_scipy_sparse_array(G)
    
    # FIX: Explicitly convert to old-style 'csr_matrix' 
    # This ensures markov_clustering uses sparse math instead of crashing on dense math
    matrix = scipy.sparse.csr_matrix(matrix_array)

    print(f"--- [4] Running MCL (Inflation={MCL_INFLATION})... ---")
    
    mcl_start = time.time()
    
    # Run MCL
    result = mc.run_mcl(
        matrix, 
        inflation=MCL_INFLATION, 
        expansion=MCL_EXPANSION, 
        pruning_threshold=MCL_PRUNING_THRESHOLD
    )
    
    clusters_indices = mc.get_clusters(result)
    mcl_duration = time.time() - mcl_start
    print(f"    MCL completed in {mcl_duration:.2f} seconds.")

    print(f"--- [5] Processing Clusters ---")
    nodes_list = list(G.nodes())
    
    # Sort clusters by size
    clusters_indices.sort(key=len, reverse=True)
    
    community_groups = []
    results_data = []

    for cluster_id, indices in enumerate(clusters_indices):
        members = [nodes_list[i] for i in indices]
        community_groups.append(members)
        
        for member in members:
            results_data.append({
                "Protein": member,
                "Cluster_ID": cluster_id + 1,
                "Cluster_Size": len(members)
            })

    print(f"    Found {len(community_groups)} clusters.")

    # ------------------------------------------
    #    CALCULATE MODULARITY
    # ------------------------------------------
    print(f"--- [6] Calculating Modularity Score ---")
    try:
        # Note: On 13k nodes, if this freezes, simply comment the next two lines out
        mod_score = nx_comm.modularity(G, community_groups, weight='weight')
        print(f"    Modularity (Q): {mod_score:.4f}")
    except Exception as e:
        print(f"    Skipping modularity calculation due to error: {e}")

    # ------------------------------------------
    #    EXPORT TO CSV
    # ------------------------------------------
    print(f"--- [7] Saving results to {OUTPUT_CSV_NAME} ---")
    results_df = pd.DataFrame(results_data)
    results_df.to_csv(OUTPUT_CSV_NAME, index=False)
    
    print("\nTop 5 largest clusters:")
    for i in range(min(5, len(community_groups))):
        print(f"  Cluster {i+1}: {len(community_groups[i])} proteins")

    total_time = time.time() - start_time
    print(f"\nTotal Script Runtime: {total_time:.2f} seconds")


run_large_scale_clustering()