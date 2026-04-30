"""Render player-facing advisor cards."""

from __future__ import annotations

import pandas as pd

from .recommendations import (
    evaluate_clan_actions,
    build_action_scores,
    build_manager_summary,
    choose_manager_message,
)


def format_manager_card(user_id: str, manager_rows: pd.DataFrame) -> str:
    msg = choose_manager_message(manager_rows)

    lines = [
        f"Manager {user_id}",
        f"  Priority : {msg['priority']}",
        f"  Focus    : {msg['focus']}",
        f"  Action   : {msg['action']}",
        f"  Why      : {msg['why']}",
    ]
    return "\n".join(lines)


def render_clan_advice(advice_df: pd.DataFrame, clan_id: str) -> str:
    lines = []
    lines.append(f"CLAN {clan_id} — MANAGER ADVICE")
    lines.append("=" * 92)

    manager_order = (
        advice_df[["user_id", "slot"]]
        .drop_duplicates()
        .sort_values(["slot", "user_id"])
    )

    for i, row in enumerate(manager_order.itertuples(index=False), start=1):
        user_id = row.user_id
        g = advice_df[advice_df["user_id"] == user_id].copy()
        lines.append("")
        lines.append(f"{i}. {format_manager_card(user_id, g)}")

    return "\n".join(lines)


def render_matchup_advice(
    model,
    full_members: pd.DataFrame,
    clan_a_id: str,
    clan_b_id: str,
    feature_cols: list[str],
    value_cols: list[str],
) -> tuple[str, pd.DataFrame]:
    clan_a_advice = evaluate_clan_actions(
        model=model,
        full_members=full_members,
        clan_a_id=clan_a_id,
        clan_b_id=clan_b_id,
        advised_clan_id=clan_a_id,
        feature_cols=feature_cols,
        value_cols=value_cols,
    )

    clan_b_advice = evaluate_clan_actions(
        model=model,
        full_members=full_members,
        clan_a_id=clan_a_id,
        clan_b_id=clan_b_id,
        advised_clan_id=clan_b_id,
        feature_cols=feature_cols,
        value_cols=value_cols,
    )

    lines = []
    lines.append("#" * 92)
    lines.append("SMART ASSOCIATION ADVISOR")
    lines.append("#" * 92)
    lines.append(f"Matchup : Clan {clan_a_id} vs Clan {clan_b_id}")
    lines.append("#" * 92)
    lines.append("")
    lines.append(render_clan_advice(clan_a_advice, clan_a_id))
    lines.append("")
    lines.append("-" * 92)
    lines.append("")
    lines.append(render_clan_advice(clan_b_advice, clan_b_id))

    action_scores = build_action_scores(clan_a_advice, clan_b_advice)
    manager_summary = build_manager_summary(action_scores)

    return "\n".join(lines), manager_summary
