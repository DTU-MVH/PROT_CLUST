import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from networkx.algorithms.community import louvain_communities
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
import itertools
import pickle
import os

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_PICKLE_PATH = "data/output/louvain_clust_julle.pkl"
OUTPUT_DIR = "data/output/images"
SEEDS = [1, 50, 100, 200, 500, 1000, 3000, 5000, 7000, 10000]
RESOLUTION = 1.0

def communities_to_labels(communities, nodes):
    """
    Convert a list of sets (communities) into a list of labels 
    matching the order of the nodes list for sklearn metrics.
    """
    node2label = {}
    for label, comm in enumerate(communities):
        for n in comm:
            node2label[n] = label
    return [node2label[n] for n in nodes]

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load Graph
    print(f"[INFO] Loading graph from {INPUT_PICKLE_PATH}...")
    with open(INPUT_PICKLE_PATH, "rb") as f:
        data = pickle.load(f)
    G = data['graph']
    
    nodes_list = list(G.nodes())
    all_community_sets = []

    print(f"[INFO] Running Louvain {len(SEEDS)} times to test reproducibility...")

    # Run clustering multiple times
    for s in SEEDS:
        print(f"   > Running seed {s}...")
        comms = louvain_communities(G, weight='weight', resolution=RESOLUTION, seed=s)
        all_community_sets.append(comms)

    # Convert to label vectors for comparison
    label_vectors = [communities_to_labels(comms, nodes_list) for comms in all_community_sets]

    # Compute pairwise ARI and NMI
    ari_scores = []
    nmi_scores = []

    print("[INFO] Computing pairwise ARI and NMI scores...")
    for vec1, vec2 in itertools.combinations(label_vectors, 2):
        ari_scores.append(adjusted_rand_score(vec1, vec2))
        nmi_scores.append(normalized_mutual_info_score(vec1, vec2))

    mean_ari = np.mean(ari_scores)
    mean_nmi = np.mean(nmi_scores)

    print("-" * 30)
    print(f"Reproducibility Results ({len(SEEDS)} runs):")
    print(f"Mean Adjusted Rand Index (ARI): {mean_ari:.4f} ± {np.std(ari_scores):.4f}")
    print(f"Mean Normalized Mutual Info (NMI): {mean_nmi:.4f} ± {np.std(nmi_scores):.4f}")
    print("-" * 30)

    # Visualization: Cluster Size Distributions
    print("[INFO] Generating reproducibility plot...")
    plt.figure(figsize=(10, 6))
    for i, comms in enumerate(all_community_sets):
        sizes = [len(c) for c in comms]
        # Sort sizes descending for 'Zipf' style plot
        plt.plot(sorted(sizes, reverse=True), label=f"seed={SEEDS[i]}", alpha=0.7)
    
    plt.xlabel("Cluster Rank")
    plt.ylabel("Cluster Size")
    plt.title("Cluster Size Distributions (Reproducibility Check)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    plot_path = os.path.join(OUTPUT_DIR, "reproducibility_plot.png")
    plt.savefig(plot_path)
    print(f"[INFO] Plot saved to {plot_path}")
    print("[DONE] Script 3 completed.")

if __name__ == "__main__":
    main()