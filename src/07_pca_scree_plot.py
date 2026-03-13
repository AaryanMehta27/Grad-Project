"""
07_pca_scree_plot.py
====================
Generate a publication-quality PCA scree plot for BERT embeddings,
justifying the choice of 20 components for dimensionality reduction.

Shows cumulative explained variance vs. number of PCA components,
with vertical marker at the selected cutoff (20) and 95% threshold.

Author: Aarya
Date:   2026-03-08
"""
import sys
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.decomposition import PCA

sys.path.insert(0, str(Path(__file__).parent))
from utils import setup_logging, FIGURES_DIR, load_onet_file

logger = setup_logging("07_pca_scree_plot")


def main():
    logger.info("=" * 70)
    logger.info("PCA VARIANCE EXPLAINED ANALYSIS")
    logger.info("(BERT all-MiniLM-L6-v2 Embeddings of O*NET Task Statements)")
    logger.info("=" * 70)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Step 1: Load task statements (same as 01_data_preparation.py)
    # ------------------------------------------------------------------
    logger.info("\nStep 1: Loading O*NET task statements...")
    tasks_df = load_onet_file('task_statements')
    logger.info(f"  Total task statement rows: {len(tasks_df)}")

    # Concatenate all tasks per occupation
    task_text = tasks_df.groupby('O*NET-SOC Code')['Task'].apply(
        lambda x: ' '.join(x.dropna().astype(str))
    )
    logger.info(f"  Occupations with task text: {len(task_text)}")

    # ------------------------------------------------------------------
    # Step 2: Generate BERT embeddings
    # ------------------------------------------------------------------
    logger.info("\nStep 2: Generating BERT embeddings...")
    logger.info("  Loading SentenceTransformer model: 'all-MiniLM-L6-v2'...")

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')

    logger.info("  Encoding task descriptions (384-D per occupation)...")
    embeddings = model.encode(task_text.tolist(), show_progress_bar=True)
    logger.info(f"  Embedding matrix shape: {embeddings.shape}")

    # ------------------------------------------------------------------
    # Step 3: Run PCA with max components
    # ------------------------------------------------------------------
    n_max = min(50, embeddings.shape[0], embeddings.shape[1])
    logger.info(f"\nStep 3: Fitting PCA with n_components={n_max}...")

    pca = PCA(n_components=n_max, random_state=42)
    pca.fit(embeddings)

    cumulative_var = np.cumsum(pca.explained_variance_ratio_) * 100
    individual_var = pca.explained_variance_ratio_ * 100

    # ------------------------------------------------------------------
    # Step 4: Print variance at key thresholds
    # ------------------------------------------------------------------
    logger.info("\n" + "=" * 50)
    logger.info("CUMULATIVE VARIANCE EXPLAINED")
    logger.info("=" * 50)
    for n in [5, 10, 15, 20, 25, 30, 40, 50]:
        if n <= len(cumulative_var):
            logger.info(f"  {n:3d} components: {cumulative_var[n-1]:6.2f}%")

    # Find how many components for 95%
    threshold_95 = np.argmax(cumulative_var >= 95) + 1
    if cumulative_var[-1] < 95:
        threshold_95 = n_max
        logger.info(f"\n  95% variance NOT reached in {n_max} components")
        logger.info(f"  Max variance at {n_max} components: {cumulative_var[-1]:.2f}%")
    else:
        logger.info(f"\n  Components needed for 95% variance: {threshold_95}")

    var_at_20 = cumulative_var[19] if len(cumulative_var) >= 20 else cumulative_var[-1]
    logger.info(f"  Variance at 20 components: {var_at_20:.2f}%")

    # ------------------------------------------------------------------
    # Step 5: Generate publication-quality figure
    # ------------------------------------------------------------------
    logger.info("\nStep 5: Generating scree plot...")

    fig, ax = plt.subplots(figsize=(10, 6))

    components = np.arange(1, n_max + 1)

    # Individual variance bars
    ax.bar(components, individual_var, alpha=0.35, color='steelblue',
           label='Per-Component Variance', zorder=2)

    # Cumulative variance line
    ax.plot(components, cumulative_var, 'b-o', markersize=4, linewidth=2,
            label='Cumulative Explained Variance', zorder=3)

    # Vertical dashed line at component 20
    ax.axvline(x=20, color='red', linestyle='--', linewidth=1.5, alpha=0.8,
               label=f'Selected cutoff: 20 components ({var_at_20:.1f}%)')

    # Horizontal dashed line at 95%
    ax.axhline(y=95, color='gray', linestyle=':', linewidth=1, alpha=0.7,
               label='95% Variance Threshold')

    # Annotation at component 20
    ax.annotate(f'{var_at_20:.1f}%',
                xy=(20, var_at_20),
                xytext=(30, var_at_20 - 10),
                fontsize=11, fontweight='bold', color='red',
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5))

    # Also annotate the "elbow" region
    if len(cumulative_var) >= 10:
        var_at_10 = cumulative_var[9]
        ax.annotate(f'{var_at_10:.1f}%',
                    xy=(10, var_at_10),
                    xytext=(16, var_at_10 - 15),
                    fontsize=9, color='gray',
                    arrowprops=dict(arrowstyle='->', color='gray', lw=1))

    ax.set_xlabel('Number of PCA Components', fontsize=12)
    ax.set_ylabel('Explained Variance (%)', fontsize=12)
    ax.set_title('Cumulative Variance Explained by PCA Components\n'
                 '(BERT all-MiniLM-L6-v2 Embeddings, 384-D → PCA)',
                 fontsize=13, fontweight='bold')
    ax.set_xlim(0, n_max + 1)
    ax.set_ylim(0, 105)
    ax.legend(loc='lower right', fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_path = FIGURES_DIR / 'pca_variance_explained.png'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    logger.info(f"  Saved: {fig_path}")

    logger.info("\n" + "=" * 70)
    logger.info("PCA SCREE PLOT COMPLETE")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
