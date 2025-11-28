import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")
"""
Module: enrichment_analysis.py
Description: 
    Performs Over-Representation Analysis (ORA) on a specific cluster 
    using the gseapy library and MSigDB Hallmark gene sets.
"""

import pandas as pd
import pickle
import os
import sys
from IPython.display import display

# Try importing gseapy
try:
    import gseapy as gp
    GSEAPY_AVAILABLE = True
except ImportError:
    GSEAPY_AVAILABLE = False

def run_enrichment_analysis(target_protein, pickle_path, output_dir):
    """
    Runs ORA on the cluster containing the target protein.

    Parameters:
        target_protein (str): The name of the protein to analyze (e.g., "SNCAIP").
        pickle_path (str): Path to the .pkl file (Louvain or MCL data).
        output_dir (str): Directory where results will be saved.

    Returns:
        pd.DataFrame: The enrichment results dataframe (or None if failed).
    """

    if not GSEAPY_AVAILABLE:
        print("❌ Error: 'gseapy' library not installed.")
        print("   Run: pip install gseapy")
        return None

    print(f"\n--- 🧬 Enrichment Analysis: {target_protein} ---")

    # --- 1. Load Data ---
    if not os.path.exists(pickle_path):
        print(f"❌ Error: Pickle file not found at {pickle_path}")
        return None

    try:
        with open(pickle_path, "rb") as f:
            data = pickle.load(f)
        
        # We need communities list and graph nodes for background
        communities = data['communities']
        G = data['graph']
        
        # Rebuild node map if needed (or use existing)
        if 'node2cluster' in data:
            node2cluster = data['node2cluster']
        else:
            node2cluster = {}
            for cid, comm in enumerate(communities):
                for node in comm:
                    node2cluster[node] = cid

    except Exception as e:
        print(f"❌ Error loading pickle: {e}")
        return None

    # --- 2. Identify Target Cluster ---
    if target_protein not in node2cluster:
        print(f"❌ Error: Protein '{target_protein}' not found in the graph.")
        return None

    cluster_id = node2cluster[target_protein]
    target_gene_list = list(communities[cluster_id])
    
    print(f"[INFO] Target found in Cluster #{cluster_id}")
    print(f"[INFO] Analyzing {len(target_gene_list)} genes against Hallmark pathways...")

    # --- 3. Define Background ---
    # Background is ALL nodes in the graph
    background_gene_list = list(G.nodes())
    print(f"[INFO] Background size: {len(background_gene_list)} genes")

    # --- 4. Run ORA with gseapy ---
    try:
        print("[INFO] Fetching Hallmark gene sets and running ORA...")
        
        # We use the 'enrichr' function which uses the Enrichr API (requires internet)
        # Alternatively, use 'prerank' or 'enrich' if you have local .gmt files.
        # Using 'MSigDB_Hallmark_2020' is a safe standard.
        
        enr = gp.enrichr(
            gene_list=target_gene_list,
            gene_sets='MSigDB_Hallmark_2020', # Uses online library
            background=background_gene_list,
            organism='Human',
            outdir=None, # Don't auto-save, we handle it manually
            verbose=False
        )

        if enr.results is None or enr.results.empty:
            print("[RESULT] No statistically significant pathways found.")
            return None
        
        # Process results
        results_df = enr.results.sort_values('Adjusted P-value')
        
        # Filter for significant results (optional threshold, e.g. 0.05)
        sig_results = results_df[results_df['Adjusted P-value'] < 0.05]
        
        # Save to CSV
        os.makedirs(output_dir, exist_ok=True)
        csv_path = os.path.join(output_dir, f"enrichment_cluster_{cluster_id}.csv")
        results_df.to_csv(csv_path, index=False)
        print(f"   ✅ Full results saved to: {csv_path}")

        # --- 5. Display ---
        print("\n--- Top Enriched Pathways (Adj. P-value < 0.05) ---")
        
        cols_to_show = ['Term', 'Overlap', 'P-value', 'Adjusted P-value', 'Genes']
        
        if not sig_results.empty:
            # Format for display (scientific notation for p-values)
            display_df = sig_results[cols_to_show].head(10).style.format({
                'P-value': '{:.2e}',
                'Adjusted P-value': '{:.2e}'
            })
            display(display_df)
        else:
            print("No pathways met the significance threshold (Adj. P < 0.05).")
            print("Showing top 5 raw results instead:")
            display(results_df[cols_to_show].head(5))

        return results_df

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None