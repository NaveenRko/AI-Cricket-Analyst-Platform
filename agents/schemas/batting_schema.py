BATTING_SQL_SCHEMA = """
Generate valid DuckDB SELECT SQL for IPL batting analytics.

Return ONLY SQL. No markdown. No explanation.
Never invent tables or columns.
Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE.

TABLES
------

batting_stats:
batter, matches_played, runs, balls, dismissals,
fours, sixes, strike_rate, average

player_season_stats:
season, batter, matches, runs, balls, dismissals,
fifties, hundreds, fours, sixes, strike_rate, average

player_match_stats:
match_id, batter, runs, balls, fours, sixes, strike_rate

phase_batting:
batter, phase, runs, balls, strike_rate

player_milestones:
batter, fifties, hundreds, ducks, player_of_match_awards

players:
player_name, player_id, alias_name

matches:
match_id, season, date, venue, city, winner,
toss_winner, toss_decision, player_of_match

deliveries:
match_id, innings, over, ball, batter, bowler,
batsman_runs, extra_runs, total_runs, is_wicket,
player_dismissed, dismissal_kind, fielder, is_powerplay


PLAYER IDENTITY
---------------

Statistics tables store canonical scorecard names such as
"V Kohli", "RG Sharma", "MS Dhoni".

players.player_name = canonical scorecard name.
players.player_id = unique player identity.
players.alias_name = searchable aliases.

Always join:

JOIN players p
ON LOWER(TRIM(stat.batter)) = LOWER(TRIM(p.player_name))

Use alias_name ONLY for player-name filtering:

WHERE LOWER(TRIM(p.alias_name))
LIKE LOWER('%virat kohli%')

NEVER GROUP BY alias_name.
For player rankings/aggregation use:

GROUP BY p.player_id, p.player_name

Return p.player_id and p.player_name when a player is requested.


TABLE GRAIN
----------

player_season_stats = one row per player per season.
player_match_stats = one row per player per match.
phase_batting = one row per player per phase.
batting_stats = aggregate batting statistics.
player_milestones = player milestone statistics.
matches = one row per match.

Never join tables with different grains unless required.
Never create joins that multiply rows before aggregation.


TABLE SELECTION
---------------

Specific season/player statistics → player_season_stats.

Career totals across seasons → player_season_stats.

Match-specific batting → player_match_stats.

Phase batting → phase_batting.

Fifties/hundreds/ducks/POTM awards → player_milestones.

Use matches only when date, venue, city, winner, toss or POTM
information is required.


AGGREGATION RULES
-----------------

Single-season statistics are already aggregated.

"Virat Kohli runs in IPL 2024"
→ ps.runs

"Top 5 run scorers in IPL 2024"
→ ps.runs

DO NOT SUM ps.runs for a single season.

Career totals across seasons require:

SUM(ps.runs)

GROUP BY p.player_id, p.player_name

Do NOT use SUM(bs.runs) for career rankings.

Never join player_season_stats with player_match_stats
before aggregating.


RANKING RULE
------------

Explicit Top N:
ORDER BY metric DESC
LIMIT N

Ranking without N:
LIMIT 10

For highest/best:
ORDER BY metric DESC LIMIT 1

For lowest/best economy:
ORDER BY metric ASC LIMIT 1.


EXAMPLES
--------

Question: Who has accumulated the most IPL runs?

SELECT
    p.player_id,
    p.player_name,
    SUM(ps.runs) AS total_runs
FROM player_season_stats ps
JOIN players p
    ON LOWER(TRIM(ps.batter)) = LOWER(TRIM(p.player_name))
GROUP BY p.player_id, p.player_name
ORDER BY total_runs DESC
LIMIT 1;

Question: Top 5 run scorers in IPL 2024?

SELECT
    p.player_id,
    p.player_name,
    ps.runs AS total_runs
FROM player_season_stats ps
JOIN players p
    ON LOWER(TRIM(ps.batter)) = LOWER(TRIM(p.player_name))
WHERE ps.season = 2024
ORDER BY ps.runs DESC
LIMIT 5;

Question: Virat Kohli runs in IPL 2024?

SELECT
    p.player_id,
    p.player_name,
    ps.runs
FROM player_season_stats ps
JOIN players p
    ON LOWER(TRIM(ps.batter)) = LOWER(TRIM(p.player_name))
WHERE LOWER(TRIM(p.alias_name))
LIKE LOWER('%virat kohli%')
AND ps.season = 2024;

Question: Highest strike rate in IPL 2024?

SELECT
    p.player_id,
    p.player_name,
    ps.strike_rate
FROM player_season_stats ps
JOIN players p
    ON LOWER(TRIM(ps.batter)) = LOWER(TRIM(p.player_name))
WHERE ps.season = 2024
ORDER BY ps.strike_rate DESC
LIMIT 1;
"""