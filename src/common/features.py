"""Shared feature engineering for training and advisor notebooks.

Both notebooks import this module so the model and the advisor use the same
matchup feature table.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def prepare_members(df: pd.DataFrame, value_cols: list[str]) -> pd.DataFrame:
    """Convert numeric manager columns to numeric dtype."""
    out = df.copy()
    numeric_cols = list(value_cols) + ["clan_multiplier"]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def add_manager_slots(members_df: pd.DataFrame) -> pd.DataFrame:
    """Sort managers inside a clan and assign a stable slot from 1 to 6."""
    out = (
        members_df
        .sort_values(
            ["clan_id", "avg_stars_top_11_players", "avg_training_bonus", "user_id"],
            ascending=[True, False, False, True],
        )
        .copy()
    )
    out["slot"] = out.groupby("clan_id").cumcount() + 1
    return out.loc[out["slot"] <= 6].copy()


def _check_six_managers_per_clan(slot_members: pd.DataFrame) -> None:
    clan_sizes = slot_members.groupby("clan_id").size()
    bad_clans = clan_sizes[clan_sizes != 6]
    if len(bad_clans):
        raise ValueError(f"Expected 6 managers per clan, found {len(bad_clans)} bad clans.")


def make_clan_features(members_df: pd.DataFrame, value_cols: list[str]) -> pd.DataFrame:
    """Aggregate six manager rows into one row per clan."""
    slot_members = add_manager_slots(members_df)
    _check_six_managers_per_clan(slot_members)

    for col in value_cols:
        slot_members[f"{col}_x_multiplier"] = (
            slot_members[col] * slot_members["clan_multiplier"]
        )

    rows = []
    for clan_id, g in slot_members.groupby("clan_id", sort=False):
        g = g.sort_values("slot")
        row = {"clan_id": clan_id}

        for col in value_cols:
            values = g[col].astype(float).to_numpy()
            row[f"{col}_mean"] = np.nanmean(values)
            row[f"{col}_min"] = np.nanmin(values)
            row[f"{col}_max"] = np.nanmax(values)
            row[f"{col}_std"] = np.nanstd(values)
            row[f"{col}_top2_avg"] = np.nanmean(values[:2])
            row[f"{col}_bottom2_avg"] = np.nanmean(values[-2:])

            weighted_values = g[f"{col}_x_multiplier"].astype(float).to_numpy()
            row[f"{col}_x_multiplier_mean"] = np.nanmean(weighted_values)
            row[f"{col}_x_multiplier_min"] = np.nanmin(weighted_values)
            row[f"{col}_x_multiplier_max"] = np.nanmax(weighted_values)
            row[f"{col}_x_multiplier_std"] = np.nanstd(weighted_values)
            row[f"{col}_x_multiplier_top2_avg"] = np.nanmean(weighted_values[:2])
            row[f"{col}_x_multiplier_bottom2_avg"] = np.nanmean(weighted_values[-2:])

        rows.append(row)

    return pd.DataFrame(rows)


def make_matchup_features(
    members_df: pd.DataFrame,
    matches_df: pd.DataFrame,
    value_cols: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """Build directional clan_1 minus clan_2 matchup features."""
    clan_features = make_clan_features(members_df, value_cols=value_cols)

    matchup = (
        matches_df.copy()
        .merge(
            clan_features.add_prefix("clan1_"),
            left_on="clan_1_id",
            right_on="clan1_clan_id",
            how="left",
        )
        .merge(
            clan_features.add_prefix("clan2_"),
            left_on="clan_2_id",
            right_on="clan2_clan_id",
            how="left",
        )
    )

    feature_cols = []
    for feat in clan_features.columns.drop("clan_id"):
        col = f"{feat}_diff"
        matchup[col] = matchup[f"clan1_{feat}"] - matchup[f"clan2_{feat}"]
        feature_cols.append(col)

    if "clan_winner" in matchup.columns:
        matchup["target_clan1_win"] = (matchup["clan_winner"] == 1).astype(int)

    if {"clan_1_points", "clan_2_points"}.issubset(matchup.columns):
        matchup["point_diff"] = matchup["clan_1_points"] - matchup["clan_2_points"]
        matchup["abs_point_diff"] = matchup["point_diff"].abs()

    return matchup, feature_cols


def build_matchup_feature_table(
    members_df: pd.DataFrame,
    matches_df: pd.DataFrame,
    value_cols: list[str],
) -> tuple[pd.DataFrame, list[str]]:
    """Public helper used by both the training and advisor notebooks."""
    return make_matchup_features(
        members_df=members_df,
        matches_df=matches_df,
        value_cols=value_cols,
    )
