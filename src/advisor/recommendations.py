"""Turn simulated action scores into manager-level advice."""

from __future__ import annotations

import pandas as pd

from src.common.features import add_manager_slots
from .actions import apply_manager_action
from .config import ACTIONS, ACTION_TEXT
from .scoring import score_matchup_probability


def get_two_clan_members(full_members: pd.DataFrame, clan_a_id: str, clan_b_id: str) -> pd.DataFrame:
    two_clans = full_members[full_members["clan_id"].isin([clan_a_id, clan_b_id])].copy()
    counts = two_clans.groupby("clan_id")["user_id"].nunique()

    for clan_id in [clan_a_id, clan_b_id]:
        if counts.get(clan_id, 0) != 6:
            raise ValueError(f"Expected 6 managers for clan {clan_id}, found {counts.get(clan_id, 0)}.")

    return two_clans


def mark_high_multiplier_managers(clan_members: pd.DataFrame) -> pd.DataFrame:
    """Mark managers who share the highest multiplier in the clan.

    If all six managers share the same multiplier, nobody gets special wording.
    """
    out = clan_members.copy()
    multipliers = pd.to_numeric(out["clan_multiplier"], errors="coerce")

    if multipliers.nunique(dropna=True) <= 1:
        out["is_high_multiplier"] = False
        return out

    max_multiplier = multipliers.max(skipna=True)
    out["is_high_multiplier"] = multipliers.eq(max_multiplier)
    return out


def evaluate_clan_actions(
    model,
    full_members: pd.DataFrame,
    clan_a_id: str,
    clan_b_id: str,
    advised_clan_id: str,
    feature_cols: list[str],
    value_cols: list[str],
) -> pd.DataFrame:
    """Evaluate all candidate actions for every manager in one advised clan."""
    if advised_clan_id not in {clan_a_id, clan_b_id}:
        raise ValueError("advised_clan_id must be either clan_a_id or clan_b_id")

    two_clans = add_manager_slots(get_two_clan_members(full_members, clan_a_id, clan_b_id))

    clan_a_members = two_clans[two_clans["clan_id"] == clan_a_id].copy()
    clan_b_members = two_clans[two_clans["clan_id"] == clan_b_id].copy()

    base_p_a_win = score_matchup_probability(
        model=model,
        matchup_members=pd.concat([clan_a_members, clan_b_members], ignore_index=True),
        clan_a_id=clan_a_id,
        clan_b_id=clan_b_id,
        feature_cols=feature_cols,
        value_cols=value_cols,
    )

    advised_members = clan_a_members if advised_clan_id == clan_a_id else clan_b_members
    other_members = clan_b_members if advised_clan_id == clan_a_id else clan_a_members
    advised_members = mark_high_multiplier_managers(advised_members)

    rows = []
    for user_id in advised_members["user_id"]:
        manager_before = advised_members.loc[advised_members["user_id"] == user_id].iloc[0]

        for action in ACTIONS:
            modified_advised = apply_manager_action(advised_members, user_id, action)

            if advised_clan_id == clan_a_id:
                modified_two_clans = pd.concat([modified_advised, other_members], ignore_index=True)
            else:
                modified_two_clans = pd.concat([other_members, modified_advised], ignore_index=True)

            p_after_a_win = score_matchup_probability(
                model=model,
                matchup_members=modified_two_clans,
                clan_a_id=clan_a_id,
                clan_b_id=clan_b_id,
                feature_cols=feature_cols,
                value_cols=value_cols,
            )

            if advised_clan_id == clan_a_id:
                lift_for_advised_clan = p_after_a_win - base_p_a_win
            else:
                lift_for_advised_clan = base_p_a_win - p_after_a_win

            rows.append({
                "clan_a_id": clan_a_id,
                "clan_b_id": clan_b_id,
                "advised_clan_id": advised_clan_id,
                "user_id": user_id,
                "slot": int(manager_before["slot"]),
                "is_high_multiplier": bool(manager_before["is_high_multiplier"]),
                "action": action,
                "p_clan_a_win_before": base_p_a_win,
                "p_clan_a_win_after": p_after_a_win,
                "lift_for_advised_clan": lift_for_advised_clan,
                "current_multiplier": manager_before["clan_multiplier"],
            })

    out = pd.DataFrame(rows)
    out["rank_for_manager"] = (
        out
        .sort_values(["user_id", "lift_for_advised_clan"], ascending=[True, False])
        .groupby("user_id")
        .cumcount() + 1
    )
    return out


def priority_label(best_lift: float, is_high_multiplier: bool) -> str:
    if best_lift > 0 and is_high_multiplier:
        return "High priority"
    if is_high_multiplier:
        return "Moderate priority"
    if best_lift > 0:
        return "Moderate priority"
    return "Low priority"


def combine_focus(actions: list[str], is_high_multiplier: bool = False) -> str:
    action_set = set(actions)

    if action_set == {"training", "activity"}:
        return "Maximize training and activity" if is_high_multiplier else "Raise training bonuses and stay active"
    if action_set == {"training", "starting_11_quality"}:
        return "Maximize bonuses now; strengthen starting 11 over time" if is_high_multiplier else "Raise bonuses now; improve starting 11 over time"
    if action_set == {"training", "star_player_quality"}:
        return "Maximize bonuses now; strengthen key players over time" if is_high_multiplier else "Raise bonuses now; improve best players over time"
    if action_set == {"activity", "starting_11_quality"}:
        return "Protect readiness now; strengthen starting 11 over time" if is_high_multiplier else "Stay active now; improve starting 11 over time"
    if action_set == {"activity", "star_player_quality"}:
        return "Protect readiness now; strengthen key players over time" if is_high_multiplier else "Stay active now; improve best players over time"
    if action_set == {"starting_11_quality", "star_player_quality"}:
        return "Strengthen squad quality over time"

    return " and ".join(ACTION_TEXT[a]["focus"].lower() for a in actions).capitalize()


def combine_action_text(actions: list[str]) -> str:
    action_set = set(actions)

    if action_set == {"training", "activity"}:
        return "Complete training before the weekend, keep bonuses high, and stay active before matches."

    if "starting_11_quality" in action_set or "star_player_quality" in action_set:
        short_term = "Keep your team ready this weekend."
        if "training" in action_set:
            short_term = "Complete training before the weekend and keep bonuses high."
        if "activity" in action_set:
            short_term = "Stay active before the tournament and keep your team ready."

        long_term_bits = []
        if "starting_11_quality" in action_set:
            long_term_bits.append("upgrade your starting 11")
        if "star_player_quality" in action_set:
            long_term_bits.append("prioritize your strongest players")

        return short_term + " Longer term, " + " and ".join(long_term_bits) + "."

    return " ".join(ACTION_TEXT[a]["action"] for a in actions)


def combine_why(actions: list[str], is_high_multiplier: bool = False) -> str:
    action_set = set(actions)

    if is_high_multiplier:
        return "Your matches carry extra weight for the Association, so strong training and steady progress here are especially important."

    if "training" in action_set and "activity" in action_set:
        return "Strong training and regular activity give the Association a better foundation going into the matchup."

    if "starting_11_quality" in action_set or "star_player_quality" in action_set:
        return "Weekend readiness matters now, while squad strength is the longer-term way to make future matchups easier."

    return "Strong training gives the Association a better foundation going into the matchup."


def choose_manager_message(manager_rows: pd.DataFrame) -> dict:
    """Turn action scores for one manager into a player-facing message."""
    ranked = manager_rows.sort_values("lift_for_advised_clan", ascending=False).reset_index(drop=True)

    best = ranked.iloc[0]
    second = ranked.iloc[1]

    best_lift = float(best["lift_for_advised_clan"])
    second_lift = float(second["lift_for_advised_clan"])
    is_high = bool(best["is_high_multiplier"])
    priority = priority_label(best_lift, is_high)

    if best_lift <= 0:
        key = "maintain"
        return {
            "priority": priority,
            "focus": ACTION_TEXT[key]["focus_high"] if is_high else ACTION_TEXT[key]["focus"],
            "why": ACTION_TEXT[key]["why_high"] if is_high else ACTION_TEXT[key]["why"],
            "action": ACTION_TEXT[key]["action"],
            "actions_used": ["maintain"],
        }

    best_action = best["action"]

    if is_high and second_lift > 0:
        actions = [best_action, second["action"]]
        return {
            "priority": priority,
            "focus": combine_focus(actions, is_high_multiplier=True),
            "why": combine_why(actions, is_high_multiplier=True),
            "action": combine_action_text(actions),
            "actions_used": actions,
        }

    text = ACTION_TEXT[best_action]
    return {
        "priority": priority,
        "focus": text["focus_high"] if is_high else text["focus"],
        "why": text["why_high"] if is_high else text["why"],
        "action": text["action"],
        "actions_used": [best_action],
    }


def build_action_scores(*advice_frames: pd.DataFrame) -> pd.DataFrame:
    action_scores = pd.concat(advice_frames, ignore_index=True)
    return action_scores.sort_values(
        ["advised_clan_id", "slot", "user_id", "lift_for_advised_clan"],
        ascending=[True, True, True, False],
    )


def build_manager_summary(action_scores: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for (clan_id, user_id), g in action_scores.groupby(["advised_clan_id", "user_id"], sort=False):
        g = g.sort_values("lift_for_advised_clan", ascending=False).reset_index(drop=True)
        msg = choose_manager_message(g)

        rows.append({
            "advised_clan_id": clan_id,
            "user_id": user_id,
            "priority": msg["priority"],
            "focus": msg["focus"],
            "actions_used": ", ".join(msg["actions_used"]),
        })

    return pd.DataFrame(rows).sort_values(["advised_clan_id", "user_id"])
