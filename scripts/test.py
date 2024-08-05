from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import players 
import pandas as pd

all_players = players.get_players()

df_players = pd.DataFrame(all_players)

# print(df_players.head())

player_name = "Stephen Curry"
player = players.find_players_by_full_name(player_name)
player_id = 0

if player:
    player_id = player[0]['id']
    print(f"Player ID of {player_name} is {player[0]['id']}")
else:
    print(f"Player {player_name} not found.")

career = playercareerstats.PlayerCareerStats(player_id)

df = career.get_data_frames()[0]

print(df.head())

career.get_json()

career.get_dict()

