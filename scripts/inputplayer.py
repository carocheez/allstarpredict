from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.static import players
from rapidfuzz import process
# import openai

def get_best_match(player_name):
    all_players = [player['full_name'] for player in players.get_players()]

    match, sim_score, _ = process.extractOne(player_name, all_players)

    if sim_score >= 50:
        return match
    return None

def get_player_id(player_name):
    player = [p for p in players.get_players() if p['full_name'].lower() == player_name.lower()]
    if not player:
        return None
    return player[0]['id']

def main():
    print(f"See any player's career stats!")
    player_name = input("Enter the player's full name (e.g. Stephen Curry): ")

    best_match = get_best_match(player_name)

    if not best_match:
        print(f"No close match found for '{player_name}'. Please try again.")
        return
    
    print(f"Did you mean: {best_match}?")
    confirm = input("Type 'yes' to confirm or 'no' to exit: ").strip().lower()
    if confirm != 'yes':
        print("Exiting. Please run the script again.")
        return
    
    player_id = get_player_id(best_match)

    if player_id is None:
        print(f"Player '{player_name}' not found. Please try again.")
        return
    
    # Fetch the player's career stats
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_df = career.get_data_frames()[0]  # Get the stats as a DataFrame
    
    # Display the career stats
    print(f"\nCareer stats for {best_match}:")

    columns_to_display = ["SEASON_ID", "TEAM_ABBREVIATION", "GP", "GS", "PTS", "AST", "REB", "AST", "STL", "BLK", "TOV", "PF", "PTS"]
    
    print(f"\nStats for {best_match.title()}:\n")
    print(career_df[columns_to_display].to_string(index=False))
    # print(career_df)


if __name__ == "__main__":
    main()
     