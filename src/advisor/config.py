"""Advisor action setup and player-safe wording."""

ACTION_STEPS = {
    "training": {
        "avg_training_bonus": 2.5,
        "days_active_last_7_days": 1,
        "days_active_last_28_days": 1,
    },
    "activity": {
        "days_active_last_7_days": 1,
        "days_active_last_28_days": 1,
    },
    "starting_11_quality": {
        "avg_stars_top_11_players": 0.3,
        "avg_stars_top_3_players": 0.1,
    },
    "star_player_quality": {
        "avg_stars_top_3_players": 0.3,
        "avg_stars_top_11_players": 0.1,
    },
}

FEATURE_CAPS = {
    "avg_training_bonus": 30.0,
    "days_active_last_7_days": 7.0,
    "days_active_last_28_days": 28.0,
}

RECENCY_RESET_ACTIONS = {
    "training",
    "activity",
}

ACTION_TEXT = {
    "training": {
        "focus": "Complete training",
        "focus_high": "Prioritize training now",
        "why": "Training bonuses are one of the quickest ways to improve match readiness before the war.",
        "why_high": "This manager's results count more for the Association, so missing training bonuses here can cost more.",
        "action": "Have this manager complete training now and keep bonuses high before matches.",
    },
    "activity": {
        "focus": "Ping this manager to log in",
        "focus_high": "Urgent login reminder",
        "why": "If this manager does not log in before the war, they may miss training, lineup checks, and final preparation.",
        "why_high": "This manager's matches carry extra weight, so the clan should make sure they log in before the war.",
        "action": "Ping this manager to log in before the war and check their team readiness.",
    },
    "starting_11_quality": {
        "focus": "Check starting 11",
        "focus_high": "Prioritize starting 11 check",
        "why": "The starting 11 decides most of the match strength, so a final lineup check can prevent avoidable weak spots.",
        "why_high": "This manager's matches carry extra weight, so the starting 11 should be checked carefully before the war.",
        "action": "Have this manager check the starting 11 and make any available upgrades before matches.",
    },
    "star_player_quality": {
        "focus": "Check key players",
        "focus_high": "Prioritize key-player check",
        "why": "Strong key players can make close matches easier to control, especially when the matchup is tight.",
        "why_high": "This manager's matches carry extra weight, so their strongest players should be ready before the war.",
        "action": "Have this manager check their strongest players and make any available upgrades before matches.",
    },
    "maintain": {
        "focus": "No urgent action",
        "focus_high": "Keep ready",
        "why": "This manager already looks prepared enough, so the clan does not need to spend extra attention here.",
        "why_high": "This manager's matches matter a lot, but their preparation already looks stable. Keep it that way.",
        "action": "No urgent ping needed. Just keep normal training, bonuses, and lineup readiness in place.",
    },
}

ACTIONS = list(ACTION_STEPS.keys())