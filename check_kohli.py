import duckdb

DATABASE = "database/ipl.duckdb"

conn = duckdb.connect(DATABASE)

query = """
SELECT
    p.player_id,
    p.player_name,
    COUNT(*) AS joined_rows,
    SUM(ps.runs) AS total_runs
FROM player_season_stats ps
JOIN (
    SELECT DISTINCT
        player_id,
        player_name
    FROM players
) p
    ON LOWER(TRIM(ps.batter))
       = LOWER(TRIM(p.player_name))
WHERE p.player_id = 767
GROUP BY
    p.player_id,
    p.player_name;
"""

df = conn.execute(query).fetchdf()

print(df.to_string(index=False))

conn.close()