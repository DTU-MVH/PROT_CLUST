import pandas as pd
import networkx as nx
import markov_clustering as mc
import networkx.algorithms.community as nx_comm
import scipy.sparse
import time
import sys
import os
import pickle

# ==========================================
#        USER CONFIGURATION VARIABLES
# ==========================================

INPUT_FILENAME = "data/cleaned_data.csv" 

# Output Settings
OUTPUT_DIR = "data/output"
OUTPUT_FILENAME = "mcl_annotated_graph.pkl" # Saving as a Python object (Pickle)
FULL_OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

# --- MCL Parameters ---
# Inflation affects cluster granularity (higher = more, smaller clusters)
MCL_INFLATION = 2.0
MCL_EXPANSION = 2
MCL_PRUNING_THRESHOLD = 0.001 

def run_large_scale_clustering():
    start_time = time.time()
    print(f"--- [1] Loading data from {INPUT_FILENAME} ---")
    
    # 1. Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Read Data
    try:
        df = pd.read_csv(INPUT_FILENAME)
        # Normalize weights (MCL works best with weights, usually 0.0 to 1.0)
        # Assuming combined_score is 0-1000
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
    # The order of nodes in nodes_list corresponds to rows/cols in the matrix
    nodes_list = list(G.nodes())
    matrix_array = nx.to_scipy_sparse_array(G, nodelist=nodes_list)
    
    # Explicitly convert to old-style 'csr_matrix' for the markov_clustering library
    matrix = scipy.sparse.csr_matrix(matrix_array)

    print(f"--- [4] Running MCL (Inflation={MCL_INFLATION})... ---")
    mcl_start = time.time()
    
    # Run MCL Algorithm
    result = mc.run_mcl(
        matrix, 
        inflation=MCL_INFLATION, 
        expansion=MCL_EXPANSION, 
        pruning_threshold=MCL_PRUNING_THRESHOLD
    )
    
    # Get clusters (list of tuples, where values are indices in nodes_list)
    clusters_indices = mc.get_clusters(result)
    
    mcl_duration = time.time() - mcl_start
    print(f"    MCL completed in {mcl_duration:.2f} seconds.")

    print(f"--- [5] Processing and Embedding Clusters into Graph ---")
    
    # Sort clusters by size (Largest = Cluster 0)
    clusters_indices.sort(key=len, reverse=True)
    
    # Create a mapping: Node Name -> Cluster ID
    cluster_mapping = {}
    
    # We also keep a list form for modularity calculation
    community_groups = []

    for cluster_id, indices in enumerate(clusters_indices):
        # Convert matrix indices back to Protein Names
        members = [nodes_list[i] for i in indices]
        community_groups.append(members)
        
        # Map every protein to its new Cluster ID
        for member in members:
            cluster_mapping[member] = cluster_id

    # Update the NetworkX Graph object with the Cluster IDs
    nx.set_node_attributes(G, cluster_mapping, "cluster_id")
    
    print(f"    Attributes attached. Found {len(community_groups)} clusters.")

    # ------------------------------------------
    #    CALCULATE STATISTICS
    # ------------------------------------------
    print(f"--- [6] Calculating Statistics ---")
    
    # Print top 5 clusters
    print("    Top 5 largest clusters:")
    for i in range(min(5, len(community_groups))):
        print(f"      Cluster {i}: {len(community_groups[i])} proteins")

    # Calculate Modularity
    try:
        mod_score = nx_comm.modularity(G, community_groups, weight='weight')
        print(f"    Modularity (Q): {mod_score:.4f}")
    except Exception as e:
        print(f"    Skipping modularity calculation due to error: {e}")

    # ------------------------------------------
    #    SAVE AS PICKLE OBJECT
    # ------------------------------------------
    print(f"--- [7] Saving Graph Object to {FULL_OUTPUT_PATH} ---")
    
    try:
        with open(FULL_OUTPUT_PATH, 'wb') as f:
            pickle.dump(G, f)
        print("    Success! The graph (nodes, edges, weights, and MCL cluster IDs) is saved.")
    except Exception as e:
        print(f"    Error saving pickle file: {e}")

    total_time = time.time() - start_time
    print(f"\nTotal Script Runtime: {total_time:.2f} seconds")

# =============================================================================
# SECTION: HOW TO LOAD (EXAMPLE)
# =============================================================================
def verify_loading():
    """Run this to verify the file works as expected."""
    print("\n--- Verifying Load ---")
    if os.path.exists(FULL_OUTPUT_PATH):
        with open(FULL_OUTPUT_PATH, 'rb') as f:
            G_loaded = pickle.load(f)
        
        # Check a random node
        test_node = list(G_loaded.nodes())[0]
        cluster = G_loaded.nodes[test_node].get('cluster_id')
        print(f"    Loaded Graph with {G_loaded.number_of_nodes()} nodes.")
        print(f"    Sample Check: Node '{test_node}' is in Cluster {cluster}")
    else:
        print("    Output file not found.")


run_large_scale_clustering()
# verify_loading() # Uncomment to test immediately