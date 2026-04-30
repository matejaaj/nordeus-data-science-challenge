# Top Eleven Association Winner Prediction + Smart Advisor

This project predicts the winner of Top Eleven Association / Clan tournament matchups and includes a small manager-level advisory system built on top of the trained classifier.

## Project structure

```text
artifacts/
└── clan_winner_classifier_artifact.joblib      # Saved trained classifier and metadata used by the advisor.

data/

notebooks/
├── eda/
│   ├── clan_matches.ipynb                      # Match-level EDA.
│   ├── member_stats.ipynb                      # Member-level EDA.
│   ├── joined_clan_matches_member_stats.ipynb  # Cross-file checks and multiplier consistency checks.
│   └── joined_features.ipynb                   # Early joined-feature exploration.
├── train_classifier.ipynb                      # Builds features, trains the classifier, evaluates CV, and creates predictions.
└── advisor_demo.ipynb                          # Demonstrates the manager-level advisory system.

src/
├── common/
│   └── features.py                             # Shared feature-building code used by both training and advisor scoring.
└── advisor/
    ├── actions.py                              # Candidate manager actions and player-safe wording.
    ├── config.py                               # Advisor-level constants/configuration.
    ├── scoring.py                              # Scores matchups before and after simulated manager actions.
    ├── recommendations.py                      # Chooses the best recommendation for each manager.
    └── rendering.py                            # Converts recommendations into player-facing advice text.

clan_winner_predictions.csv                     # Final challenge submission file.
```

## Feature engineering

Each clan has six managers, so the raw member table is first aggregated to clan-level features.

For each key manager feature, I compute roster summaries such as:

- mean
- min
- max
- standard deviation
- top-2 average
- bottom-2 average

I compute the same summaries after multiplying each manager value by `clan_multiplier`, so the model can capture whether activity, preparation, or quality is attached to higher-impact managers.

The final model features are directional matchup differences:

```text
clan_1_feature - clan_2_feature
```

This matches the binary target:

```text
target_clan1_win = 1 if clan_1 wins, else 0
```

The final feature set focuses on recent activity, recency, training count, training bonus, starting 11 quality, top-player quality, and multiplier-weighted versions of those same signals.

### EDA: multiplier inconsistency edge case

I found a small multiplier consistency edge case during EDA. Some clan appearances exceeded the theoretical two-leg maximum implied by the multipliers in `member_stats_training.csv`. After checking with the Nordeus team, this was confirmed to be expected game behavior: the member table is a real pre-match snapshot, but users can increase their Association multiplier after the snapshot is taken through an in-game event reward. Other values, such as training bonuses or squad quality, can also change after the snapshot. Because the task is to predict before matches begin, I keep using only the available pre-match snapshot and treat multiplier as a useful but imperfect signal.

## Model and results

The final model is an XGBoost binary classifier evaluated with stratified cross-validation using accuracy, matching the challenge metric.

The model is weak-to-moderate but has real signal. 

| Model | Average CV accuracy |
|---|---:|
| XGBoost classifier | 0.588974 |


OOF accuracy by realised absolute point-difference bucket:

| Margin bucket | Actual point-diff range | OOF accuracy |
|---|---:|---:|
| Q1 closest | 1–10 | 0.5171 |
| Q2 | 11–20 | 0.54108 |
| Q3 | 21–31 | 0.587762 |
| Q4 | 32–47 | 0.619888 |
| Q5 largest | 48–144 | 0.680776 |


## Interpretation and data limitations

The average CV accuracy is modest, but the margin-bucket diagnostics show that the model is not purely random. It is close to a coin flip on the closest matches and becomes more accurate as the realised point margin increases. This suggests that the available features capture broad clan strength and preparation gaps better than they capture narrow matchup outcomes.

The main limitation is that the biggest likely signal is not observed: the actual manager-to-manager matchup structure. The data does not show the real pairings, schedule changes, or individual match outcomes. It is also only a pre-match snapshot, so some manager values can change before or between the matches. Because of this, the model has limited information for close matchups where small tactical or pairing differences may decide the result.

## Advisory system

The advisor is a manager-level preparation assistant built on top of the trained classifier. It is meant to turn model signal into practical preparation guidance, not to claim causal effects or guaranteed outcomes.

For every manager in both clans, it simulates a small set of possible actions, rebuilds the same matchup features, and checks which action most improves that manager's clan outlook according to the trained classifier.

The internal simulations are not shown directly to players. The advisor translates them into natural preparation priorities, so the output does not ask managers to chase artificial numeric changes such as “+0.5 stars”; it instead gives practical guidance like improving readiness, keeping bonuses high, or strengthening the squad over time.

The recommendations should be read as model-estimated priorities for where attention may be most useful, not as guarantees that a specific action will change the match result.
The actions and deltas were not picked randomly. I first inspected the distributions of the underlying manager features, then chose small, interpretable changes that are meaningful on the observed scale of the data. For example, `avg_training_bonus` ranges from 0 to 30 with a median around 10, so a `+2.5` bonus change is noticeable but not extreme. `days_active_last_7_days` is capped at 7, so the activity action adds one active day and respects the cap. Quality changes are smaller because star averages are continuous and move on a tighter scale.

The simulated actions are:

| Action | Internal feature change | Player-facing meaning |
|---|---|---|
| Training | `avg_training_bonus + 2.5` | Raise training bonuses before the weekend |
| Activity | `days_active_last_7_days + 1`, `days_active_last_28_days + 1` | Stay active before the tournament |
| Starting 11 quality | `avg_stars_top_11_players + 0.5`, `avg_stars_top_3_players + 0.2` | Improve starting 11 quality over time |
| Key player quality | `avg_stars_top_3_players + 0.5`, `avg_stars_top_11_players + 0.15` | Improve best players over time |


## Example advisor output

```text
############################################################################################
SMART ASSOCIATION ADVISOR
############################################################################################
Matchup : Clan clan_44207 vs Clan clan_43560
############################################################################################

CLAN clan_44207 — MANAGER ADVICE
============================================================================================

1. Manager user_154960
  Priority : High priority
  Focus    : Maximize training bonuses
  Action   : Complete training before the weekend and keep bonuses high before matches.
  Why      : Your matches carry extra weight for the Association, so strong training here is especially important.

2. Manager user_254405
  Priority : Moderate priority
  Focus    : Protect match readiness
  Action   : Stay active, complete normal training, and keep bonuses ready before the weekend.
  Why      : Your matches carry extra weight for the Association, so steady readiness is especially important.

3. Manager user_254263
  Priority : Low priority
  Focus    : Keep readiness steady
  Action   : Stay active, complete normal training, and keep bonuses ready before the weekend.
  Why      : Good tournament readiness is about consistency. Keep your team ready and avoid dropping form before the weekend.

4. Manager user_260099
  Priority : Low priority
  Focus    : Keep readiness steady
  Action   : Stay active, complete normal training, and keep bonuses ready before the weekend.
  Why      : Good tournament readiness is about consistency. Keep your team ready and avoid dropping form before the weekend.

5. Manager user_171029
  Priority : Moderate priority
  Focus    : Protect match readiness
  Action   : Stay active, complete normal training, and keep bonuses ready before the weekend.
  Why      : Your matches carry extra weight for the Association, so steady readiness is especially important.

6. Manager user_289677
  Priority : High priority
  Focus    : Maximize bonuses now; strengthen starting 11 over time
  Action   : Complete training before the weekend and keep bonuses high. Longer term, upgrade your starting 11.
  Why      : Your matches carry extra weight for the Association, so strong training and steady progress here are especially important.

--------------------------------------------------------------------------------------------

CLAN clan_43560 — MANAGER ADVICE
============================================================================================

1. Manager user_241110
  Priority : Moderate priority
  Focus    : Raise training bonuses
  Action   : Complete training before the weekend and keep bonuses high before matches.
  Why      : Strong training gives the Association a better foundation going into the matchup.

2. Manager user_146867
  Priority : High priority
  Focus    : Maximize bonuses now; strengthen starting 11 over time
  Action   : Complete training before the weekend and keep bonuses high. Longer term, upgrade your starting 11.
  Why      : Your matches carry extra weight for the Association, so strong training and steady progress here are especially important.

3. Manager user_275817
  Priority : High priority
  Focus    : Strengthen your starting 11 over time
  Action   : Keep your team ready this weekend. Longer term, make upgrades to your starting 11.
  Why      : Your matches carry extra weight for the Association, so long-term squad strength matters more in this slot.

4. Manager user_221196
  Priority : High priority
  Focus    : Strengthen your starting 11 over time
  Action   : Keep your team ready this weekend. Longer term, make upgrades to your starting 11.
  Why      : Your matches carry extra weight for the Association, so long-term squad strength matters more in this slot.

5. Manager user_191370
  Priority : High priority
  Focus    : Maximize training bonuses
  Action   : Complete training before the weekend and keep bonuses high before matches.
  Why      : Your matches carry extra weight for the Association, so strong training here is especially important.

6. Manager user_286145
  Priority : High priority
  Focus    : Maximize training bonuses
  Action   : Complete training before the weekend and keep bonuses high before matches.
  Why      : Your matches carry extra weight for the Association, so strong training here is especially important.
  ```