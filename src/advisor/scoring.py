"""Scoring helpers for the advisor."""

from __future__ import annotations

import pandas as pd

from src.common.features import build_matchup_feature_table


def score_matchup_probability(
    model,
    matchup_members: pd.DataFrame,
    clan_a_id: str,
    clan_b_id: str,
    feature_cols: list[str],
    value_cols: list[str],
) -> float:
    """Return P(clan_a wins) using the trained classifier."""
    one_match = pd.DataFrame({
        "clan_1_id": [clan_a_id],
        "clan_2_id": [clan_b_id],
    })

    one_matchup, _ = build_matchup_feature_table(
        members_df=matchup_members,
        matches_df=one_match,
        value_cols=value_cols,
    )

    missing = sorted(set(feature_cols) - set(one_matchup.columns))
    if missing:
        raise ValueError(f"Missing features for model: {missing[:20]}")

    X_one = one_matchup[feature_cols].copy()
    return float(model.predict_proba(X_one)[:, 1][0])
