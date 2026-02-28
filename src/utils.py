"""
utils.py
Purpose: Shared utility functions, file paths, and configuration for the MAEI project.
Author: Aarya
Date: 2026-02-26
"""

import logging
from pathlib import Path

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

BASE_PATH = Path("C:/Users/aarya/OneDrive/Desktop/Graduation_Project_Data/MAEI_Project/Grad-Project")
ONET_PATH = BASE_PATH / "data" / "raw" / "db_30_1_text"
FO_DATA_PATH = BASE_PATH / "data" / "raw" / "F&O" / "automation_data_by_state.csv"

# Output directories
DATA_RAW = BASE_PATH / "data" / "raw"
DATA_PROCESSED = BASE_PATH / "data" / "processed"
DATA_EXTERNAL = BASE_PATH / "data" / "external"
MODELS_DIR = BASE_PATH / "models"
RESULTS_DIR = BASE_PATH / "results"
FIGURES_DIR = BASE_PATH / "figures"
SRC_DIR = BASE_PATH / "src"

# ============================================================================
# O*NET FILE PATHS
# ============================================================================

ONET_FILES = {
    "occupations": ONET_PATH / "Occupation Data.txt",
    "abilities": ONET_PATH / "Abilities.txt",
    "skills": ONET_PATH / "Skills.txt",
    "knowledge": ONET_PATH / "Knowledge.txt",
    "work_activities": ONET_PATH / "Work Activities.txt",
    "work_context": ONET_PATH / "Work Context.txt",
    "work_styles": ONET_PATH / "Work Styles.txt",
    "task_statements": ONET_PATH / "Task Statements.txt",
    "task_ratings": ONET_PATH / "Task Ratings.txt",
    "education": ONET_PATH / "Education, Training, and Experience.txt",
    "interests": ONET_PATH / "Interests.txt",
    "job_zones": ONET_PATH / "Job Zones.txt",
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger with standard formatting."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(name)

# ============================================================================
# DATA LOADING HELPERS
# ============================================================================

def load_onet_file(key: str, **kwargs):
    """Load an O*NET file by its key name. Returns a pandas DataFrame."""
    import pandas as pd
    filepath = ONET_FILES[key]
    return pd.read_csv(filepath, sep='\t', encoding='utf-8', **kwargs)

def get_base_soc(onet_code: str) -> str:
    """
    Extract 6-digit SOC code from O*NET-SOC code.
    Example: '11-1011.00' -> '11-1011'
             '11-1011.03' -> '11-1011'
    """
    return onet_code.split('.')[0] if '.' in str(onet_code) else str(onet_code)
