import networkx as nx
import pickle
import os
import matplotlib.pyplot as plt

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_PICKLE_PATH = "data/output/louvain_clust_julle.pkl"
OUTPUT_DIR = "data/output"
IMAGE_DIR = "data/output/images"
TARGET_PROTEIN = "SNCAIP"  # Change this to query different proteins
TOP_N_RANKING = 40

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)

    # 1. Load Data
    print(f"[INFO] Loading data...")
    if not os.path.exists(INPUT_PICKLE_PATH):
        print("Pickle not found.")
        return

    with open(INPUT_PICKLE_PATH, "rb") as f:
        data = pickle.load(f)
    
    G = data['graph']
    communities = data['communities']

    # 2. Map nodes to clusters
    node2cluster_id = {}
    for cluster_id, comm in enumerate(communities):
        for n in comm:
            node2cluster_id[n] = cluster_id

    # 3. Locate Target
    if TARGET_PROTEIN not in node2cluster_id:
        print(f"[ERROR] Target protein '{TARGET_PROTEIN}' not found in the network.")
        return

    target_cluster_id = node2cluster_id[TARGET_PROTEIN]
    print(f"[INFO] Target '{TARGET_PROTEIN}' found in Cluster ID: {target_cluster_id}")

    # Extract nodes for target cluster and background
    target_nodes = {n for n, c in node2cluster_id.items() if c == target_cluster_id}
    
    # Save Target Cluster Nodes
    with open(os.path.join(OUTPUT_DIR, "target_cluster_nodes.txt"), "w") as f:
        f.write(repr(list(target_nodes)))
    
    print(f"[INFO] Extracted target cluster with {len(target_nodes)} nodes.")

    # 4. Bottleneck Analysis on Subgraph
    print("[INFO] Performing bottleneck analysis on target subgraph...")
    target_subgraph = G.subgraph(target_nodes).copy()

    # A. Betweenness Centrality
    bc_scores = nx.betweenness_centrality(target_subgraph, weight="weight", normalized=True)
    
    # B. Degree Centrality (Node Degree)
    deg_scores = dict(target_subgraph.degree())
    
    # C. Clustering Coefficient
    clust_scores = nx.clustering(target_subgraph, weight="weight")

    # 5. Combined Ranking Calculation
    # We rank proteins based on: High BC + High Degree + Low Clustering Coefficient
    
    # Sort and create rank lookup dictionaries
    sorted_bc = sorted(bc_scores.items(), key=lambda x: x[1], reverse=True)[:TOP_N_RANKING]
    bc_ranks = {p: i+1 for i, (p, _) in enumerate(sorted_bc)}

    sorted_deg = sorted(deg_scores.items(), key=lambda x: x[1], reverse=True)[:TOP_N_RANKING]
    deg_ranks = {p: i+1 for i, (p, _) in enumerate(sorted_deg)}

    # Ascending sort for clustering (we want LOW clustering)
    sorted_clust = sorted(clust_scores.items(), key=lambda x: x[1], reverse=False)[:TOP_N_RANKING]
    clust_ranks = {p: i+1 for i, (p, _) in enumerate(sorted_clust)}

    # Calculate combined rank
    # Note: If a protein is not in the Top N for a specific metric, we apply a penalty rank (TOP_N + 1)
    unique_proteins = set(bc_ranks.keys()) | set(deg_ranks.keys()) | set(clust_ranks.keys())
    
    combined_results = []
    for p in unique_proteins:
        r_bc = bc_ranks.get(p, TOP_N_RANKING + 1)
        r_deg = deg_ranks.get(p, TOP_N_RANKING + 1)
        r_clust = clust_ranks.get(p, TOP_N_RANKING + 1)
        
        total_rank_score = r_bc + r_deg + r_clust
        combined_results.append({
            "Protein": p,
            "BC_Rank": r_bc,
            "Deg_Rank": r_deg,
            "Clust_Rank": r_clust,
            "Total_Score": total_rank_score
        })

    # Sort by total score (lower is better)
    combined_results.sort(key=lambda x: x["Total_Score"])

    # 6. Output Ranking Results
    print(f"\n[RESULTS] Top 10 Bottleneck Candidates in Cluster {target_cluster_id}:")
    print(f"{'Rank':<5} {'Protein':<15} {'Total':<8} {'BC':<5} {'Deg':<5} {'Clust':<5}")
    print("-" * 50)
    
    for i, res in enumerate(combined_results[:10], 1):
        print(f"{i:<5} {res['Protein']:<15} {res['Total_Score']:<8} {res['BC_Rank']:<5} {res['Deg_Rank']:<5} {res['Clust_Rank']:<5}")

    # 7. Visualization of Top Candidates in Subgraph
    top_candidates = [res['Protein'] for res in combined_results[:10]]
    
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(target_subgraph, seed=42)
    
    # Draw all nodes
    nx.draw_networkx_nodes(target_subgraph, pos, node_size=30, node_color='lightgrey', alpha=0.6)
    nx.draw_networkx_edges(target_subgraph, pos, alpha=0.1)
    
    # Highlight Target and Top Bottlenecks
    # Highlight original target
    if TARGET_PROTEIN in pos:
        nx.draw_networkx_nodes(target_subgraph, pos, nodelist=[TARGET_PROTEIN], node_color='red', node_size=150, label="Query Target")
    
    # Highlight top bottlenecks
    nx.draw_networkx_nodes(target_subgraph, pos, nodelist=top_candidates, node_color='blue', node_size=100, label="Bottlenecks")
    
    # Labels for top candidates only to avoid clutter
    labels = {n: n for n in top_candidates}
    labels[TARGET_PROTEIN] = TARGET_PROTEIN
    nx.draw_networkx_labels(target_subgraph, pos, labels=labels, font_size=8, font_weight="bold")

    plt.title(f"Target Cluster: {target_cluster_id} (Query: {TARGET_PROTEIN})")
    plt.legend()
    plt.axis('off')
    
    plot_path = os.path.join(IMAGE_DIR, f"cluster_{target_cluster_id}_bottlenecks.png")
    plt.savefig(plot_path)
    print(f"\n[INFO] Cluster visualization saved to {plot_path}")
    print("[DONE] Script 4 completed.")

if __name__ == "__main__":
    main()