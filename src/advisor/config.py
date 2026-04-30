"""Advisor action setup and player-safe wording."""

ACTION_STEPS = {
    "training": {
        "avg_training_bonus": 2.5,
    },
    "activity": {
        "days_active_last_7_days": 1,
        "days_active_last_28_days": 1,
    },
    "starting_11_quality": {
        "avg_stars_top_11_players": 0.5,
        "avg_stars_top_3_players": 0.2,
    },
    "star_player_quality": {
        "avg_stars_top_3_players": 0.5,
        "avg_stars_top_11_players": 0.15,
    },
}

FEATURE_CAPS = {
    "avg_training_bonus": 30.0,
    "days_active_last_7_days": 7.0,
    "days_active_last_28_days": 28.0,
}

ACTION_TEXT = {
    "training": {
        "focus": "Raise training bonuses",
        "focus_high": "Maximize training bonuses",
        "why": "Strong training gives the Association a better foundation going into the matchup.",
        "why_high": "Your matches carry extra weight for the Association, so strong training here is especially important.",
        "action": "Complete training before the weekend and keep bonuses high before matches.",
    },
    "activity": {
        "focus": "Stay active before the tournament",
        "focus_high": "Protect match readiness",
        "why": "Regular activity helps keep your team ready for weekend matches.",
        "why_high": "Your matches carry extra weight for the Association, so staying ready before the weekend is especially important.",
        "action": "Log in before the tournament and keep your team ready.",
    },
    "starting_11_quality": {
        "focus": "Improve your starting 11 over time",
        "focus_high": "Strengthen your starting 11 over time",
        "why": "A stronger starting 11 gives the Association more stability across the matchup.",
        "why_high": "Your matches carry extra weight for the Association, so long-term squad strength matters more in this slot.",
        "action": "Keep your team ready this weekend. Longer term, make upgrades to your starting 11.",
    },
    "star_player_quality": {
        "focus": "Improve your best players over time",
        "focus_high": "Strengthen your key players over time",
        "why": "Stronger key players can make important matches easier to control.",
        "why_high": "Your matches carry extra weight for the Association, so stronger key players can be especially valuable over time.",
        "action": "Keep your team ready this weekend. Longer term, prioritize upgrades to your strongest players.",
    },
    "maintain": {
        "focus": "Keep readiness steady",
        "focus_high": "Protect match readiness",
        "why": "Good tournament readiness is about consistency. Keep your team ready and avoid dropping form before the weekend.",
        "why_high": "Your matches carry extra weight for the Association, so steady readiness is especially important.",
        "action": "Stay active, complete normal training, and keep bonuses ready before the weekend.",
    },
}

ACTIONS = list(ACTION_STEPS.keys())
