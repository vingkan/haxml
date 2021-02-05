"""
Logic and utilities for HaxML analytics.
"""

import json
import math
from tqdm import tqdm


"""
Constants
"""
ZERO = 1e-10
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
SCORED_TYPES = {
    "goal": True,
    "error": True
}
ALLOWED_TYPES = {
    "goal": True,
    "own_goal": True
}
TARGET_STADIUMS = {
    "NAFL Official Map v1": True,
    "Futsal 3x3 4x4 from HaxMaps": True,
    "Futsalx3 | TK&ED": True,
    "Futsal x3 by Bazinga from HaxMaps": True,
    "FUTHAX 4v4": True,
    "Happy Futsal 3x3 4x4": True,
    "Happy Futsal 3x3 4x4": True
}


def is_shot(kick):
    """
    Checks whether the given kick is a shot on goal. Goals, saves, and errors (when
    a shot deflects off of the defender and results in an own goal) count as shots.
    Args:
        kick: The kick data, as a dict.
    Returns:
        True if the kick is considered a shot on goal, False otherwise.
    """
    return kick["type"] in SHOT_TYPES


def is_scored_goal(kick):
    """
    Checks whether the given kick is a scored goal, the binary target for
    expected goals on offense. Scored goals must be either goals or errors.
    Errors are counted as scored goals to avoid counting own goals that did not
    originate from an attacking player.
    Args:
        kick: The kick data, as a dict.
    Returns:
        True if the kick is considered a scored goal, False otherwise.
    """
    return kick["type"] in SCORED_TYPES


def is_allowed_goal(kick):
    """
    Checks whether the given kick is an allowed goal, a measure on defense.
    Allowed goals must be either goals or own goals. Own goals are a superset of
    errors, so we do not include errors in the count.
    Args:
        kick: The kick data, as a dict.
    Returns:
        True if the kick is considered an allowed goal, False otherwise.
    """
    return kick["type"] in ALLOWED_TYPES


def is_target_stadium(stadium):
    """
    Checks whether the given stadium is a target stadium.
    Args:
        stadium: Name of the stadium (string).
    Returns:
        True if the stadium is considered a target stadium, False otherwise.
    """
    return stadium in TARGET_STADIUMS


def to_clock(time_secs):
    """
    Converts match time in seconds to a clock time in the format: m:ss.
    Args:
        time_secs: Number of seconds (float).
    Returns:
        Clock time in format: m:ss (str).
    """
    mins = math.floor(time_secs / 60)
    secs = str(math.floor(time_secs) % 60)
    secs_left_pad = "0{}".format(secs) if len(secs) == 1 else secs
    time_clock = "{}:{}".format(mins, secs_left_pad)
    return time_clock


def inflate_match(packed):
    """
    Inflates packed match data from the database.
    Args:
        packed: The packed match, as a dict.
    Returns:
        The inflated match, as a dict, with all the fields in the data schema.
    """
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


def load_match(infile, callback=None):
    """
    Loads packed match data from the given file and then runs a callback on it.
    If no callback, returns inflated match data.
    Args:
        infile: Filename where packed match data is stored (string).
        callback: Method to call on inflated match data (method).
    Returns:
        Return value of callback, if any.
    """
    with open(infile, "r") as file:
        packed = json.load(file)
        match = inflate_match(packed)
    if callback:
        return callback(match)
    return match


def get_stadiums(infile):
    """
    Reads a dict of stadium data from a filename.
    Args:
        infile: Filename where stadium map data is stored (string).
    Returns:
        Dict of stadium names (strings) to stadium map data records (dicts).
    """
    stadium_dict = {}
    with open(infile, "r") as file:
        stadiums = json.load(file)
        for stadium in stadiums:
            stadium_dict[stadium["stadium"]] = stadium
    return stadium_dict


def get_opposing_goalpost(stadium, team):
    """
    Returns goalpost that a player of the given team should try to score in.
    Args:
        stadium: Stadium data (dict).
        team: Team of player trying to score ("red" or "blue")
    Returns:
        Dict of goalpost data.
    """
    if "goalposts" not in stadium:
        raise ValueError("No goalposts for the given stadium.")
    if team not in ["red", "blue"]:
        raise ValueError(f"Invalid team: {team}")
    # 1 is for red, 2 is for blue, so we switch them to get the opposing goal.
    opposing_goalpost_id = "1" if team == "blue" else "2"
    return stadium["goalposts"][opposing_goalpost_id]


def get_matches_metadata(infile):
    """
    Reads match IDs and metadata from a filename.
    Args:
        infile: Filename where match IDs and metadata are stored (string).
    Returns:
        List of dicts with IDs and metadata for each match.
    """
    out = []
    with open(infile, "r") as file:
        lines = file.read().split("\n")
        # First two lines are column names and types.
        header = lines[0].split(",")
        types = lines[1].split(",")
        for line in filter(lambda x: len(x) > 0, lines[2:]):
            data = line.split(",")
            row = {}
            for i in range(len(data)):
                if types[i] == "int":
                    row[header[i]] = int(data[i])
                elif types[i] == "float":
                    row[header[i]] = float(data[i])
                elif types[i] == "str":
                    row[header[i]] = data[i]
                else:
                    err = "Unsupported column type: {}".format(types[i])
                    raise ValueError(err)
            out.append(row)
    return out


def train_test_split_matches_even_count(metadata):
    """
    Evenly splits matches into train and test lists of almost the same size.
    Matches are sorted by number of scored goals, in an attempt to evenly
    distribute scored goals between the two lists.
    Args:
        metadata: List of dicts with IDs and metadata for each match, to split
            into train and test lists.
    Returns:
        (train, test): Tuple containing match IDs for train and test splits
            (lists of strings).
    """
    train = []
    test = []
    meta_sorted = sorted(metadata, key=total_scored_goals)
    for i, record in enumerate(meta_sorted):
        is_train = i % 2 == 0
        if is_train:
            train.append(record)
        else:
            test.append(record)
    return train, test


def total_scored_goals(meta):
    """
    Adds up the total number of scored goals from the match metadata.
    Note: Own goals are not scored goals, only goals and errors.
    Args:
        meta: Match metadata (dict).
    Returns:
        Number of scored goals by both teams (int).
    """
    return meta["scored_goals_red"] + meta["scored_goals_blue"]


def total_kicks(meta):
    """
    Adds up the total number of kicks from the match metadata.
    Args:
        meta: Match metadata (dict).
    Returns:
        Number of kicks (int).
    """
    return meta["kicks_red"] + meta["kicks_blue"]


def goal_fraction(goals, kicks):
    """
    Calculate the fraction of goals out of kicks.
    Note: The parameter goals can be any kind of goals. When calculating
    for offense, use scored goals, (goals and errors, but no own goals). When
    calculating for defense, use allowed goals (goals and own goals, no errors).
    Args:
        goals: Number of goals in the match (int).
        kicks: Number of kicks in the match (int).
    Returns:
        Fraction goals / kicks (float).
    """
    return float(goals) / (float(kicks) + ZERO)


def stadium_distance(x1, y1, x2, y2):
    """
    Calculates distance between (x1, y1) and (x2, y2) using L2-norm.
    Args:
        x1: X-coordinate of point 1.
        y1: X-coordinate of point 1.
        x2: Y-coordinate of point 2.
        y2: Y-coordinate of point 2.
    Returns:
        Distance between points (float).
    """
    return math.sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))


def angle_from_goal(x, y, gx, gy):
    """
    Computes angle between straight shot and goal line.
    Note: This method naively computes a straight shot from (x, y) to (gx, xy)
    but in HaxBall, it is common for players to bounce the ball off of walls and
    take another trajectory. Any point on the goal line can be used, such as the
    midpoint between the posts.
    Args:
        x: X-coordinate where ball was kicked from.
        y: Y-coordinate where ball was kicked from.
        gx: X-coordinate of point on goal line.
        gy: Y-coordinate of point on goal line.
    Returns:
        Angle between straight shot and goalline in radians,
        e.g., 0 is a straight shot along the goal line,
        Pi/2 is a straight shot perpendicular to the goal line.
    """
    # Use absolute value to restrict angle between [0, Pi/2].
    dx = float(abs(x - gx))
    dy = float(abs(y - gy))
    # Avoid division by zero error.
    angle = math.atan(dx / dy) if dy > 0 else math.pi / 2.0
    return angle


def replace_usernames_all_time_kicks(all_time_kicks, progress=False):
    """
    Replaces usernames with anonymous numbered players in-place.
    Note: Username replacement is only consistent within file, i.e., "Player 4"
    refers to the same player across this all-time kicks response, but may not
    be the same player as "Player 4" in the matches data file, which had its
    usernames replaced separately.
    Args:
        all_time_kicks: All-time kicks response from database (dict).
        progress: Whether or not to show progress bar (boolean).
    Returns:
        All-time kicks response (dict), but with player usernames replaced.
    """
    username_map = {}
    bar = tqdm(all_time_kicks.keys()) if progress else all_time_kicks.keys()
    for key in bar:
        kick = all_time_kicks[key]
        from_name = kick["fromName"] if "fromName" in kick else None
        to_name = kick["toName"] if "toName" in kick else None
        if from_name:
            if from_name not in username_map:
                username_map[from_name] = "Player {}".format(len(username_map))
            kick["fromName"] = username_map[from_name]
        if to_name:
            if to_name not in username_map:
                username_map[to_name] = "Player {}".format(len(username_map))
            kick["toName"] = username_map[to_name]
    return all_time_kicks


def replace_usernames_packed_matches(packed_matches, progress=False):
    """
    Replaces usernames with anonymous numbered players in-place.
    Note: Username replacement is only consistent within file, Refer to the
    docstring of replace_usernames_all_time_kicks for more details.
    Args:
        packed_matches: Packed matches response from database (dict).
        progress: Whether or not to show progress bar (boolean).
    Returns:
        Packed matches response (dict), but with player usernames replaced.
    """
    username_map = {}
    bar = tqdm(packed_matches.keys()) if progress else packed_matches.keys()
    for match_id in bar:
        packed = packed_matches[match_id]
        if packed is None:
            print("None MID: {}".format(match_id))
        for player in packed["players"]:
            name = player["name"]
            if name not in username_map:
                username_map[name] = "Player {}".format(len(username_map))
            player["name"] = username_map[name]
    return packed_matches


def get_positions_at_time(positions, t):
    """
    Return a list of positions (dicts) closest to, but before time t.
    """
    # Assume positions list is already sorted.
    # frame is a list of positions (dicts) that have the same timestamp.
    frame = []
    frame_time = 0.0
    for pos in positions:
        # If we passed the target time t, return the frame we have
        if pos["time"] > t:
            break
        # If this positions is part of the current frame, add it
        if pos["time"] == frame_time:
            frame.append(pos)
        # If current frame is over, make a new frame and add this position to it
        else:
            frame = []
            frame.append(pos)
            frame_time = pos["time"]
    return frame


def get_positions_in_range(positions, start, end):
    """
    Return a list of positions (dicts) between start and end (inclusive).
    """
    assert start <= end, "Time `start` must be before `end`."

    def is_in_time_range(pos):
        return pos["time"] >= start and pos["time"] <= end

    return list(filter(is_in_time_range, positions))


# Edwin feature functions

def defender_feature(match,kick,dist):
    positions = get_positions_at_time(match["positions"], kick["time"])
    closest_defender = float('inf')
    defenders_pressuring = 0
    ret = [0,0]
    for person in positions:
        if person['team'] is not kick['fromTeam'] and person['type'] == "player":
            defender_dist = stadium_distance(kick['fromX'],kick['fromY'],person['x'],person['y'])
            #((kick['fromX'] - person['x'])**2 + (kick['fromY'] - person['y'])**2)**(1/2)
            if defender_dist < closest_defender:
                closest_defender = defender_dist
                ret[0] = closest_defender
            if defender_dist <= dist:
                defenders_pressuring = defenders_pressuring + 1
                ret[1] = defenders_pressuring
    return ret

def is_in_range(person,goal_low,goal_high,fromX,goal_x, kick_team):
    is_x = False
    is_y = False
    if kick_team == "red":
        if(person['x']>=fromX and person['x']<=goal_x):
            is_x = True
    else:
        if(person['x']>=goal_x and person['x']<=fromX):
            is_x = True

    if(person['y']>=goal_low and person['y']<=goal_high):
        is_y = True

    return is_x and is_y

def defender_box(match,stadium,kick):
    count = 0
    gp = get_opposing_goalpost(stadium,kick["fromTeam"])
    gp_y_high = max([p["y"] for p in gp["posts"]])
    gp_y_low = min([p["y"] for p in gp["posts"]])
    goal_x = gp["posts"][0]["x"]
    positions = get_positions_at_time(match["positions"], kick["time"])
    kicker = None
    for person in positions:
        if person["playerId"] == kick["fromId"]:
            kicker = person
            break
    if kicker is None:
        return 0,False
    #print("positions time = ", positions[0]["time"])
    for person in positions:
        if person["type"] == "ball" or person["playerId"] == kicker["playerId"]:
            continue
        if is_in_range(person,gp_y_low,gp_y_high,kicker['x'],goal_x, kicker["team"]):
            count = count + 1
    in_box = True if count>0 else False
    return count, in_box

def is_in_range_tri(person,goal_low,goal_high,fromX,fromY,goal_x, kick_team):
    if(fromY - goal_low != 0 and fromX - goal_x != 0):
        slope_1 = (fromY-goal_low)/(fromX-goal_x)
    else:
        slope_1 = 0
    if(fromY - goal_high != 0 and fromX - goal_x != 0):
        slope_2 = (fromY-goal_high)/(fromX-goal_x)
    else:
        slope_2 = 0

    if(person['x']*slope_1+goal_low <= person['y'] and person['x']*slope_2+goal_high >= person['y']):
        return True
    return False

def defender_cone(match,stadium,kick,offset):
    count = 0
    gp = get_opposing_goalpost(stadium,kick["fromTeam"])
    gp_y_high = max([p["y"] for p in gp["posts"]])
    gp_y_low = min([p["y"] for p in gp["posts"]])
    goal_x = gp["posts"][0]["x"]
    positions = get_positions_at_time(match["positions"], kick["time"]- offset)
    kicker = None
    for person in positions:
        if person["playerId"] == kick["fromId"]:
            kicker = person
            break
    if kicker is None:
        return 0, False
    for person in positions:
        if person["type"] == "ball" or person["playerId"] == kicker["playerId"]:
            continue
        if is_in_range_tri(person,gp_y_low,gp_y_high,kicker['x'],kicker['y'],goal_x, kicker["team"]):
            count = count + 1
    in_cone = True if count>0 else False
    return count, in_cone

def speed_ball(match,kick,offset):
    speed = 0
    if kick["time"]>1:
        position_before = get_positions_at_time(match["positions"], kick["time"] - offset)
        position_after = get_positions_at_time(match["positions"], kick["time"])
    else:
        return 0
    ball_before = list(filter(lambda person: person["type"] == "ball",position_before))[0]
    ball_after = list(filter(lambda person: person["type"] == "ball",position_after))[0]
    distance = stadium_distance(ball_before['x'],ball_before['y'],ball_after['x'],ball_after['y'])
    time = (ball_after['time']-ball_before['time'])
    return distance/time

#Lynn's features

def shot_intersection(match,kick, stadium, frame):
    '''Finds where the ball would intersect
    Args:
    match: Which match it is
    kick: Which kick we want to measure
    staduim: What stadium size it is (so we know where the goals and bounds are)

    Returns:
    Int 1 or 0 if the ball is going towars the goal or not
    '''
    #Getting last frame before the kick 
    #print("Calculate intersection at time: {}".format(kick["time"] - offset))
    #frame = get_positions_at_time(match["positions"], kick["time"] - offset)
    #Using in range and tracing back to see what frame was right before it left the foot
    #A list of lists with only info about player we want and ball
    shooter_frames = []
    ball_frames = []
    #print(kick['fromName'])
    for i in frame:
        if i['name'] == kick['fromName']: 
            shooter_frames.append(i)  
        elif i['type'] == 'ball':
            ball_frames.append(i)
    #print(shooter_frames)
    #print(ball_frames)
    #picking frame with least dist
    least_dist = float('inf')
    player_position = {}
    ball_position = {}
    #List of dicts
    length = min(len(shooter_frames),len(ball_frames))
    set_dist = 30 #ball and player are at least get within 30 units then we assume that it was kicked
    
    for i in range(length-1,-1,-1): #frame len of ball and shooter should be the same
        dist = stadium_distance(shooter_frames[i]['x'],shooter_frames[i]['y'],ball_frames[i]['x'],ball_frames[i]['y'])
        if dist <= set_dist:
            player_position = shooter_frames[i]
            ball_position = ball_frames[i]
            break
    #If a frame isn't found with dist that is <= 30, then use least dist to calculate
    if not (ball_position) or not (player_position): #The dictionaries were not populated yet so default to getting least distance
        for i in range(length-1,-1,-1): #frame len of ball and shooter should be the same
            dist = stadium_distance(shooter_frames[i]['x'],shooter_frames[i]['y'],ball_frames[i]['x'],ball_frames[i]['y'])
            if dist <= least_dist:
                player_position = shooter_frames[i]
                ball_position = ball_frames[i]
                least_dist = dist
            else: #stopped decreasing
                break
    #print(frame)
    #print(player_position)
    #print(ball_position)
    #Getting goal positions
    goal_mid = get_opposing_goalpost(stadium, kick['fromTeam'])['mid']
    #print(goal_mid)
     #Extend line from shot angle (can't extend lines easily)
    if(len(player_position)==0 or len(ball_position)==0):
        return None, None, None
    y_val = point_slope(
        player_position,
        slope(player_position['x'], player_position['y'], ball_position['x'], ball_position['y']),
        goal_mid['x']
    )
    #Checking if the projection between the posts
    intersect = { 'x': goal_mid['x'], 'y': y_val }
    return player_position, ball_position, intersect

def shot_on_goal(match, kick, intersect, stadium):
    '''Figuring out if shot is going into the goal or not
        Args:
            match: Which match it is
            kick: Which kick we want to measure
            intersect: x,y of the shot intersection
            stadium: Which staduim was it played on

        Returns:
                1 if shot is on goal, .5 if it hits the post, and 0 if it isn't on goal
    '''
    goal_posts = get_opposing_goalpost(stadium, kick['fromTeam'])['posts']
    if intersect['y'] > goal_posts[0]['y'] and intersect['y'] < goal_posts[1]['y']:
        return 1
    #elif intersect['y'] == goal_posts[0]['y'] or intersect['y'] == goal_posts[1]['y']:
        #hits posts
        #return .5
    else:
        return 0

def speed_player(match,kick,player_name,positions):
    '''' Speed of the player
       Args:
           match: Which match it is
           kick: Which kick we want to measure
           player_name: What player do we want to measure the speed for

        Returns:
           Int that represents the speed of the player
    '''
    #Getting time range to be able to measure distance
    #start = get_positions_at_time(match["positions"], kick["time"] - offset)
    #end = get_positions_at_time(match["positions"], kick["time"])
    #getting positions
    
    #print(positions)
    player_pos = []
    for i in positions:
        if i['name'] == player_name: 
            player_pos.append(i)    
    #print(player_pos)
    #Getting the time
    if len(player_pos) > 1:
        last = len(player_pos)-1#getting last index)
        time = player_pos[last]['time'] -  player_pos[0]['time'] 
        #Getting the distance 
        distance = stadium_distance(player_pos[0]['x'],player_pos[0]['y'],player_pos[last]['x'],player_pos[last]['y'])
        #dist_formula(player_pos[0]['x'],player_pos[0]['y'],player_pos[last]['x'],player_pos[last]['y'])
        #print("dist:" + str(distance))
        #print("time:" + str(time))
        #Returns speed
        #NEED TO CHANGE TIME INTO SECONDS SO THAT IT IS CONSTANT AND NOT DIVIDING BY DIFF VALS
        return distance/time
    else:
        return 0

def defender_feature_weighted(match,kick,stadium,positions,dist=0):
    '''Figuring out the closest defender and num of defenders for a kick
        Note: This is weighted so that defenders that are close to the player/ball or the goal count as 1.5 rather than 1
        Args:
            match: Which match it is
            kick: Which kick we want to measure
            dist: Set distance to consider a player pressuring

        Returns:
                List that contains the distance of the closest defender and the number of defenders (weighted)
'''
    closest_defender = float('inf')
    defenders_pressuring = 0
    ret = [0,0]
    for person in positions:
        if person['team'] is not kick['fromTeam'] and person['type'] == "player": 
            defender_dist = stadium_distance(kick['fromX'],kick['fromY'],person['x'],person['y'])
            #((kick['fromX'] - person['x'])**2 + (kick['fromY'] - person['y'])**2)**(1/2)
            if defender_dist < closest_defender:
                closest_defender = defender_dist
                ret[0] = closest_defender
            if defender_dist <= dist:
                #Checking distances  for weights
                post = get_opposing_goalpost(stadium, kick['fromTeam'])
                goal_dist = stadium_distance(post['mid']['x'], post['mid']['y'] ,person['x'],person['y'])
                if defender_dist <= 5:
                    defenders_pressuring += 1.5
                elif goal_dist <= 5:
                    defenders_pressuring += 1.5
                else:
                    defenders_pressuring += 1
                ret[1] = defenders_pressuring
    return ret

def in_stadium(stadium):
    recognized_stadiums = ["NAFL Official Map v1","Futsal 3x3 4x4 from HaxMaps", "Futsalx3 | TK&ED", "Futsal x3 by Bazinga from HaxMaps", "FUTHAX 4v4", "Happy Futsal 3x3 4x4","Happy Futsal 3x3 4x4"]
    if stadium in recognized_stadiums:
        return 1
    return 0

#Helper functions
def point_slope(p, slope,x_goal):
    #y - y1 = m(x-x1) -->  y=mx-mx1+y1 (returning the y)
    y_val = (slope*x_goal)-(slope*p['x'])+p['y'] 
    return y_val

def slope(x1, y1, x2, y2):
    m = (y2-y1)/(x2-x1+1e-10)
    return m
