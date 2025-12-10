"""Helper utilities for working with the FiNER dataset.

This module shows how you *could* load a sample of the FiNER dataset
from a CSV file and inspect its contents. The core web app only needs
raw text input, but this helper is useful for experimentation and for
documenting how the dataset relates to the project.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd


def load_finer_sample(path: str = "data/finer_sample.csv", n_rows: int = 5) -> pd.DataFrame:
    """Load a small sample from the FiNER dataset.

    Parameters
    ----------
    path : str
        Path to the FiNER CSV file. In this project we assume a file
        like ``data/finer_sample.csv`` exists locally.
    n_rows : int
        Number of rows to read and display as a sample.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the sample rows.
    """

    df = pd.read_csv(path).head(n_rows)

    # Print a short summary so students can see the structure
    print("Loaded FiNER sample from:", path)
    print("Columns:", list(df.columns))
    print(df.head(n_rows))

    # Example: if the dataset contains columns like
    # - "sentence" or "text" for the news fragment
    # - "entity" and "label" for the annotated entity
    # you could later map those labels into your custom categories.

    return df
