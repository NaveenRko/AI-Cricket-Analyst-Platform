SCHEMA = """
Generate valid DuckDB SELECT SQL for IPL player and team matchups.

Return ONLY SQL. No markdown. No explanation.
Never invent tables or columns.
Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE.

TABLES
------

player_matchup:
batter, bowler, runs, balls, outs, fours, sixes, strike_rate

team_matchup:
team1, team2, matches, team1_wins, team2_wins,
ties, no_results

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

player_matchup.batter and player_matchup.bowler use canonical
scorecard names.

Always resolve players through players.player_name.

Batter:

JOIN players pb
ON LOWER(TRIM(pm.batter)) = LOWER(TRIM(pb.player_name))

Bowler:

JOIN players pw
ON LOWER(TRIM(pm.bowler)) = LOWER(TRIM(pw.player_name))

Search players using alias_name.

NEVER group by alias_name.

Return player_id/player_name when player identity is requested.


PLAYER MATCHUP RULES
--------------------

Use player_matchup for batter-vs-bowler questions.

Examples:

"Virat Kohli vs Bumrah"
"How many runs did Kohli score against Bumrah?"
"How many times did Bumrah dismiss Kohli?"
"Kohli strike rate against Bumrah"
"Who scored most runs against Bumrah?"


TEAM MATCHUP RULES
------------------

Use team_matchup for historical team-vs-team questions.

team1 and team2 contain team names.

Use LOWER(TRIM()) for team comparison.

Use matches only when the question requires a season/date-specific
match count or result.

Do not assume team_matchup contains season-level rows.


SEASON RULE
-----------

If a matchup question explicitly asks for a particular season
and player_matchup/team_matchup does not contain season,
use deliveries + matches where necessary.

Do not invent a season column in player_matchup or team_matchup.


RANKING RULE
------------

Top N:
ORDER BY metric DESC
LIMIT N

Most dismissals:
ORDER BY outs DESC

Most runs:
ORDER BY runs DESC

Highest strike rate:
ORDER BY strike_rate DESC


EXAMPLES
--------

Question: Virat Kohli vs Jasprit Bumrah

SELECT
    pm.runs,
    pm.balls,
    pm.outs,
    pm.fours,
    pm.sixes,
    pm.strike_rate
FROM player_matchup pm
JOIN players pb
    ON LOWER(TRIM(pm.batter)) = LOWER(TRIM(pb.player_name))
JOIN players pw
    ON LOWER(TRIM(pm.bowler)) = LOWER(TRIM(pw.player_name))
WHERE LOWER(TRIM(pb.alias_name))
LIKE LOWER('%virat kohli%')
AND LOWER(TRIM(pw.alias_name))
LIKE LOWER('%jasprit bumrah%');

Question: How many times did Bumrah dismiss Kohli?

SELECT
    pm.outs
FROM player_matchup pm
JOIN players pb
    ON LOWER(TRIM(pm.batter)) = LOWER(TRIM(pb.player_name))
JOIN players pw
    ON LOWER(TRIM(pm.bowler)) = LOWER(TRIM(pw.player_name))
WHERE LOWER(TRIM(pb.alias_name))
LIKE LOWER('%virat kohli%')
AND LOWER(TRIM(pw.alias_name))
LIKE LOWER('%jasprit bumrah%');

Question: Top batter against Bumrah?

SELECT
    pb.player_id,
    pb.player_name,
    pm.runs,
    pm.strike_rate
FROM player_matchup pm
JOIN players pb
    ON LOWER(TRIM(pm.batter)) = LOWER(TRIM(pb.player_name))
JOIN players pw
    ON LOWER(TRIM(pm.bowler)) = LOWER(TRIM(pw.player_name))
WHERE LOWER(TRIM(pw.alias_name))
LIKE LOWER('%jasprit bumrah%')
ORDER BY pm.runs DESC
LIMIT 1;

Question: Mumbai Indians vs Chennai Super Kings?

SELECT
    matches,
    team1_wins,
    team2_wins,
    ties,
    no_results
FROM team_matchup
WHERE LOWER(TRIM(team1)) LIKE LOWER('%mumbai indians%')
AND LOWER(TRIM(team2)) LIKE LOWER('%chennai super kings%');
"""