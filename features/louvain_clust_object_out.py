import pandas as pd
import networkx as nx
import numpy as np
import time
import os
import pickle
from networkx.algorithms.community import louvain_communities, modularity

# =============================================================================
# SECTION 1: INPUT VARIABLES & CONFIGURATION
# =============================================================================

# Input file path
INPUT_FILE_PATH = "data/cleaned_data.csv" 

# Output settings
OUTPUT_DIR = "data/output"
# We use .pkl (pickle) to save the full Python object
OUTPUT_FILENAME = "louvain_annotated_graph.pkl" 
FULL_OUTPUT_PATH = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

# CSV Column Mapping
COL_SOURCE = "protein1"
COL_TARGET = "protein2"
COL_WEIGHT = "combined_score"

# Louvain Parameters
LOUVAIN_RESOLUTION = 1.0 
LOUVAIN_SEED = 42 

# =============================================================================
# SECTION 2: MAIN EXECUTION
# =============================================================================

def main():
    print("--- Starting Graph Clustering and Annotation ---")
    
    # 1. LOAD DATA
    print(f"Reading data from: {INPUT_FILE_PATH}")
    if not os.path.exists(INPUT_FILE_PATH):
        print(f"Error: Input file not found at {INPUT_FILE_PATH}")
        return

    try:
        df = pd.read_csv(INPUT_FILE_PATH, usecols=[COL_SOURCE, COL_TARGET, COL_WEIGHT])
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # 2. BUILD GRAPH
    print("Building NetworkX Graph...")
    G = nx.Graph()
    edges = list(zip(df[COL_SOURCE], df[COL_TARGET], df[COL_WEIGHT]))
    G.add_weighted_edges_from(edges)
    
    print(f"Graph constructed.")
    print(f" - Nodes: {G.number_of_nodes()}")
    print(f" - Edges: {G.number_of_edges()}")

    # 3. RUN LOUVAIN CLUSTERING
    print(f"\nRunning Louvain Algorithm (Resolution={LOUVAIN_RESOLUTION})...")
    t0 = time.time()
    
    # Returns a list of sets [{node, node}, {node, node}]
    communities = louvain_communities(
        G, 
        weight='weight', 
        resolution=LOUVAIN_RESOLUTION, 
        seed=LOUVAIN_SEED
    )
    
    t1 = time.time()
    print(f"Clustering complete in {t1 - t0:.2f} seconds.")

    # 4. EMBED CLUSTER INFO INTO GRAPH
    print("Embedding cluster IDs into graph nodes...")
    
    # Create a dictionary mapping: Node -> Cluster ID
    cluster_mapping = {}
    for cluster_id, node_set in enumerate(communities):
        for node in node_set:
            cluster_mapping[node] = cluster_id
            
    # Add 'cluster_id' as a property to every node in the graph object
    nx.set_node_attributes(G, cluster_mapping, "cluster_id")

    # 5. CALCULATE STATISTICS
    print("\nCalculating statistics...")
    mod_score = modularity(G, communities, weight='weight')
    community_sizes = [len(c) for c in communities]
    community_sizes.sort(reverse=True)

    # 6. PRINT TERMINAL SUMMARY
    print("\n" + "="*40)
    print("CLUSTERING SUMMARY")
    print("="*40)
    print(f"Total Clusters Detected: {len(communities)}")
    print(f"Modularity Score:        {mod_score:.4f}")
    print("-" * 40)
    print("Largest 10 Clusters (by node count):")
    for i, size in enumerate(community_sizes[:10]):
        print(f"  Rank {i+1}: {size} nodes")
    print("="*40)

    # 7. SAVE FULL GRAPH OBJECT (PICKLE)
    print(f"\nSaving full graph object to: {FULL_OUTPUT_PATH}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        with open(FULL_OUTPUT_PATH, 'wb') as f:
            pickle.dump(G, f)
        print("Success! The graph (nodes, edges, weights, and cluster IDs) is saved.")
    except Exception as e:
        print(f"Error saving pickle file: {e}")

# =============================================================================
# SECTION 3: HOW TO LOAD EXAMPLE
# =============================================================================
def show_loading_example():
    """
    This function runs strictly to demonstrate how to read the file later.
    """
    print("\n" + "-"*40)
    print("EXAMPLE: Verifying file reload...")
    
    try:
        with open(FULL_OUTPUT_PATH, 'rb') as f:
            G_loaded = pickle.load(f)
        
        print("Graph loaded successfully!")
        
        # Verify data exists
        sample_node = list(G_loaded.nodes())[0]
        cluster_id = G_loaded.nodes[sample_node].get('cluster_id')
        neighbors = list(G_loaded.neighbors(sample_node))
        
        print(f"Sample Node: {sample_node}")
        print(f" -> Belongs to Cluster: {cluster_id}")
        print(f" -> Has {len(neighbors)} connections (edges preserved).")
        
    except Exception as e:
        print(f"Verification failed: {e}")


main()
    # Uncomment the line below if you want to verify the file immediately after running
    # show_loading_example()