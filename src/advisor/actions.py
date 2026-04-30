"""Apply simulated manager actions."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ACTION_STEPS, FEATURE_CAPS


def apply_cap(series: pd.Series, col: str) -> pd.Series:
    if col in FEATURE_CAPS:
        return np.minimum(FEATURE_CAPS[col], series)
    return series


def apply_manager_action(clan_members: pd.DataFrame, user_id: str, action: str) -> pd.DataFrame:
    """Apply one candidate action to one manager.

    Each action changes only the feature family represented by that action.
    The activity action also resets recency because logging in is part of that action.
    """
    df = clan_members.copy()
    mask = df["user_id"] == user_id

    if mask.sum() != 1:
        raise ValueError(f"Expected exactly one manager with user_id={user_id}, found {mask.sum()}.")

    if action not in ACTION_STEPS:
        raise ValueError(f"Unknown action: {action}")

    for col, delta in ACTION_STEPS[action].items():
        df.loc[mask, col] = apply_cap(df.loc[mask, col] + delta, col)

    if action == "activity":
        df.loc[mask, "days_since_last_active"] = 0

    return df
