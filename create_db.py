import duckdb
import pandas as pd

conn = duckdb.connect("database/ipl.duckdb")

tables = {
    "matches": "data/matches.csv",
    "deliveries": "data/deliveries.csv",
    "players": "data/players.csv",

    "batting_stats": "data/batting_stats.csv",
    "bowling_stats": "data/bowling_stats.csv",

    "team_match_stats": "data/team_match_stats.csv",
    "team_season_stats": "data/team_season_stats.csv",

    "player_match_stats": "data/player_match_stats.csv",
    "player_season_stats": "data/player_season_stats.csv",

    "phase_batting": "data/phase_batting.csv",
    "phase_bowling": "data/phase_bowling.csv",

    "player_vs_player": "data/player_vs_player.csv",

    "venue_stats": "data/venue_stats.csv",
    "bowler_match_stats": "data/bowler_match_stats.csv",
    "bowler_season_stats": "data/bowler_season_stats.csv",
    "player_milestones": "data/player_milestones.csv",
    "venue_match_stats": "data/venue_match_stats.csv"
}

for table_name, file_path in tables.items():

    df = pd.read_csv(file_path)

    conn.register("temp_df", df)

    conn.execute(f"""
        CREATE OR REPLACE TABLE {table_name}
        AS SELECT * FROM temp_df
    """)

print("\nTables Created:\n")

for t in conn.execute("SHOW TABLES").fetchall():
    print(t[0])

conn.close()

if __name__ == "__main__":
    create_database()