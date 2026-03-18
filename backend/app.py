from flask import Flask, jsonify, request
from flask_cors import CORS
from google import genai
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog, playercareerstats
from rapidfuzz import process, fuzz
import pandas as pd
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    gemini_client = None


# ── Player helpers ──────────────────────────────────────────────────────────

def get_best_match(player_name):
    all_players = players.get_players()
    names = [p["full_name"] for p in all_players]
    result = process.extractOne(player_name, names, scorer=fuzz.WRatio)
    if result and result[1] >= 50:
        return result[0]
    return None


def get_player_id(full_name):
    for p in players.get_players():
        if p["full_name"].lower() == full_name.lower():
            return p["id"]
    return None


# ── Gemini query parser ─────────────────────────────────────────────────────

PARSE_PROMPT = """Parse this NBA query and return ONLY valid JSON — no markdown, no code fences.

Query: "{query}"

JSON structure:
{{
  "intent": "game_log_filter" | "career_stats" | "prediction",
  "player_name": "<full name or null>",
  "stat_column": "PTS" | "AST" | "REB" | "STL" | "BLK" | null,
  "threshold": <number or null>,
  "comparison": "gte" | "lte" | "eq" | null,
  "season": "<YYYY-YY or null>",
  "all_seasons": <true | false>,
  "game_date": "<YYYY-MM-DD or null>",
  "prediction_type": "all_star" | "general" | null
}}

Rules:
- "50 point games"              → intent=game_log_filter, stat_column=PTS, threshold=50, comparison=gte, all_seasons=true
- "triple doubles"              → intent=game_log_filter, stat_column=null, threshold=null, all_seasons=true
- "stats on december 4, 2023"  → intent=game_log_filter, game_date="2023-12-04", all_seasons=false, season="2023-24"
- "career stats"                → intent=career_stats
- "predict all-star"            → intent=prediction, prediction_type=all_star
- Any query about a player on a specific date → intent=game_log_filter (NOT "player_stats")
- If a specific date is mentioned, always set game_date and derive the correct season (YYYY-YY)
- No season or date mentioned  → all_seasons=true for game_log_filter, else false
"""


def parse_query(query: str) -> dict:
    if not gemini_client:
        raise RuntimeError("GEMINI_API_KEY is not set")
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash", contents=PARSE_PROMPT.format(query=query)
    )
    text = response.text.strip()
    if "```" in text:
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


# ── NBA data fetchers ───────────────────────────────────────────────────────

def get_career_seasons(player_id):
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    return career.get_data_frames()[0]["SEASON_ID"].tolist()


def fetch_game_logs(player_id, seasons: list) -> pd.DataFrame:
    frames = []
    for season in seasons:
        try:
            gl = playergamelog.PlayerGameLog(player_id=player_id, season=season)
            frames.append(gl.get_data_frames()[0])
            time.sleep(0.6)  # respect rate limit
        except Exception:
            pass
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def is_triple_double(row):
    cats = [row.get("PTS", 0), row.get("REB", 0), row.get("AST", 0),
            row.get("STL", 0), row.get("BLK", 0)]
    return sum(1 for c in cats if c >= 10) >= 3


# ── API endpoint ────────────────────────────────────────────────────────────

GAME_LOG_COLS = ["GAME_DATE", "MATCHUP", "WL", "MIN", "PTS", "AST", "REB",
                 "STL", "BLK", "FG3M", "FG3A", "FG_PCT", "FG3_PCT", "FT_PCT"]
CAREER_COLS   = ["SEASON_ID", "TEAM_ABBREVIATION", "GP", "GS", "MIN",
                 "PTS", "REB", "AST", "STL", "BLK", "TOV",
                 "FG_PCT", "FG3_PCT", "FT_PCT"]


@app.route("/api/query", methods=["POST"])
def handle_query():
    body = request.get_json(force=True)
    query = (body.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Empty query"}), 400

    try:
        parsed = parse_query(query)
    except Exception as e:
        return jsonify({"error": f"Query parsing failed: {e}"}), 500

    # ── Resolve player ──
    player_name = parsed.get("player_name")
    matched_name = player_id = None
    if player_name:
        matched_name = get_best_match(player_name)
        if not matched_name:
            return jsonify({"error": f"Player not found: {player_name}"}), 404
        player_id = get_player_id(matched_name)

    intent = parsed.get("intent")
    # Normalize any date-specific intent Gemini might return
    if intent == "player_stats":
        intent = "game_log_filter"

    try:
        # ── Game log filter ──
        if intent == "game_log_filter":
            if not player_id:
                return jsonify({"error": "Player name required"}), 400

            seasons = (get_career_seasons(player_id)
                       if parsed.get("all_seasons")
                       else [parsed.get("season") or "2024-25"])

            df = fetch_game_logs(player_id, seasons)
            if df.empty:
                return jsonify({"intent": intent, "player": matched_name,
                                "results": [], "count": 0,
                                "message": "No game data found for that season."})

            stat_col  = parsed.get("stat_column")
            threshold = parsed.get("threshold")
            comparison = parsed.get("comparison", "gte")

            if stat_col and threshold is not None:
                ops = {"gte": "__ge__", "lte": "__le__", "eq": "__eq__"}
                df = df[getattr(df[stat_col], ops[comparison])(threshold)]
            elif not stat_col and not threshold:
                # triple-double fallback
                if "triple double" in query.lower() or "triple-double" in query.lower():
                    mask = df.apply(is_triple_double, axis=1)
                    df = df[mask]

            # Filter by specific game date if provided
            game_date = parsed.get("game_date")
            if game_date:
                from datetime import datetime
                target = datetime.strptime(game_date, "%Y-%m-%d")
                target_str = target.strftime("%b %d, %Y")
                df = df[df["GAME_DATE"] == target_str]

            avail = [c for c in GAME_LOG_COLS if c in df.columns]
            df = df[avail].sort_values("GAME_DATE", ascending=False)

            response_data = {
                "intent": intent,
                "player": matched_name,
                "results": df.to_dict("records"),
                "count": len(df),
            }
            if game_date and len(df) == 0:
                response_data["message"] = f"No game found on {game_date}. {matched_name} may not have played that day."
            return jsonify(response_data)

        # ── Career stats ──
        elif intent == "career_stats":
            if not player_id:
                return jsonify({"error": "Player name required"}), 400

            career = playercareerstats.PlayerCareerStats(player_id=player_id)
            df = career.get_data_frames()[0]
            avail = [c for c in CAREER_COLS if c in df.columns]
            return jsonify({
                "intent": intent,
                "player": matched_name,
                "results": df[avail].to_dict("records"),
            })

        # ── Prediction ──
        elif intent == "prediction":
            if not player_id:
                return jsonify({"error": "Player name required"}), 400

            career = playercareerstats.PlayerCareerStats(player_id=player_id)
            df = career.get_data_frames()[0]
            stats_text = df[["SEASON_ID", "GP", "PTS", "AST", "REB",
                              "STL", "BLK", "FG_PCT"]].to_string(index=False)

            prompt = f"""You are an expert NBA analyst.

{matched_name}'s career statistics:
{stats_text}

Question: {query}

Provide:
1. Trajectory analysis based on season-over-season growth
2. Comparison to players who reached similar milestones
3. Your specific prediction with a timeline
4. Key factors that could speed up or slow down the prediction"""

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            return jsonify({
                "intent": intent,
                "player": matched_name,
                "analysis": response.text,
            })

        else:
            return jsonify({"error": f"Unrecognized intent: {intent}"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
