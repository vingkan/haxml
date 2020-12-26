"""
Logic and utilities for HaxClass analytics.
"""


"""
Constants
"""
TEAMS = {
    1: "red",
    2: "blue",
    "1": "red",
    "2": "blue",
    "red": 1,
    "blue": 2
}
SHOT_TYPES = {
    "save": True,
    "error": True,
    "goal": True    
}


"""
Inflates packed match data from the database.
Args:
    packed: The packed match, as a dict.
Returns:
    The inflated match, as a dict, with all the fields in the data schema. 
"""
def inflate(packed):
    player_map = {}
    for player in packed["players"]:
        player_map[player["id"]] = player
    players = []
    for p in packed["players"]:
        players.append({
            "id": p["id"],
            "name": p["name"],
            "team": TEAMS[p["team"]]
        })
    goals = []
    for line in packed["goals"]:
        data = line.split(",")
        scorer_id = int(data[6])
        scorer = player_map[scorer_id]
        assist_id = int(data[9]) if len(data) > 9 else None
        assist = player_map[assist_id] if assist_id in player_map else None
        goals.append({
            "time": float(data[0]),
            "team": TEAMS[data[1]],
            "scoreRed": int(data[2]),
            "scoreBlue": int(data[3]),
            "ballX": float(data[4]),
            "ballY": float(data[5]),
            "scorerId": scorer_id,
            "scorerX": float(data[7]),
            "scorerY": float(data[8]),
            "scorerName": scorer["name"],
            "scorerTeam": TEAMS[scorer["team"]],
            "assistId": assist_id,
            "assistX": float(data[10]) if len(data) > 10 else None,
            "assistY": float(data[11]) if len(data) > 11 else None,
            "assistName": assist["name"] if assist else None,
            "assistTeam": TEAMS[assist["team"]] if assist else None
        })
    kicks = []
    for line in packed["kicks"]:
        data = line.split(",")
        from_id = int(data[2])
        from_player = player_map[from_id]
        to_id = int(data[5]) if len(data) > 5 else None
        to_player = player_map[to_id] if to_id in player_map else None
        kicks.append({
            "time": float(data[0]),
            "type": data[1],
            "fromId": from_id,
            "fromX": float(data[3]),
            "fromY": float(data[4]),
            "fromName": from_player["name"],
            "fromTeam": TEAMS[from_player["team"]],
            "toId": to_id,
            "toX": float(data[6]) if len(data) > 6 else None,
            "toY": float(data[7]) if len(data) > 7 else None,
            "toName": to_player["name"] if to_player else None,
            "toTeam": TEAMS[to_player["team"]] if to_player else None
        })
    possessions = []
    for line in packed["possessions"]:
        data = line.split(",")
        player_id = int(data[2])
        player = player_map[player_id]
        possessions.append({
            "start": float(data[0]),
            "end": float(data[1]),
            "playerId": player_id,
            "playerName": player["name"],
            "team": TEAMS[player["team"]]
        })
    positions = []
    for line in packed["positions"]:
        data = line.split(",")
        is_player = len(data) == 4
        player_id = int(data[3]) if is_player else None
        player = player_map[player_id] if player_id in player_map else None
        positions.append({
            "type": "player" if is_player else "ball",
            "time": float(data[0]),
            "x": float(data[1]),
            "y": float(data[2]),
            "playerId": player_id,
            "name": player["name"] if player else None,
            "team": TEAMS[player["team"]] if player else None
        })
    return {
        "saved": packed["saved"],
        "score": packed["score"],
        "stadium": packed["stadium"],
        "players": players,
        "goals": goals,
        "kicks": kicks,
        "possessions": possessions,
        "positions": positions
    }


"""
Checks whether the given kick is a shot on goal. Goals, saves, and errors (when
a shot deflects off of the defender and results in an own goal) count as shots.
Args:
    kick: The kick data, as a dict.
Returns:
    True if the kick is considered a shot on goal, False otherwise.
"""
def is_shot(kick):
    return kick["type"] in SHOT_TYPES
