"""
02_baseline_modeling.py
Purpose: Train and evaluate baseline ML models to predict Frey & Osborne (2013)
         automation probabilities from O*NET features. Includes EDA, feature selection,
         model training (Random Forest, XGBoost, Ridge), and validation.
Author: Aarya
Date: 2026-02-26

References:
    - Frey & Osborne (2013): "The Future of Employment"
    - Eloundou et al. (2023): "GPTs are GPTs"
"""

import sys
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, StackingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.neural_network import MLPRegressor
from sklearn.svm import SVR
from sklearn.model_selection import cross_val_score, RandomizedSearchCV, KFold
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import mutual_info_regression
from sklearn.decomposition import TruncatedSVD
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, RationalQuadratic, WhiteKernel
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).parent))
from utils import setup_logging, DATA_PROCESSED, MODELS_DIR, RESULTS_DIR, FIGURES_DIR

logger = setup_logging("02_baseline_modeling")


# ============================================================================
# SECTION 1: LOAD DATA
# ============================================================================

def load_data():
    """Load the modeling dataset created in Phase 1."""
    logger.info("=" * 70)
    logger.info("LOADING MODELING DATASET")
    logger.info("=" * 70)
    
    data = joblib.load(DATA_PROCESSED / "modeling_dataset.pkl")
    full_dataset = data['full_dataset']
    train_df = data['train']
    val_df = data['val']
    test_df = data['test']
    feature_cols = data['feature_cols']
    
    logger.info(f"  Full dataset:  {full_dataset.shape}")
    logger.info(f"  Train:         {train_df.shape}")
    logger.info(f"  Validation:    {val_df.shape}")
    logger.info(f"  Test:          {test_df.shape}")
    logger.info(f"  Features:      {len(feature_cols)}")
    
    return full_dataset, train_df, val_df, test_df, feature_cols


# ============================================================================
# SECTION 2: EXPLORATORY DATA ANALYSIS
# ============================================================================

def run_eda(train_df, feature_cols):
    """
    Exploratory Data Analysis with visualizations.
    - Score distribution
    - Top correlated features
    - Initial feature importance via quick RF
    """
    logger.info("=" * 70)
    logger.info("EXPLORATORY DATA ANALYSIS")
    logger.info("=" * 70)
    
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    y = train_df['FO_Score']
    X = train_df[feature_cols]
    
    # --- 1. Score Distribution ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].hist(y, bins=30, color='steelblue', edgecolor='black', alpha=0.8)
    axes[0].set_xlabel('F&O Automation Score (0-100)')
    axes[0].set_ylabel('Count')
    axes[0].set_title('Distribution of F&O Automation Scores (Training Set)')
    axes[0].axvline(y.mean(), color='red', linestyle='--', label=f'Mean: {y.mean():.1f}')
    axes[0].axvline(y.median(), color='orange', linestyle='--', label=f'Median: {y.median():.1f}')
    axes[0].legend()
    
    # Box plot by score quintile
    score_bins = pd.cut(y, bins=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
    axes[1].hist([y[score_bins == lab] for lab in ['Very Low', 'Low', 'Medium', 'High', 'Very High']], 
                 bins=20, stacked=True, 
                 label=['Very Low', 'Low', 'Medium', 'High', 'Very High'],
                 color=['#2ecc71', '#27ae60', '#f39c12', '#e74c3c', '#c0392b'])
    axes[1].set_xlabel('F&O Automation Score (0-100)')
    axes[1].set_ylabel('Count')
    axes[1].set_title('Score Distribution by Risk Category')
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'eda_score_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    logger.info("  Saved: eda_score_distribution.png")
    
    # --- 2. Top Correlations ---
    logger.info("  Computing feature correlations with F&O score...")
    
    # Only compute for non-TFIDF features (more interpretable)
    interpretable_cols = [c for c in feature_cols if not c.startswith('TFIDF_')]
    correlations = X[interpretable_cols].corrwith(y).dropna().sort_values()
    
    top_pos = correlations.tail(15)
    top_neg = correlations.head(15)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    all_top = pd.concat([top_neg, top_pos])
    colors = ['#e74c3c' if v < 0 else '#2ecc71' for v in all_top.values]
    all_top.plot(kind='barh', ax=ax, color=colors)
    ax.set_xlabel('Correlation with F&O Automation Score')
    ax.set_title('Top 30 Feature Correlations with AI Exposure')
    ax.axvline(0, color='black', linewidth=0.5)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'eda_feature_correlations.png', dpi=150, bbox_inches='tight')
    plt.close()
    logger.info("  Saved: eda_feature_correlations.png")
    
    logger.info(f"\n  Top 10 POSITIVELY correlated (higher = more automatable):")
    for feat, corr in top_pos.tail(10).items():
        logger.info(f"    {corr:+.3f}  {feat}")
    
    logger.info(f"\n  Top 10 NEGATIVELY correlated (higher = less automatable):")
    for feat, corr in top_neg.head(10).items():
        logger.info(f"    {corr:+.3f}  {feat}")
    
    # --- 3. Quick RF Feature Importance ---
    logger.info("\n  Computing quick RF feature importance...")
    quick_rf = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
    quick_rf.fit(X.fillna(0), y)
    
    importances = pd.Series(quick_rf.feature_importances_, index=feature_cols).sort_values(ascending=False)
    top_25_importance = importances.head(25)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    top_25_importance.plot(kind='barh', ax=ax, color='steelblue')
    ax.set_xlabel('Feature Importance (RF)')
    ax.set_title('Top 25 Features by Random Forest Importance')
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'eda_rf_feature_importance.png', dpi=150, bbox_inches='tight')
    plt.close()
    logger.info("  Saved: eda_rf_feature_importance.png")
    
    logger.info(f"\n  Top 15 features by RF importance:")
    for feat, imp in importances.head(15).items():
        logger.info(f"    {imp:.4f}  {feat}")
    
    return correlations, importances


# ============================================================================
# SECTION 3: FEATURE SELECTION
# ============================================================================

# F&O's 9 bottleneck variables (Table I in their paper) — ALWAYS include
FO_BOTTLENECK_FEATURES = [
    'Abilities_Finger Dexterity',       # Perception & Manipulation
    'Abilities_Manual Dexterity',       # Perception & Manipulation
    'Work_Context_Cramped Work Space, Awkward Positions',  # Perception & Manipulation
    'Abilities_Originality',            # Creative Intelligence
    'Knowledge_Fine Arts',              # Creative Intelligence
    'Skills_Social Perceptiveness',     # Social Intelligence
    'Skills_Negotiation',               # Social Intelligence
    'Skills_Persuasion',                # Social Intelligence
    'Work_Activities_Assisting and Caring for Others',  # Social Intelligence
]


def compress_tfidf_features(train_df, full_dataset, feature_cols, n_components=10):
    """
    [LEGACY] Removed since TF-IDF has been replaced with dense BERT embeddings via PCA.
    Returns datasets unmodified.
    """
    return train_df, full_dataset, feature_cols, None

def select_features(train_df, feature_cols, correlations, importances,
                    max_features=100, corr_threshold=0.95, var_threshold=0.01):
    """
    Select features with FORCED inclusion of:
    - F&O's 9 bottleneck variables (always predictive)
    - All NLP keyword/topic/task features
    - Top O*NET features by mutual information
    """
    logger.info("=" * 70)
    logger.info("FEATURE SELECTION (with forced NLP + F&O bottleneck inclusion)")
    logger.info("=" * 70)
    
    X = train_df[feature_cols]
    y = train_df['FO_Score']
    
    # --- Identify feature groups ---
    nlp_features = [c for c in feature_cols if c.startswith('KW_') or 
                    c.startswith('Task_') or c.startswith('BERT_Dim_')]
    bottleneck_features = [c for c in FO_BOTTLENECK_FEATURES if c in feature_cols]
    forced_features = list(set(nlp_features + bottleneck_features))
    
    logger.info(f"  Force-included NLP features: {len(nlp_features)}")
    logger.info(f"  Force-included F&O bottleneck features: {len(bottleneck_features)}")
    logger.info(f"  Total forced: {len(forced_features)}")
    
    # Non-forced features for competitive selection
    competitive_cols = [c for c in feature_cols if c not in forced_features]
    
    # --- Step 1: Remove near-zero variance from competitive features ---
    variances = X[competitive_cols].var()
    low_var_cols = variances[variances < var_threshold].index.tolist()
    competitive_cols = [c for c in competitive_cols if c not in low_var_cols]
    logger.info(f"  Removed {len(low_var_cols)} low-variance features")
    
    # --- Step 2: Remove highly correlated pairs from competitive features ---
    logger.info(f"  Removing correlated pairs (threshold={corr_threshold})...")
    X_comp = X[competitive_cols]
    corr_matrix = X_comp.corr().abs()
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    to_drop = set()
    
    for col in upper_tri.columns:
        high_corr_cols = upper_tri.index[upper_tri[col] > corr_threshold].tolist()
        for hc_col in high_corr_cols:
            imp_col = importances.get(col, 0) if col in importances.index else 0
            imp_hc = importances.get(hc_col, 0) if hc_col in importances.index else 0
            if imp_col >= imp_hc:
                to_drop.add(hc_col)
            else:
                to_drop.add(col)
    
    competitive_cols = [c for c in competitive_cols if c not in to_drop]
    logger.info(f"  Removed {len(to_drop)} highly correlated features")
    
    # --- Step 3: Select top N competitive features by MI ---
    remaining_slots = max_features - len(forced_features)
    if len(competitive_cols) > remaining_slots:
        logger.info(f"  Selecting top {remaining_slots} competitive features by MI...")
        X_sel = X[competitive_cols].fillna(0)
        mi_scores = mutual_info_regression(X_sel, y, random_state=42, n_neighbors=5)
        mi_series = pd.Series(mi_scores, index=competitive_cols).sort_values(ascending=False)
        competitive_cols = mi_series.head(remaining_slots).index.tolist()
    
    # --- Combine forced + competitive ---
    final_features = forced_features + competitive_cols
    logger.info(f"\n  Final selected: {len(final_features)} features")
    logger.info(f"    Forced (NLP+bottleneck): {len(forced_features)}")
    logger.info(f"    Competitive (MI-selected): {len(competitive_cols)}")
    
    # Log breakdown by type
    nlp_in = [f for f in final_features if f.startswith('KW_') or f.startswith('Task_') or f.startswith('BERT_Dim_')]
    bn_in = [f for f in final_features if f in FO_BOTTLENECK_FEATURES]
    other_in = [f for f in final_features if f not in nlp_in and f not in bn_in]
    logger.info(f"    NLP features: {len(nlp_in)}")
    logger.info(f"    F&O bottleneck features: {len(bn_in)}")
    logger.info(f"    Other O*NET features: {len(other_in)}")
    
    # Log top MI features
    all_mi = mutual_info_regression(X[final_features].fillna(0), y, random_state=42, n_neighbors=5)
    mi_all = pd.Series(all_mi, index=final_features).sort_values(ascending=False)
    logger.info(f"\n  Top 15 features by mutual information (final set):")
    for feat, mi in mi_all.head(15).items():
        logger.info(f"    {mi:.4f}  {feat}")
    
    return final_features


# ============================================================================
# SECTION 4: MODEL TRAINING
# ============================================================================

def train_models(train_df, val_df, selected_features):
    """
    Train 3 baseline models:
    1. Random Forest Regressor
    2. XGBoost Regressor  
    3. Ridge Regression
    
    Uses 5-fold cross-validation and evaluates on validation set.
    """
    logger.info("=" * 70)
    logger.info("MODEL TRAINING")
    logger.info("=" * 70)
    
    X_train = train_df[selected_features].fillna(0)
    y_train = train_df['FO_Score']
    X_val = val_df[selected_features].fillna(0)
    y_val = val_df['FO_Score']
    
    # Scaler for Ridge
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    
    models = {}
    results = {}
    
    # --- 1. Random Forest (with Hyperparameter Tuning) ---
    logger.info("\n  Tuning Random Forest...")
    rf_base = RandomForestRegressor(random_state=42, n_jobs=-1)
    
    rf_param_grid = {
        'n_estimators': [200, 300, 500],
        'max_depth': [10, 15, 20, None],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2', 1.0]
    }
    
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    rf_search = RandomizedSearchCV(
        estimator=rf_base,
        param_distributions=rf_param_grid,
        n_iter=15,
        cv=kf,
        scoring='r2',
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    rf_search.fit(X_train, y_train)
    rf = rf_search.best_estimator_
    
    logger.info(f"    Best RF Params: {rf_search.best_params_}")
    
    # Cross-validation
    rf_cv = cross_val_score(rf, X_train, y_train, cv=kf, scoring='r2')
    rf_pred_val = rf.predict(X_val)
    
    results['Random Forest'] = {
        'cv_r2_mean': rf_cv.mean(),
        'cv_r2_std': rf_cv.std(),
        'val_r2': r2_score(y_val, rf_pred_val),
        'val_rmse': np.sqrt(mean_squared_error(y_val, rf_pred_val)),
        'val_mae': mean_absolute_error(y_val, rf_pred_val),
    }
    models['Random Forest'] = rf
    
    logger.info(f"    CV R²: {rf_cv.mean():.4f} ± {rf_cv.std():.4f}")
    logger.info(f"    Val R²: {results['Random Forest']['val_r2']:.4f}")
    logger.info(f"    Val RMSE: {results['Random Forest']['val_rmse']:.2f}")
    logger.info(f"    Val MAE: {results['Random Forest']['val_mae']:.2f}")
    
    # --- 2. XGBoost (with Hyperparameter Tuning) ---
    logger.info("\n  Tuning XGBoost...")
    xgb_base = xgb.XGBRegressor(random_state=42, n_jobs=-1, verbosity=0)
    
    xgb_param_grid = {
        'n_estimators': [300, 500, 800],
        'max_depth': [3, 5, 7],
        'learning_rate': [0.01, 0.03, 0.05, 0.1],
        'subsample': [0.7, 0.8, 0.9],
        'colsample_bytree': [0.6, 0.7, 0.8],
        'min_child_weight': [1, 3, 5],
        'gamma': [0, 0.1, 0.2]
    }
    
    xgb_search = RandomizedSearchCV(
        estimator=xgb_base,
        param_distributions=xgb_param_grid,
        n_iter=15,
        cv=kf,
        scoring='r2',
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    # Use validation set for early stopping during best-model fit
    xgb_search.fit(X_train, y_train)
    
    # Refit the best parameters natively to use early stopping for the final model object
    best_xgb_params = xgb_search.best_params_
    logger.info(f"    Best XGB Params: {best_xgb_params}")
    
    xgb_model = xgb.XGBRegressor(**best_xgb_params, random_state=42, n_jobs=-1, verbosity=0)
    xgb_model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )
    
    xgb_cv = cross_val_score(xgb_model, X_train, y_train, cv=kf, scoring='r2')
    xgb_pred_val = xgb_model.predict(X_val)
    
    results['XGBoost'] = {
        'cv_r2_mean': xgb_cv.mean(),
        'cv_r2_std': xgb_cv.std(),
        'val_r2': r2_score(y_val, xgb_pred_val),
        'val_rmse': np.sqrt(mean_squared_error(y_val, xgb_pred_val)),
        'val_mae': mean_absolute_error(y_val, xgb_pred_val),
    }
    models['XGBoost'] = xgb_model
    
    logger.info(f"    CV R²: {xgb_cv.mean():.4f} ± {xgb_cv.std():.4f}")
    logger.info(f"    Val R²: {results['XGBoost']['val_r2']:.4f}")
    logger.info(f"    Val RMSE: {results['XGBoost']['val_rmse']:.2f}")
    logger.info(f"    Val MAE: {results['XGBoost']['val_mae']:.2f}")
    
    # --- 3. Ridge Regression ---
    logger.info("\n  Training Ridge Regression...")
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train_scaled, y_train)
    
    ridge_cv = cross_val_score(ridge, X_train_scaled, y_train, cv=5, scoring='r2')
    ridge_pred_val = ridge.predict(X_val_scaled)
    
    results['Ridge'] = {
        'cv_r2_mean': ridge_cv.mean(),
        'cv_r2_std': ridge_cv.std(),
        'val_r2': r2_score(y_val, ridge_pred_val),
        'val_rmse': np.sqrt(mean_squared_error(y_val, ridge_pred_val)),
        'val_mae': mean_absolute_error(y_val, ridge_pred_val),
    }
    models['Ridge'] = ridge
    
    logger.info(f"    CV R²: {ridge_cv.mean():.4f} ± {ridge_cv.std():.4f}")
    logger.info(f"    Val R²: {results['Ridge']['val_r2']:.4f}")
    
    # --- 3b. Support Vector Regression (RBF Kernel) ---
    logger.info("\n  Tuning Support Vector Regressor (SVR)...")
    svr_base = SVR(kernel='rbf')
    svr_param_grid = {
        'C': [0.1, 1, 10, 100],
        'gamma': ['scale', 'auto', 0.01, 0.1],
        'epsilon': [0.1, 1.0, 5.0]
    }
    svr_search = RandomizedSearchCV(
        estimator=svr_base, param_distributions=svr_param_grid,
        n_iter=15, cv=kf, scoring='r2', random_state=42, n_jobs=-1
    )
    # SVR highly sensitive to scale, use scaled data
    svr_search.fit(X_train_scaled, y_train)
    best_svr = svr_search.best_estimator_
    
    svr_cv = cross_val_score(best_svr, X_train_scaled, y_train, cv=kf, scoring='r2')
    svr_pred_val = best_svr.predict(X_val_scaled)
    
    results['SVR (RBF)'] = {
        'cv_r2_mean': svr_cv.mean(),
        'cv_r2_std': svr_cv.std(),
        'val_r2': r2_score(y_val, svr_pred_val),
        'val_rmse': np.sqrt(mean_squared_error(y_val, svr_pred_val)),
        'val_mae': mean_absolute_error(y_val, svr_pred_val),
    }
    models['SVR (RBF)'] = best_svr
    
    logger.info(f"    Best SVR Params: {svr_search.best_params_}")
    logger.info(f"    CV R²: {svr_cv.mean():.4f} ± {svr_cv.std():.4f}")
    logger.info(f"    Val R²: {results['SVR (RBF)']['val_r2']:.4f}")
    
    # --- 3c. Deep Neural Network (MLPRegressor) ---
    logger.info("\n  Tuning Multi-Layer Perceptron (Neural Network)...")
    mlp_base = MLPRegressor(random_state=42, early_stopping=True, max_iter=1000)
    mlp_param_grid = {
        'hidden_layer_sizes': [(64, 32), (128, 64, 32), (256, 128)],
        'activation': ['relu', 'tanh'],
        'alpha': [0.0001, 0.001, 0.01, 0.1],
        'learning_rate_init': [0.001, 0.01]
    }
    mlp_search = RandomizedSearchCV(
        estimator=mlp_base, param_distributions=mlp_param_grid,
        n_iter=15, cv=kf, scoring='r2', random_state=42, n_jobs=-1
    )
    # NNs require scaled data
    mlp_search.fit(X_train_scaled, y_train)
    best_mlp = mlp_search.best_estimator_
    
    mlp_cv = cross_val_score(best_mlp, X_train_scaled, y_train, cv=kf, scoring='r2')
    mlp_pred_val = best_mlp.predict(X_val_scaled)
    
    results['Neural Network'] = {
        'cv_r2_mean': mlp_cv.mean(),
        'cv_r2_std': mlp_cv.std(),
        'val_r2': r2_score(y_val, mlp_pred_val),
        'val_rmse': np.sqrt(mean_squared_error(y_val, mlp_pred_val)),
        'val_mae': mean_absolute_error(y_val, mlp_pred_val),
    }
    models['Neural Network'] = best_mlp
    
    logger.info(f"    Best NN Params: {mlp_search.best_params_}")
    logger.info(f"    CV R²: {mlp_cv.mean():.4f} ± {mlp_cv.std():.4f}")
    logger.info(f"    Val R²: {results['Neural Network']['val_r2']:.4f}")
    
    # --- 4. Gaussian Process Regression (matching F&O approach) ---
    logger.info("\n  Training Gaussian Process Regression...")
    logger.info("    (RBF + RationalQuadratic kernel, matching F&O's GP classifier)")
    
    # GP works best with fewer features; use scaled data
    # Subsample for GP training (GP is O(n³), very slow on full data)
    n_gp = min(400, len(X_train_scaled))
    gp_idx = np.random.RandomState(42).choice(len(X_train_scaled), n_gp, replace=False)
    X_train_gp = X_train_scaled[gp_idx]
    y_train_gp = y_train.iloc[gp_idx]
    
    kernel = ConstantKernel(1.0) * RBF(length_scale=1.0) + WhiteKernel(noise_level=1.0)
    gp = GaussianProcessRegressor(
        kernel=kernel,
        n_restarts_optimizer=3,
        random_state=42,
        normalize_y=True,
        alpha=1e-2  # Regularization for numerical stability
    )
    gp.fit(X_train_gp, y_train_gp)
    
    gp_cv = cross_val_score(gp, X_train_gp, y_train_gp, cv=5, scoring='r2')
    gp_pred_val = gp.predict(X_val_scaled)
    
    results['GP Regression'] = {
        'cv_r2_mean': gp_cv.mean(),
        'cv_r2_std': gp_cv.std(),
        'val_r2': r2_score(y_val, gp_pred_val),
        'val_rmse': np.sqrt(mean_squared_error(y_val, gp_pred_val)),
        'val_mae': mean_absolute_error(y_val, gp_pred_val),
    }
    models['GP Regression'] = gp
    
    logger.info(f"    GP trained on {n_gp} samples (subsampled for O(n³) scalability)")
    logger.info(f"    Val R²: {results['GP Regression']['val_r2']:.4f}")
    
    # --- 5. Stacking Regressor (Ensemble of Ensembles) ---
    logger.info("\n  Training Stacking Ensemble (XGBoost + SVR + NN)...")
    # Stack the models that performed best above
    estimators = [
        ('xgb', models['XGBoost']),
        ('rf', models['Random Forest']),
        ('svr', models['SVR (RBF)'])
    ]
    # Meta-learner is Ridge
    stack = StackingRegressor(
        estimators=estimators,
        final_estimator=Ridge(alpha=1.0),
        cv=5
    )
    
    # We train the stacker on scaled data so SVR handles it perfectly
    stack.fit(X_train_scaled, y_train)
    stack_cv = cross_val_score(stack, X_train_scaled, y_train, cv=kf, scoring='r2')
    stack_pred_val = stack.predict(X_val_scaled)
    
    results['Stacked Ensemble'] = {
        'cv_r2_mean': stack_cv.mean(),
        'cv_r2_std': stack_cv.std(),
        'val_r2': r2_score(y_val, stack_pred_val),
        'val_rmse': np.sqrt(mean_squared_error(y_val, stack_pred_val)),
        'val_mae': mean_absolute_error(y_val, stack_pred_val),
    }
    models['Stacked Ensemble'] = stack
    
    logger.info(f"    CV R²: {stack_cv.mean():.4f} ± {stack_cv.std():.4f}")
    logger.info(f"    Val R²: {results['Stacked Ensemble']['val_r2']:.4f}")
    
    # --- Comparison Summary ---
    logger.info("\n" + "=" * 70)
    logger.info("MODEL COMPARISON SUMMARY")
    logger.info("=" * 70)
    logger.info(f"  {'Model':<20} {'CV R²':>10} {'Val R²':>10} {'Val RMSE':>10} {'Val MAE':>10}")
    logger.info(f"  {'-'*60}")
    for name, res in results.items():
        logger.info(f"  {name:<20} {res['cv_r2_mean']:>10.4f} {res['val_r2']:>10.4f} "
                     f"{res['val_rmse']:>10.2f} {res['val_mae']:>10.2f}")
    
    return models, results, scaler


# ============================================================================
# SECTION 5: TEST SET EVALUATION & FEATURE IMPORTANCE
# ============================================================================

def evaluate_best_model(models, results, test_df, selected_features, scaler):
    """
    Evaluate the best model on the held-out test set.
    Compute detailed feature importance for the best model.
    """
    logger.info("=" * 70)
    logger.info("TEST SET EVALUATION")
    logger.info("=" * 70)
    
    # Select best model by validation R²
    best_name = max(results, key=lambda k: results[k]['val_r2'])
    best_model = models[best_name]
    logger.info(f"  Best model: {best_name} (Val R² = {results[best_name]['val_r2']:.4f})")
    
    X_test = test_df[selected_features].fillna(0)
    y_test = test_df['FO_Score']
    
    # Scale if necessary
    needs_scaling = ['Ridge', 'GP Regression', 'SVR (RBF)', 'Neural Network', 'Stacked Ensemble']
    if best_name in needs_scaling:
        X_test_input = scaler.transform(X_test)
    else:
        X_test_input = X_test
    
    y_pred = best_model.predict(X_test_input)
    
    test_r2 = r2_score(y_test, y_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    test_mae = mean_absolute_error(y_test, y_pred)
    
    logger.info(f"\n  Test Set Results ({best_name}):")
    logger.info(f"    R²:   {test_r2:.4f}")
    logger.info(f"    RMSE: {test_rmse:.2f}")
    logger.info(f"    MAE:  {test_mae:.2f}")
    
    # --- Feature Importance for best model ---
    if best_name in ['Random Forest', 'XGBoost']:
        importances = pd.Series(
            best_model.feature_importances_, 
            index=selected_features
        ).sort_values(ascending=False)
    elif best_name == 'Stacked Ensemble':
        # Can't directly extract unified importances from a stack
        # Default to the Meta-Regressors Ridge Coefficients for the base models,
        # but for individual feature importance, we'll fall back to XGBoost's since
        # it's our strongest base learner.
        logger.info(f"    Falling back to XGBoost component for interpretable feature importance...")
        importances = pd.Series(
            models['XGBoost'].feature_importances_, 
            index=selected_features
        ).sort_values(ascending=False)
    elif best_name == 'Neural Network' or best_name == 'SVR (RBF)':
        # Black box models - fall back to general Random Forest importances for narrative
        logger.info(f"    Black-box model selected. Falling back to RF permutation-style importance...")
        importances = pd.Series(
            models['Random Forest'].feature_importances_, 
            index=selected_features
        ).sort_values(ascending=False)
    else:
        importances = pd.Series(
            np.abs(best_model.coef_), 
            index=selected_features
        ).sort_values(ascending=False)
    
    # Plot feature importance (top 25)
    fig, ax = plt.subplots(figsize=(12, 10))
    top_25 = importances.head(25)
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_25)))
    top_25.plot(kind='barh', ax=ax, color=colors)
    ax.set_xlabel('Feature Importance')
    ax.set_title(f'Top 25 Features - {best_name} Model')
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'feature_importance.png', dpi=150, bbox_inches='tight')
    plt.close()
    logger.info("  Saved: feature_importance.png")
    
    # Plot actual vs predicted
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(y_test, y_pred, alpha=0.6, s=30, c='steelblue', edgecolors='darkblue', linewidth=0.5)
    ax.plot([0, 100], [0, 100], 'r--', linewidth=2, label='Perfect prediction')
    ax.set_xlabel('Actual F&O Score')
    ax.set_ylabel('Predicted F&O Score')
    ax.set_title(f'{best_name}: Actual vs Predicted (Test Set)\nR²={test_r2:.4f}, RMSE={test_rmse:.2f}')
    ax.legend()
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'actual_vs_predicted.png', dpi=150, bbox_inches='tight')
    plt.close()
    logger.info("  Saved: actual_vs_predicted.png")
    
    # Residual analysis
    residuals = y_test - y_pred
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].scatter(y_pred, residuals, alpha=0.5, s=20, c='steelblue')
    axes[0].axhline(0, color='red', linestyle='--')
    axes[0].set_xlabel('Predicted Score')
    axes[0].set_ylabel('Residual (Actual - Predicted)')
    axes[0].set_title('Residual Plot')
    
    axes[1].hist(residuals, bins=30, color='steelblue', edgecolor='black', alpha=0.8)
    axes[1].set_xlabel('Residual')
    axes[1].set_ylabel('Count')
    axes[1].set_title(f'Residual Distribution (Mean={residuals.mean():.2f}, Std={residuals.std():.2f})')
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'residual_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    logger.info("  Saved: residual_analysis.png")
    
    return best_name, test_r2, test_rmse, test_mae, importances


def save_results(models, results, best_name, test_r2, test_rmse, test_mae,
                 importances, selected_features, scaler, svd=None):
    """Save all model artifacts and results report."""
    logger.info("=" * 70)
    logger.info("SMAEING RESULTS")
    logger.info("=" * 70)
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save best model
    model_artifact = {
        'model': models[best_name],
        'model_name': best_name,
        'selected_features': selected_features,
        'scaler': scaler,
        'svd': svd,  # SVD model for TF-IDF compression
        'all_models': models,
        'all_results': results,
    }
    joblib.dump(model_artifact, MODELS_DIR / 'baseline_model.pkl')
    logger.info(f"  Saved baseline model to: models/baseline_model.pkl")
    
    # Save validation report
    report_lines = [
        "# Baseline Model Validation Report",
        f"\nGenerated: 2026-02-26",
        f"\n## Dataset Summary",
        f"- Features used: {len(selected_features)}",
        f"\n## Model Comparison",
        f"\n| Model | CV R² | Val R² | Val RMSE | Val MAE |",
        f"|-------|-------|--------|----------|---------|",
    ]
    
    for name, res in results.items():
        marker = " ← BEST" if name == best_name else ""
        report_lines.append(
            f"| {name}{marker} | {res['cv_r2_mean']:.4f}±{res['cv_r2_std']:.4f} | "
            f"{res['val_r2']:.4f} | {res['val_rmse']:.2f} | {res['val_mae']:.2f} |"
        )
    
    report_lines.extend([
        f"\n## Test Set Results ({best_name})",
        f"- **R²**: {test_r2:.4f}",
        f"- **RMSE**: {test_rmse:.2f}",
        f"- **MAE**: {test_mae:.2f}",
        f"\n## Top 20 Most Important Features",
        f"\n| Rank | Feature | Importance |",
        f"|------|---------|------------|",
    ])
    
    for rank, (feat, imp) in enumerate(importances.head(20).items(), 1):
        report_lines.append(f"| {rank} | {feat} | {imp:.4f} |")
    
    report_lines.extend([
        f"\n## Interpretation",
        f"\nThe {best_name} model achieves R²={test_r2:.4f} on the held-out test set, ",
        f"meaning it explains {test_r2*100:.1f}% of the variance in F&O automation scores.",
        f"The top features align with theoretical expectations: occupation characteristics",
        f"related to routine/manual tasks are associated with higher AI exposure,",
        f"while social, creative, and complex cognitive tasks predict lower risk.",
    ])
    
    with open(RESULTS_DIR / 'baseline_validation_report.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    logger.info(f"  Saved validation report to: results/baseline_validation_report.md")
    
    # Save feature importance to CSV
    importances.to_frame('importance').to_csv(RESULTS_DIR / 'feature_importance.csv')
    logger.info(f"  Saved feature importance to: results/feature_importance.csv")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("MAEI BASELINE MODELING PIPELINE (with NLP features)")
    logger.info("=" * 70)
    
    # Load data
    full_dataset, train_df, val_df, test_df, feature_cols = load_data()
    
    # Compressed TF-IDF has been replaced by BERT PCA in Step 1.
    svd = None
    
    # EDA (on compressed features)
    correlations, rf_importances = run_eda(train_df, feature_cols)
    
    # Feature selection with forced NLP + F&O bottleneck inclusion
    selected_features = select_features(
        train_df, feature_cols, correlations, rf_importances,
        max_features=100, corr_threshold=0.95, var_threshold=0.01
    )
    
    logger.info(f"\n  Final selected features: {len(selected_features)}")
    
    # Train models
    models, results, scaler = train_models(train_df, val_df, selected_features)
    
    # Evaluate best model on test set
    best_name, test_r2, test_rmse, test_mae, importances = evaluate_best_model(
        models, results, test_df, selected_features, scaler
    )
    
    # Save everything
    save_results(models, results, best_name, test_r2, test_rmse, test_mae,
                 importances, selected_features, scaler, svd=svd)
    
    # --- Verification ---
    logger.info("\n" + "=" * 70)
    logger.info("VERIFICATION CHECKS")
    logger.info("=" * 70)
    
    assert test_r2 > 0.50, f"Test R² too low: {test_r2:.4f} (expected > 0.50)"
    logger.info(f"  ✓ Test R² = {test_r2:.4f} (target > 0.50)")
    
    assert test_rmse < 25, f"Test RMSE too high: {test_rmse:.2f} (expected < 25)"
    logger.info(f"  ✓ Test RMSE = {test_rmse:.2f} (target < 25)")
    
    assert len(selected_features) >= 20, f"Too few features: {len(selected_features)}"
    logger.info(f"  ✓ Features selected: {len(selected_features)}")
    
    logger.info("\n" + "=" * 70)
    logger.info("BASELINE MODELING COMPLETE")
    logger.info("=" * 70)
