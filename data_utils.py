# data_utils.py
import pandas as pd
from pathlib import Path

# Define the base directory (where data_utils.py is located)
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Ensure the data directory exists
DATA_DIR.mkdir(exist_ok=True)

def load_csv(filename):
    """Loads a CSV file from the data folder into a pandas DataFrame."""
    file_path = DATA_DIR / filename
    return pd.read_csv(file_path)

def save_csv(df, filename):
    """Saves a pandas DataFrame to a CSV file in the data folder."""
    file_path = DATA_DIR / filename
    df.to_csv(file_path, index=False)
    print(f"Successfully saved to: {file_path}")