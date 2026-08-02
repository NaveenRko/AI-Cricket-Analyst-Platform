SCHEMA = """
Generate valid DuckDB SELECT SQL for IPL bowling analytics.

Return ONLY SQL. No markdown. No explanation.
Never invent tables or columns.
Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE.

TABLES
------

bowling_stats:
bowler, matches_played, wickets, overs, runs_conceded, economy

bowler_season_stats:
season, bowler, matches, runs_conceded, wickets,
overs, economy, strike_rate

bowler_match_stats:
match_id, bowler, wickets, runs_conceded, overs, economy

phase_bowling:
bowler, phase, wickets, runs_conceded, balls, economy

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

Statistics tables store canonical scorecard names.

players.player_name = canonical scorecard name.
players.player_id = unique player identity.
players.alias_name = searchable aliases.

Always join:

JOIN players p
ON LOWER(TRIM(stat.bowler)) = LOWER(TRIM(p.player_name))

Use alias_name ONLY for searching:

WHERE LOWER(TRIM(p.alias_name))
LIKE LOWER('%jasprit bumrah%')

NEVER GROUP BY alias_name.

For player rankings use:

GROUP BY p.player_id, p.player_name

Return canonical player identity, not aliases.


TABLE GRAIN
----------

bowler_season_stats = one row per bowler per season.
bowler_match_stats = one row per bowler per match.
phase_bowling = one row per bowler per phase.
bowling_stats = aggregate bowling statistics.
matches = one row per match.

Never join different grains unless required.
Never create joins that multiply rows before aggregation.


TABLE SELECTION
---------------

Season bowling → bowler_season_stats.

Career bowling aggregation → bowler_season_stats.

Match bowling → bowler_match_stats.

Phase bowling → phase_bowling.

Use matches only when date, venue, city, winner, toss or POTM
information is required.


AGGREGATION RULES
-----------------

Single-season bowling statistics are already aggregated.

"Jasprit Bumrah wickets in IPL 2024"
→ bs.wickets

"Top 5 wicket takers in IPL 2024"
→ bs.wickets

DO NOT SUM season values for a single season.

Career wickets across seasons:

SUM(bs.wickets)

GROUP BY p.player_id, p.player_name

Do not join bowler_season_stats with bowler_match_stats
before aggregation.


RANKING RULE
------------

Most wickets:
ORDER BY wickets DESC

Best economy:
ORDER BY economy ASC

Best bowling strike rate:
ORDER BY strike_rate ASC

Explicit Top N:
LIMIT N

Ranking without N:
LIMIT 10


EXAMPLES
--------

Question: Most wickets in IPL 2024?

SELECT
    p.player_id,
    p.player_name,
    bs.wickets
FROM bowler_season_stats bs
JOIN players p
    ON LOWER(TRIM(bs.bowler)) = LOWER(TRIM(p.player_name))
WHERE bs.season = 2024
ORDER BY bs.wickets DESC
LIMIT 1;

Question: Top 5 wicket takers in IPL 2024?

SELECT
    p.player_id,
    p.player_name,
    bs.wickets
FROM bowler_season_stats bs
JOIN players p
    ON LOWER(TRIM(bs.bowler)) = LOWER(TRIM(p.player_name))
WHERE bs.season = 2024
ORDER BY bs.wickets DESC
LIMIT 5;

Question: Bumrah wickets in IPL 2024?

SELECT
    p.player_id,
    p.player_name,
    bs.wickets
FROM bowler_season_stats bs
JOIN players p
    ON LOWER(TRIM(bs.bowler)) = LOWER(TRIM(p.player_name))
WHERE LOWER(TRIM(p.alias_name))
LIKE LOWER('%jasprit bumrah%')
AND bs.season = 2024;

Question: Best economy in IPL 2024?

SELECT
    p.player_id,
    p.player_name,
    bs.economy
FROM bowler_season_stats bs
JOIN players p
    ON LOWER(TRIM(bs.bowler)) = LOWER(TRIM(p.player_name))
WHERE bs.season = 2024
ORDER BY bs.economy ASC
LIMIT 1;
"""