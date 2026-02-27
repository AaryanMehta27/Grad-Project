"""
01_data_preparation.py
Purpose: Load Frey & Osborne (2013) data, fix corrupted SOC codes, map to O*NET codes,
         extract features from all O*NET files, and create the modeling dataset.
Author: Aarya
Date: 2026-02-26

References:
    - Frey & Osborne (2013): "The Future of Employment"
    - O*NET Database v30.1
"""

import sys
import re
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    setup_logging, BASE_PATH, ONET_PATH, FO_DATA_PATH,
    DATA_PROCESSED, ONET_FILES, load_onet_file, get_base_soc
)

logger = setup_logging("01_data_preparation")


# ============================================================================
# SECTION 1: FIX & LOAD FREY-OSBORNE DATA
# ============================================================================

# Mapping for Excel-corrupted SOC codes.
# Excel converts codes like "11-2011" to date "Nov-11".
# Month abbreviations map to the first part of the SOC code.
MONTH_TO_SOC_PREFIX = {
    'Jan': '1', 'Feb': '2', 'Mar': '3', 'Apr': '4',
    'May': '5', 'Jun': '6', 'Jul': '7', 'Aug': '8',
    'Sep': '9', 'Oct': '10', 'Nov': '11', 'Dec': '12'
}


def fix_soc_code(raw_code: str, occupation_title: str) -> str:
    """
    Fix Excel-corrupted SOC codes.
    
    Excel auto-formats codes like '11-2011' as dates like 'Nov-11'.
    Pattern: 'Month-DD' -> 'XX-DD??'
    
    The logic: If 'Nov-11', the 'Nov' = month 11 = SOC major group 11,
    and '11' = the minor part. But SOC codes are XX-XXXX format.
    
    Actually, the corruption pattern is:
    SOC '11-2011' -> Excel sees it as ambiguous, stores as 'Nov-11'
    But we can't perfectly reverse this without a lookup table.
    
    Better approach: Match corrupted entries to known SOC codes by title.
    
    Args:
        raw_code: The potentially corrupted SOC code string
        occupation_title: The occupation title for fallback matching
        
    Returns:
        Fixed SOC code string (6-digit format like '11-2011')
    """
    # If already a valid SOC code (XX-XXXX format), return as-is
    if re.match(r'^\d{2}-\d{4}$', str(raw_code)):
        return str(raw_code)
    
    # Return as-is if it's a partial match (like '11-1011' without leading zero issues)
    if re.match(r'^\d{1,2}-\d{4}$', str(raw_code)):
        parts = str(raw_code).split('-')
        return f"{int(parts[0]):02d}-{parts[1]}"
    
    # For Excel-corrupted codes, we'll need the lookup table
    return str(raw_code)


def build_soc_lookup_from_onet() -> Dict[str, str]:
    """
    Build a lookup table: occupation title (lowercase) -> 6-digit SOC code
    from O*NET occupation data.
    """
    logger.info("Building SOC code lookup from O*NET occupation data...")
    occ_df = load_onet_file("occupations")
    lookup = {}
    for _, row in occ_df.iterrows():
        soc_6 = get_base_soc(row['O*NET-SOC Code'])
        title_lower = row['Title'].strip().lower()
        lookup[title_lower] = soc_6
        # Also store without common suffixes for fuzzy matching
        for suffix in [', all other', ', except ', ' and ']:
            if suffix in title_lower:
                short_title = title_lower.split(suffix)[0].strip()
                if short_title not in lookup:
                    lookup[short_title] = soc_6
    
    logger.info(f"  Built lookup with {len(lookup)} title entries")
    return lookup


def load_and_fix_frey_osborne() -> pd.DataFrame:
    """
    Load Frey & Osborne data and fix corrupted SOC codes.
    
    Strategy:
    1. Load the raw CSV
    2. Build a mapping from O*NET occupations
    3. For valid SOC codes, keep them
    4. For corrupted codes, match by occupation title to O*NET data
    5. For remaining unmatched, attempt pattern-based repair
    
    Returns:
        DataFrame with columns: SOC_Code, Occupation, Probability, FO_Score
    """
    logger.info("=" * 70)
    logger.info("LOADING FREY & OSBORNE (2013) DATA")
    logger.info("=" * 70)
    
    # Load raw data
    fo_raw = pd.read_csv(FO_DATA_PATH, encoding='latin-1')
    logger.info(f"  Raw F&O data: {len(fo_raw)} rows")
    logger.info(f"  Columns: {list(fo_raw.columns)}")
    logger.info(f"  Probability range: {fo_raw['Probability'].min():.4f} to {fo_raw['Probability'].max():.4f}")
    
    # Build lookup from O*NET
    onet_lookup = build_soc_lookup_from_onet()
    
    # Also build a reverse lookup: SOC code -> list of O*NET titles
    occ_df = load_onet_file("occupations")
    soc_to_titles = {}
    for _, row in occ_df.iterrows():
        soc_6 = get_base_soc(row['O*NET-SOC Code'])
        soc_to_titles.setdefault(soc_6, []).append(row['Title'].strip().lower())
    
    # Process each row
    fixed_rows = []
    match_stats = {'valid': 0, 'title_match': 0, 'partial_match': 0, 'unmatched': 0}
    
    for _, row in fo_raw.iterrows():
        raw_soc = str(row['SOC']).strip()
        title = str(row['Occupation']).strip()
        prob = float(row['Probability'])
        title_lower = title.lower()
        
        # Check if SOC code is already valid
        if re.match(r'^\d{2}-\d{4}$', raw_soc):
            fixed_soc = raw_soc
            match_stats['valid'] += 1
        else:
            # Try exact title match first
            fixed_soc = None
            
            # Clean up F&O title for matching (they use semicolons instead of commas sometimes)
            title_clean = title_lower.replace(';', ',').strip()
            
            if title_clean in onet_lookup:
                fixed_soc = onet_lookup[title_clean]
                match_stats['title_match'] += 1
            else:
                # Try partial matching - find best matching title
                best_match = None
                best_score = 0
                
                for onet_title, soc_code in onet_lookup.items():
                    # Simple word overlap score
                    fo_words = set(title_clean.split())
                    onet_words = set(onet_title.split())
                    if len(fo_words) > 0 and len(onet_words) > 0:
                        overlap = len(fo_words & onet_words)
                        score = overlap / max(len(fo_words), len(onet_words))
                        if score > best_score and score > 0.5:
                            best_score = score
                            best_match = soc_code
                
                if best_match:
                    fixed_soc = best_match
                    match_stats['partial_match'] += 1
                else:
                    # Last resort: try to decode Excel date format
                    # Pattern: 'Mon-DD' where Mon is month abbreviation
                    month_match = re.match(r'^([A-Za-z]{3})-(\d{1,2})$', raw_soc)
                    if month_match:
                        month_str = month_match.group(1).capitalize()[:3]
                        day_str = month_match.group(2)
                        if month_str in MONTH_TO_SOC_PREFIX:
                            prefix = MONTH_TO_SOC_PREFIX[month_str]
                            # Try to find a valid SOC code that starts with this prefix
                            # and has a matching occupation title
                            candidates = [
                                soc for soc in soc_to_titles.keys()
                                if soc.startswith(f"{int(prefix):02d}-")
                            ]
                            # Match among candidates by title
                            for cand_soc in candidates:
                                for cand_title in soc_to_titles.get(cand_soc, []):
                                    fo_words = set(title_clean.split())
                                    c_words = set(cand_title.split())
                                    if len(fo_words & c_words) / max(len(fo_words), 1) > 0.4:
                                        fixed_soc = cand_soc
                                        break
                                if fixed_soc:
                                    break
                    
                    if fixed_soc:
                        match_stats['partial_match'] += 1
                    else:
                        fixed_soc = raw_soc  # Keep original, flag as unmatched
                        match_stats['unmatched'] += 1
        
        fixed_rows.append({
            'SOC_Code': fixed_soc,
            'Occupation': title,
            'Probability': prob,
            'FO_Score': round(prob * 100, 2),  # Convert to 0-100 scale
            'Original_SOC': raw_soc,
            'Match_Method': (
                'direct' if match_stats == 'valid' else
                'title_exact' if raw_soc != fixed_soc and re.match(r'^\d{2}-\d{4}$', str(fixed_soc)) else
                'original'
            )
        })
    
    fo_fixed = pd.DataFrame(fixed_rows)
    
    # Better match method assignment
    for i, row in fo_fixed.iterrows():
        if re.match(r'^\d{2}-\d{4}$', str(row['Original_SOC'])):
            fo_fixed.at[i, 'Match_Method'] = 'direct'
        elif re.match(r'^\d{2}-\d{4}$', str(row['SOC_Code'])) and row['SOC_Code'] != row['Original_SOC']:
            fo_fixed.at[i, 'Match_Method'] = 'fuzzy_matched'
        else:
            fo_fixed.at[i, 'Match_Method'] = 'unmatched'
    
    logger.info(f"\n  SOC Code Repair Results:")
    logger.info(f"    Already valid:    {match_stats['valid']}")
    logger.info(f"    Title matched:    {match_stats['title_match']}")
    logger.info(f"    Partial matched:  {match_stats['partial_match']}")
    logger.info(f"    Unmatched:        {match_stats['unmatched']}")
    
    # Log match method distribution
    method_counts = fo_fixed['Match_Method'].value_counts()
    logger.info(f"\n  Match Method Distribution:")
    for method, count in method_counts.items():
        logger.info(f"    {method}: {count}")
    
    # Show some examples of fixes
    corrupted = fo_fixed[fo_fixed['Original_SOC'] != fo_fixed['SOC_Code']].head(10)
    if len(corrupted) > 0:
        logger.info(f"\n  Example SOC code fixes:")
        for _, row in corrupted.iterrows():
            logger.info(f"    '{row['Original_SOC']}' -> '{row['SOC_Code']}' ({row['Occupation']})")
    
    return fo_fixed


# ============================================================================
# SECTION 2: LOAD & CONSOLIDATE O*NET FEATURES
# ============================================================================

def load_rated_features(file_key: str, scale_preference: str = 'IM') -> pd.DataFrame:
    """
    Load a rated O*NET file (Abilities, Skills, Knowledge, Work Activities, 
    Work Context, Work Styles) and pivot to create one row per occupation.
    
    Uses 'Importance' (IM) scale by default, falls back to 'Level' (LV).
    
    Args:
        file_key: Key for ONET_FILES dict
        scale_preference: Preferred scale - 'IM' for Importance, 'LV' for Level
        
    Returns:
        DataFrame with O*NET-SOC Code as index, features as columns.
        Column names are prefixed with the file_key.
    """
    logger.info(f"  Loading {file_key}...")
    df = load_onet_file(file_key)
    
    # Filter to preferred scale
    if 'Scale ID' in df.columns:
        scale_df = df[df['Scale ID'] == scale_preference].copy()
        
        # If too few records, try the other scale
        if len(scale_df) < len(df) * 0.3:
            other_scale = 'LV' if scale_preference == 'IM' else 'IM'
            scale_df = df[df['Scale ID'] == other_scale].copy()
            logger.info(f"    Using {other_scale} scale instead of {scale_preference}")
        else:
            logger.info(f"    Using {scale_preference} scale")
    else:
        scale_df = df.copy()
    
    # Filter out suppressed data
    if 'Recommend Suppress' in scale_df.columns:
        scale_df = scale_df[scale_df['Recommend Suppress'] != 'Y'].copy()
    
    # Pivot: rows = occupations, columns = element names
    if 'Element Name' in scale_df.columns and 'Data Value' in scale_df.columns:
        pivot = scale_df.pivot_table(
            index='O*NET-SOC Code',
            columns='Element Name',
            values='Data Value',
            aggfunc='mean'
        )
        
        # Prefix column names
        prefix = file_key.replace('_', ' ').title().replace(' ', '_')
        pivot.columns = [f"{prefix}_{col}" for col in pivot.columns]
        
        logger.info(f"    {pivot.shape[0]} occupations x {pivot.shape[1]} features")
        return pivot
    else:
        logger.warning(f"    Could not pivot {file_key} - missing expected columns")
        return pd.DataFrame()


def load_all_numeric_features() -> pd.DataFrame:
    """
    Load and consolidate all rated O*NET features into a single feature matrix.
    
    Returns:
        DataFrame with O*NET-SOC Code as index, all numeric features as columns.
    """
    logger.info("=" * 70)
    logger.info("LOADING O*NET NUMERIC FEATURES")
    logger.info("=" * 70)
    
    feature_dfs = []
    
    # Load each rated feature file
    rated_files = {
        'abilities': 'IM',         # 52 abilities
        'skills': 'IM',            # 35 skills  
        'knowledge': 'IM',         # 33 knowledge areas
        'work_activities': 'IM',   # 41 activities
        'work_styles': 'IM',       # 16 styles
    }
    
    for file_key, scale in rated_files.items():
        df = load_rated_features(file_key, scale)
        if not df.empty:
            feature_dfs.append(df)
    
    # Work Context needs special handling - uses multiple scale types
    logger.info("  Loading work_context (special handling for multiple scales)...")
    wc_df = load_onet_file('work_context')
    
    # For work context, we'll use whatever scale gives data, averaging across scales
    if 'Element Name' in wc_df.columns:
        # Filter suppressed
        if 'Recommend Suppress' in wc_df.columns:
            wc_df = wc_df[wc_df['Recommend Suppress'] != 'Y']
        
        wc_pivot = wc_df.pivot_table(
            index='O*NET-SOC Code',
            columns='Element Name',
            values='Data Value',
            aggfunc='mean'
        )
        wc_pivot.columns = [f"Work_Context_{col}" for col in wc_pivot.columns]
        feature_dfs.append(wc_pivot)
        logger.info(f"    {wc_pivot.shape[0]} occupations x {wc_pivot.shape[1]} features")
    
    # Merge all features
    if not feature_dfs:
        raise ValueError("No feature DataFrames were loaded!")
    
    all_features = feature_dfs[0]
    for df in feature_dfs[1:]:
        all_features = all_features.join(df, how='outer')
    
    logger.info(f"\n  Combined numeric features: {all_features.shape[0]} occupations x {all_features.shape[1]} features")
    
    return all_features


def extract_nlp_features(max_tfidf_features: int = 200) -> pd.DataFrame:
    """
    Extract NLP features from task statements.
    
    Creates:
    1. TF-IDF features (top N terms across all task descriptions)
    2. Keyword category counts (routine/creative/social/technical indicators)
    3. Task statistics (count, avg importance, variety)
    
    Args:
        max_tfidf_features: Number of TF-IDF features to extract
        
    Returns:
        DataFrame with O*NET-SOC Code as index, NLP features as columns
    """
    logger.info("=" * 70)
    logger.info("EXTRACTING NLP FEATURES FROM TASK STATEMENTS")
    logger.info("=" * 70)
    
    # Load task statements
    tasks_df = load_onet_file('task_statements')
    logger.info(f"  Total task statements: {len(tasks_df)}")
    
    # Concatenate all tasks per occupation
    task_text = tasks_df.groupby('O*NET-SOC Code')['Task'].apply(
        lambda x: ' '.join(x.dropna().astype(str))
    )
    logger.info(f"  Occupations with tasks: {len(task_text)}")
    
    # --- TF-IDF Features ---
    logger.info(f"  Extracting TF-IDF features (top {max_tfidf_features} terms)...")
    tfidf = TfidfVectorizer(
        max_features=max_tfidf_features,
        stop_words='english',
        min_df=5,           # Term must appear in at least 5 occupations
        max_df=0.95,        # Ignore terms in >95% of docs
        ngram_range=(1, 2)  # Unigrams and bigrams
    )
    
    tfidf_matrix = tfidf.fit_transform(task_text)
    tfidf_df = pd.DataFrame(
        tfidf_matrix.toarray(),
        index=task_text.index,
        columns=[f"TFIDF_{term}" for term in tfidf.get_feature_names_out()]
    )
    logger.info(f"    TF-IDF shape: {tfidf_df.shape}")
    
    # --- Keyword Category Counts ---
    logger.info("  Computing keyword category counts...")
    
    keyword_categories = {
        'routine_keywords': [
            'routine', 'standard', 'repetitive', 'record', 'file', 'process',
            'enter', 'data entry', 'sort', 'classify', 'verify', 'check',
            'copy', 'transcribe', 'compile'
        ],
        'creative_keywords': [
            'design', 'create', 'develop', 'innovate', 'creative', 'compose',
            'artistic', 'original', 'imagine', 'conceptualize', 'invent',
            'choreograph', 'perform', 'direct', 'produce'
        ],
        'social_keywords': [
            'collaborate', 'negotiate', 'counsel', 'teach', 'serve', 'advise',
            'communicate', 'mentor', 'coach', 'empathize', 'listen',
            'mediate', 'persuade', 'patient', 'client', 'customer'
        ],
        'technical_keywords': [
            'program', 'analyze', 'compute', 'operate', 'repair', 'maintain',
            'calibrate', 'diagnose', 'install', 'configure', 'troubleshoot',
            'code', 'algorithm', 'database', 'software'
        ],
        'physical_keywords': [
            'lift', 'carry', 'move', 'physical', 'manual', 'assemble',
            'construct', 'weld', 'drill', 'hammer', 'climb', 'bend',
            'reach', 'outdoor', 'heavy'
        ]
    }
    
    keyword_features = {}
    for onet_code, text in task_text.items():
        text_lower = text.lower()
        word_count = max(len(text_lower.split()), 1)
        features = {}
        for category, keywords in keyword_categories.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            features[f"KW_{category}"] = count
            features[f"KW_{category}_norm"] = count / word_count * 1000  # Per 1000 words
        keyword_features[onet_code] = features
    
    keyword_df = pd.DataFrame.from_dict(keyword_features, orient='index')
    logger.info(f"    Keyword features shape: {keyword_df.shape}")
    
    # --- Task Statistics ---
    logger.info("  Computing task statistics...")
    
    task_count = tasks_df.groupby('O*NET-SOC Code').size().rename('Task_Count')
    
    # Load task ratings for importance
    ratings_df = load_onet_file('task_ratings')
    
    # Filter for importance scale (typically 'IM' for Importance)
    if 'Scale ID' in ratings_df.columns:
        imp_ratings = ratings_df[ratings_df['Scale ID'] == 'IM']
    else:
        imp_ratings = ratings_df
    
    task_stats = imp_ratings.groupby('O*NET-SOC Code')['Data Value'].agg(
        Task_Avg_Importance='mean',
        Task_Std_Importance='std',
        Task_Max_Importance='max',
        Task_Min_Importance='min'
    )
    
    # Combine all NLP features
    nlp_features = tfidf_df.join(keyword_df, how='outer')
    nlp_features = nlp_features.join(task_count.to_frame(), how='outer')
    nlp_features = nlp_features.join(task_stats, how='outer')
    
    logger.info(f"\n  Combined NLP features: {nlp_features.shape[0]} occupations x {nlp_features.shape[1]} features")
    
    return nlp_features


def load_derived_features() -> pd.DataFrame:
    """
    Load derived features: education level, job zone, RIASEC interests.
    
    Returns:
        DataFrame with O*NET-SOC Code as index.
    """
    logger.info("=" * 70)
    logger.info("LOADING DERIVED FEATURES")
    logger.info("=" * 70)
    
    derived_dfs = []
    
    # --- Job Zones ---
    logger.info("  Loading Job Zones...")
    try:
        jz_df = load_onet_file('job_zones')
        if 'Job Zone' in jz_df.columns:
            jz_pivot = jz_df[['O*NET-SOC Code', 'Job Zone']].drop_duplicates()
            jz_pivot = jz_pivot.set_index('O*NET-SOC Code')
            derived_dfs.append(jz_pivot)
            logger.info(f"    Job Zones: {len(jz_pivot)} occupations")
    except Exception as e:
        logger.warning(f"    Could not load Job Zones: {e}")
    
    # --- Education ---
    logger.info("  Loading Education data...")
    try:
        edu_df = load_onet_file('education')
        if 'Category' in edu_df.columns and 'Data Value' in edu_df.columns:
            # Get education level that's required for the majority
            edu_pivot = edu_df.pivot_table(
                index='O*NET-SOC Code',
                columns='Category',
                values='Data Value',
                aggfunc='mean'
            )
            edu_pivot.columns = [f"Education_{col}" for col in edu_pivot.columns]
            derived_dfs.append(edu_pivot)
            logger.info(f"    Education: {edu_pivot.shape[0]} occupations x {edu_pivot.shape[1]} features")
        elif 'Element Name' in edu_df.columns:
            # Alternative structure
            edu_pivot = edu_df.pivot_table(
                index='O*NET-SOC Code',
                columns='Element Name',
                values='Data Value',
                aggfunc='mean'
            )
            edu_pivot.columns = [f"Education_{col}" for col in edu_pivot.columns]
            derived_dfs.append(edu_pivot)
            logger.info(f"    Education: {edu_pivot.shape[0]} occupations x {edu_pivot.shape[1]} features")
    except Exception as e:
        logger.warning(f"    Could not load Education: {e}")
    
    # --- Interests (RIASEC) ---
    logger.info("  Loading Interests (RIASEC)...")
    try:
        int_df = load_onet_file('interests')
        if 'Element Name' in int_df.columns and 'Data Value' in int_df.columns:
            # Filter for high-point scale if available
            if 'Scale ID' in int_df.columns:
                int_df_filtered = int_df[int_df['Scale ID'] == 'OI']
                if len(int_df_filtered) == 0:
                    int_df_filtered = int_df
            else:
                int_df_filtered = int_df
            
            int_pivot = int_df_filtered.pivot_table(
                index='O*NET-SOC Code',
                columns='Element Name',
                values='Data Value',
                aggfunc='mean'
            )
            int_pivot.columns = [f"Interest_{col}" for col in int_pivot.columns]
            derived_dfs.append(int_pivot)
            logger.info(f"    Interests: {int_pivot.shape[0]} occupations x {int_pivot.shape[1]} features")
    except Exception as e:
        logger.warning(f"    Could not load Interests: {e}")
    
    # Combine
    if derived_dfs:
        derived = derived_dfs[0]
        for df in derived_dfs[1:]:
            derived = derived.join(df, how='outer')
        logger.info(f"\n  Combined derived features: {derived.shape[0]} occupations x {derived.shape[1]} features")
        return derived
    else:
        return pd.DataFrame()


# ============================================================================
# SECTION 3: MAP F&O TO O*NET AND CREATE MODELING DATASET
# ============================================================================

def map_fo_to_onet(fo_df: pd.DataFrame) -> pd.DataFrame:
    """
    Map Frey & Osborne occupations to O*NET-SOC codes.
    
    Mapping strategy:
    1. Direct match on 6-digit SOC code
    2. For O*NET codes with sub-specializations (.01, .02, etc.),
       map to the parent .00 code
    3. Use occupation group averages for remaining
    
    Args:
        fo_df: Fixed F&O DataFrame with SOC_Code column
        
    Returns:
        DataFrame mapping O*NET-SOC Code -> F&O score and metadata
    """
    logger.info("=" * 70)
    logger.info("MAPPING F&O OCCUPATIONS TO O*NET CODES")
    logger.info("=" * 70)
    
    # Load O*NET occupations
    occ_df = load_onet_file("occupations")
    onet_codes = occ_df['O*NET-SOC Code'].tolist()
    logger.info(f"  O*NET occupations: {len(onet_codes)}")
    logger.info(f"  F&O occupations: {len(fo_df)}")
    
    # Build F&O lookup: SOC_Code -> (FO_Score, Occupation, Probability)
    fo_lookup = {}
    for _, row in fo_df.iterrows():
        soc = str(row['SOC_Code']).strip()
        if re.match(r'^\d{2}-\d{4}$', soc):
            fo_lookup[soc] = {
                'FO_Score': row['FO_Score'],
                'FO_Probability': row['Probability'],
                'FO_Occupation': row['Occupation']
            }
    
    logger.info(f"  Valid F&O lookup entries: {len(fo_lookup)}")
    
    # Map each O*NET occupation
    mapped_rows = []
    map_stats = {'direct': 0, 'parent': 0, 'group_avg': 0, 'unmapped': 0}
    
    for onet_code in onet_codes:
        base_soc = get_base_soc(onet_code)
        onet_title = occ_df[occ_df['O*NET-SOC Code'] == onet_code]['Title'].iloc[0]
        
        row_data = {
            'ONET_SOC_Code': onet_code,
            'Base_SOC': base_soc,
            'ONET_Title': onet_title,
        }
        
        # Strategy 1: Direct match on 6-digit SOC
        if base_soc in fo_lookup:
            row_data.update(fo_lookup[base_soc])
            row_data['Mapping_Method'] = 'direct'
            map_stats['direct'] += 1
        else:
            # Strategy 2: Try parent code (for sub-specializations)
            # e.g., 11-1011.03 -> check if any .00 or similar has data
            parent_soc = base_soc  # Already base
            
            # Check if another O*NET code with same base has a match
            found = False
            for fo_soc in fo_lookup:
                if fo_soc == base_soc:
                    row_data.update(fo_lookup[fo_soc])
                    row_data['Mapping_Method'] = 'parent'
                    map_stats['parent'] += 1
                    found = True
                    break
            
            if not found:
                # Strategy 3: Use 4-digit SOC group average
                soc_4 = base_soc[:5]  # e.g., '11-10' from '11-1011'
                group_scores = [
                    v['FO_Score'] for k, v in fo_lookup.items() 
                    if k.startswith(soc_4)
                ]
                
                if group_scores:
                    row_data['FO_Score'] = np.mean(group_scores)
                    row_data['FO_Probability'] = np.mean(group_scores) / 100
                    row_data['FO_Occupation'] = f"[Group avg: {soc_4}]"
                    row_data['Mapping_Method'] = 'group_avg'
                    map_stats['group_avg'] += 1
                else:
                    # Strategy 4: Use 2-digit SOC major group average
                    soc_2 = base_soc[:2]
                    major_scores = [
                        v['FO_Score'] for k, v in fo_lookup.items()
                        if k.startswith(soc_2)
                    ]
                    
                    if major_scores:
                        row_data['FO_Score'] = np.mean(major_scores)
                        row_data['FO_Probability'] = np.mean(major_scores) / 100
                        row_data['FO_Occupation'] = f"[Major group avg: {soc_2}]"
                        row_data['Mapping_Method'] = 'group_avg'
                        map_stats['group_avg'] += 1
                    else:
                        row_data['FO_Score'] = np.nan
                        row_data['FO_Probability'] = np.nan
                        row_data['FO_Occupation'] = '[Unmapped]'
                        row_data['Mapping_Method'] = 'unmapped'
                        map_stats['unmapped'] += 1
        
        mapped_rows.append(row_data)
    
    mapped_df = pd.DataFrame(mapped_rows)
    
    logger.info(f"\n  Mapping Results:")
    logger.info(f"    Direct match:      {map_stats['direct']} ({map_stats['direct']/len(onet_codes)*100:.1f}%)")
    logger.info(f"    Parent match:      {map_stats['parent']} ({map_stats['parent']/len(onet_codes)*100:.1f}%)")
    logger.info(f"    Group average:     {map_stats['group_avg']} ({map_stats['group_avg']/len(onet_codes)*100:.1f}%)")
    logger.info(f"    Unmapped:          {map_stats['unmapped']} ({map_stats['unmapped']/len(onet_codes)*100:.1f}%)")
    logger.info(f"    Total mapped:      {len(mapped_df) - map_stats['unmapped']}/{len(onet_codes)}")
    
    return mapped_df


def create_modeling_dataset(
    mapped_df: pd.DataFrame,
    numeric_features: pd.DataFrame,
    nlp_features: pd.DataFrame,
    derived_features: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Merge all features with F&O scores and create train/val/test splits.
    
    Args:
        mapped_df: F&O mapped to O*NET codes
        numeric_features: Consolidated O*NET numeric features
        nlp_features: TF-IDF and keyword features
        derived_features: Education, job zone, interests
        
    Returns:
        Tuple of (full_dataset, train_df, val_df, test_df)
    """
    logger.info("=" * 70)
    logger.info("CREATING MODELING DATASET")
    logger.info("=" * 70)
    
    # Set index for merging
    mapped_indexed = mapped_df.set_index('ONET_SOC_Code')
    
    # Merge all features
    dataset = mapped_indexed.copy()
    
    for name, feat_df in [
        ('numeric', numeric_features),
        ('nlp', nlp_features),
        ('derived', derived_features)
    ]:
        if feat_df is not None and not feat_df.empty:
            # Ensure index name matches
            feat_df.index.name = 'ONET_SOC_Code' if feat_df.index.name == 'O*NET-SOC Code' else feat_df.index.name
            if feat_df.index.name != 'ONET_SOC_Code':
                feat_df = feat_df.copy()
                feat_df.index.name = 'ONET_SOC_Code'
            dataset = dataset.join(feat_df, how='left')
            logger.info(f"  After joining {name}: {dataset.shape[1]} columns")
    
    # Identify feature columns (everything except metadata)
    meta_cols = ['Base_SOC', 'ONET_Title', 'FO_Score', 'FO_Probability', 
                 'FO_Occupation', 'Mapping_Method']
    feature_cols = [c for c in dataset.columns if c not in meta_cols]
    
    logger.info(f"\n  Full dataset: {dataset.shape[0]} occupations x {len(feature_cols)} features")
    logger.info(f"  Occupations with F&O score: {dataset['FO_Score'].notna().sum()}")
    logger.info(f"  Occupations without F&O score: {dataset['FO_Score'].isna().sum()}")
    
    # Handle missing feature values: impute with column median
    missing_before = dataset[feature_cols].isna().sum().sum()
    for col in feature_cols:
        if dataset[col].isna().any():
            median_val = dataset[col].median()
            if pd.isna(median_val):
                median_val = 0
            dataset[col] = dataset[col].fillna(median_val)
    missing_after = dataset[feature_cols].isna().sum().sum()
    logger.info(f"  Missing values imputed: {missing_before} -> {missing_after}")
    
    # Split into train/val/test (only occupations with F&O scores)
    has_score = dataset[dataset['FO_Score'].notna()].copy()
    no_score = dataset[dataset['FO_Score'].isna()].copy()
    
    logger.info(f"\n  Splitting {len(has_score)} scored occupations into train/val/test...")
    
    # 70% train, 15% validation, 15% test
    train_df, temp_df = train_test_split(has_score, test_size=0.30, random_state=42)
    val_df, test_df = train_test_split(temp_df, test_size=0.50, random_state=42)
    
    logger.info(f"    Train:      {len(train_df)} occupations")
    logger.info(f"    Validation: {len(val_df)} occupations")
    logger.info(f"    Test:       {len(test_df)} occupations")
    logger.info(f"    Predict:    {len(no_score)} occupations (no F&O score)")
    
    # Add split labels
    dataset['Split'] = 'predict'
    dataset.loc[train_df.index, 'Split'] = 'train'
    dataset.loc[val_df.index, 'Split'] = 'val'
    dataset.loc[test_df.index, 'Split'] = 'test'
    
    return dataset, train_df, val_df, test_df


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("MAEI DATA PREPARATION PIPELINE")
    logger.info("=" * 70)
    
    # Ensure output directories exist
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    
    # --- Step 1: Load and fix F&O data ---
    fo_df = load_and_fix_frey_osborne()
    fo_output = DATA_PROCESSED / "frey_osborne_fixed.csv"
    fo_df.to_csv(fo_output, index=False)
    logger.info(f"\n  Saved fixed F&O data to: {fo_output}")
    
    # --- Step 2: Load O*NET numeric features ---
    numeric_features = load_all_numeric_features()
    
    # --- Step 3: Extract NLP features ---
    nlp_features = extract_nlp_features(max_tfidf_features=200)
    
    # --- Step 4: Load derived features ---
    derived_features = load_derived_features()
    
    # --- Step 5: Map F&O to O*NET ---
    mapped_df = map_fo_to_onet(fo_df)
    mapped_output = DATA_PROCESSED / "frey_osborne_mapped.csv"
    mapped_df.to_csv(mapped_output, index=False)
    logger.info(f"\n  Saved mapped F&O data to: {mapped_output}")
    
    # --- Step 6: Create modeling dataset ---
    full_dataset, train_df, val_df, test_df = create_modeling_dataset(
        mapped_df, numeric_features, nlp_features, derived_features
    )
    
    # Save outputs
    import joblib
    
    dataset_output = DATA_PROCESSED / "modeling_dataset.pkl"
    joblib.dump({
        'full_dataset': full_dataset,
        'train': train_df,
        'val': val_df,
        'test': test_df,
        'feature_cols': [c for c in full_dataset.columns if c not in [
            'Base_SOC', 'ONET_Title', 'FO_Score', 'FO_Probability',
            'FO_Occupation', 'Mapping_Method', 'Split'
        ]]
    }, dataset_output)
    logger.info(f"\n  Saved modeling dataset to: {dataset_output}")
    
    # Also save a CSV summary of the features
    feature_summary = DATA_PROCESSED / "onet_features_consolidated.csv"
    full_dataset.to_csv(feature_summary)
    logger.info(f"  Saved feature summary to: {feature_summary}")
    
    # --- Verification ---
    logger.info("\n" + "=" * 70)
    logger.info("VERIFICATION CHECKS")
    logger.info("=" * 70)
    
    meta_cols = ['Base_SOC', 'ONET_Title', 'FO_Score', 'FO_Probability',
                 'FO_Occupation', 'Mapping_Method', 'Split']
    feature_cols = [c for c in full_dataset.columns if c not in meta_cols]
    
    assert len(full_dataset) > 900, f"Expected 900+ occupations, got {len(full_dataset)}"
    assert full_dataset['FO_Score'].notna().sum() > 500, "Too few occupations with F&O scores"
    assert len(feature_cols) > 50, f"Expected 50+ features, got {len(feature_cols)}"
    
    # Check for all-NaN feature columns
    all_nan_cols = [c for c in feature_cols if full_dataset[c].isna().all()]
    if all_nan_cols:
        logger.warning(f"  WARNING: {len(all_nan_cols)} features are all NaN: {all_nan_cols[:5]}...")
    else:
        logger.info("  ✓ No all-NaN feature columns")
    
    logger.info(f"  ✓ Dataset has {len(full_dataset)} occupations")
    logger.info(f"  ✓ {full_dataset['FO_Score'].notna().sum()} have F&O scores")
    logger.info(f"  ✓ {len(feature_cols)} features extracted")
    logger.info(f"  ✓ Score range: {full_dataset['FO_Score'].min():.1f} to {full_dataset['FO_Score'].max():.1f}")
    
    logger.info("\n" + "=" * 70)
    logger.info("DATA PREPARATION COMPLETE")
    logger.info("=" * 70)
