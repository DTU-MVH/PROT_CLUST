import networkx as nx
import pickle

# 1. Load the pre-calculated graph
print("Loading graph...")
with open("data/output/louvain_annotated_graph.pkl", "rb") as f:
    G = pickle.load(f)

# 2. Access Cluster Information
# Access the attribute 'cluster_id' we saved earlier
node_name = "CHMP2B" # Example protein
if node_name in G:
    cluster = G.nodes[node_name]['cluster_id']
    print(f"{node_name} is in cluster {cluster}")

# 3. Access Connectivity (Edges)
# Edges are preserved
neighbors = list(G.neighbors(node_name))
print(f"{node_name} interacts with: {neighbors}")

# 4. Filter specific clusters
target_cluster_id = 0
nodes_in_cluster_0 = [n for n, attrs in G.nodes(data=True) 
                      if attrs['cluster_id'] == target_cluster_id]

print(f"Cluster 0 has {len(nodes_in_cluster_0)} nodes.")