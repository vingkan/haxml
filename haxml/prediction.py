"""
Methods for preparing data and making XG predictions.
"""

import sys
sys.path.append("./")

from haxml.utils import (
    get_opposing_goalpost,
    stadium_distance,
    angle_from_goal,
    is_scored_goal,
    get_positions_at_time,
    get_positions_in_range,
    # Edwin's Model Features
    defender_feature,
    defender_box,
    defender_cone,
    speed_ball,
    #Lynn's Model Features
    shot_intersection,
    shot_on_goal,
    defender_feature_weighted,
    speed_player,
    in_stadium
)
import math
import pandas as pd


def generate_rows_demo(match, stadium):
    """
    Generates target and features for each kick in the match.
    Produces two features for demo classifiers:
        goal_distance: Distance from where  ball was kicked to goal midpoint.
        goal_angle: Angle (in radians) between straight shot from where ball was
            kicked to goal midpoint.
    Args:
        match: Inflated match data (dict).
        stadium: Stadium data (dict).
    Returns:
        Generator of dicts with values for each kick in the given match.
        Includes prediction target "ag" (actual goals) which is 1 for a scored
        goal (goal or error) and 0 otherwise, "index" which is the index of the
        kick in the match kick list, and all the other features needed for
        prediction and explanation.
    """
    for i, kick in enumerate(match["kicks"]):
        gp = get_opposing_goalpost(stadium, kick["fromTeam"])
        x = kick["fromX"]
        y = kick["fromY"]
        gx = gp["mid"]["x"]
        gy = gp["mid"]["y"]
        dist = stadium_distance(x, y, gx, gy)
        angle = angle_from_goal(x, y, gx, gy)
        row = {
            "ag": 1 if is_scored_goal(kick) else 0,
            "index": i,
            "time": kick["time"],
            "x": x,
            "y": y,
            "goal_x": gx,
            "goal_y": gy,
            "goal_distance": dist,
            "goal_angle": angle,
            "team": kick["fromTeam"],
            "stadium": match["stadium"]
        }
        yield row


def predict_xg_demo(match, stadium, generate_rows, clf):
    """
    Augments match data with XG predictions.
    Args:
        match: Inflated match data (dict).
        stadium: Stadium data (dict).
        generate_rows: function(match, stadium) to generate kick records.
        clf: Classifier following scikit-learn interface.
    Returns:
        Inflated match data with "xg" field added to each kick (dict).
    """
    features = ["goal_distance", "goal_angle"]
    d_kicks = pd.DataFrame(generate_rows(match, stadium))
    d_kicks["xg"] = clf.predict_proba(d_kicks[features])[:,1]
    for kick in d_kicks.to_dict(orient="records"):
        match["kicks"][kick["index"]]["xg"] = kick["xg"]
    return match

def generate_rows_edwin(match, stadium):
    """
    Generates target and features for each kick in the match.
    Produces many features for model comparison.
    Args:
        match: Inflated match data (dict).
        stadium: Stadium data (dict).
    Returns:
        Generator of dicts with values for each kick in the given match.
        Includes prediction target "ag" (actual goals) which is 1 for a scored
        goal (goal or error) and 0 otherwise, "index" which is the index of the
        kick in the match kick list, and all the other features needed for
        prediction and explanation.
    """
    for i, kick in enumerate(match["kicks"]):
        gp = get_opposing_goalpost(stadium, kick["fromTeam"])
        x = kick["fromX"]
        y = kick["fromY"]
        gx = gp["mid"]["x"]
        gy = gp["mid"]["y"]
        dist = stadium_distance(x, y, gx, gy)
        angle = angle_from_goal(x, y, gx, gy)
        defender_dist,closest_defender = defender_feature(match,kick,100)
        defenders_within_box,in_box = defender_box(match,stadium,kick)
        defenders_within_shot,in_shot = defender_cone(match,stadium,kick,1)
        ball_speed=speed_ball(match,kick,1)
        row = {
            "ag": 1 if is_scored_goal(kick) else 0,
            "index": i,
            "time": kick["time"],
            "x": x,
            "y": y,
            "goal_x": gx,
            "goal_y": gy,
            "goal_distance": dist,
            "goal_angle": angle,
            "team": kick["fromTeam"],
            "stadium": match["stadium"],
            "defender_dist": defender_dist, # numerical , numbers within a range
            "closest_defender": closest_defender, # numerical, distance of the closest 
            "defenders_within_box": defenders_within_box, # numerical, number of player(defenders) within goal and kick(ball)
            "in_box": in_box, # Boolean, Is there defenders in this boxb bteween goal and kick
            "defenders_within_shot": defenders_within_shot, # numerical, how many players(defenders) are in this cone
            "in_shot": in_shot, # Boolean, Is there defenders in this cone
            "ball_speed": ball_speed # numerical, speeds ball within a given time range
        }
        yield row

def predict_xg_edwin(match, stadium, generate_rows, clf):
    """
    Augments match data with XG predictions.
    Args:
        match: Inflated match data (dict).
        stadium: Stadium data (dict).
        generate_rows: function(match, stadium) to generate kick records.
        clf: Classifier following scikit-learn interface.
    Returns:
        Inflated match data with "xg" field added to each kick (dict).
    """
    features = ["goal_distance","goal_angle","defender_dist","closest_defender","defenders_within_box","in_box","in_shot","ball_speed"]
    d_kicks = pd.DataFrame(generate_rows(match, stadium))
    d_kicks["xg"] = clf.predict_proba(d_kicks[features])[:,1]
    for kick in d_kicks.to_dict(orient="records"):
        match["kicks"][kick["index"]]["xg"] = kick["xg"]
    return match

def predict_xg_lynn_weighted(match, stadium, generate_rows, clf):
    """
    Augments match data with XG predictions.
    Args:
        match: Inflated match data (dict).
        stadium: Stadium data (dict).
        generate_rows: function(match, stadium) to generate kick records.
        clf: Classifier following scikit-learn interface.
    Returns:
        Inflated match data with "xg" field added to each kick (dict).
    """
    features = ['goal_angle', 'goal_distance', 'closest_defender', 'in_box', 'defenders_within_shot', 'in_shot', 'ball_speed', 'on_goal', 'player_speed', 'weighted_def_dist']
    d_kicks = pd.DataFrame(generate_rows(match, stadium))
    d_kicks["xg"] = clf.predict_proba(d_kicks[features])[:,1]
    for kick in d_kicks.to_dict(orient="records"):
        match["kicks"][kick["index"]]["xg"] = kick["xg"]
    return match

def predict_xg_lynn_both(match, stadium, generate_rows, clf):
    """
    Augments match data with XG predictions.
    Args:
        match: Inflated match data (dict).
        stadium: Stadium data (dict).
        generate_rows: function(match, stadium) to generate kick records.
        clf: Classifier following scikit-learn interface.
    Returns:
        Inflated match data with "xg" field added to each kick (dict).
    """
    features = ['goal_angle', 'goal_distance', 'defender_dist', 'closest_defender', 'in_box', 'defenders_within_shot', 'in_shot', 'ball_speed', 'on_goal', 'player_speed', 'weighted_def_dist']
    d_kicks = pd.DataFrame(generate_rows(match, stadium))
    d_kicks["xg"] = clf.predict_proba(d_kicks[features])[:,1]
    for kick in d_kicks.to_dict(orient="records"):
        match["kicks"][kick["index"]]["xg"] = kick["xg"]
    return match

def generate_rows_lynn(match, stadium):
    """
    Generates target and features for each kick in the match.
    Produces many features for model comparison.
    Args:
        match: Inflated match data (dict).
        stadium: Stadium data (dict).
    Returns:
        Generator of dicts with values for each kick in the given match.
        Includes prediction target "ag" (actual goals) which is 1 for a scored
        goal (goal or error) and 0 otherwise, "index" which is the index of the
        kick in the match kick list, and all the other features needed for
        prediction and explanation.
    """
    for i, kick in enumerate(match["kicks"]):
        gp = get_opposing_goalpost(stadium, kick["fromTeam"])
        x = kick["fromX"]
        y = kick["fromY"]
        gx = gp["mid"]["x"]
        gy = gp["mid"]["y"]
        dist = stadium_distance(x, y, gx, gy)
        angle = angle_from_goal(x, y, gx, gy)
        offset_int = 4
        offset_speed = 1
        end_time = kick["time"]
        pos_int = get_positions_in_range(match["positions"], end_time - offset_int, end_time)
        pos_speed = get_positions_in_range(pos_int, end_time - offset_speed, end_time)
        pos_def = get_positions_at_time(pos_speed, end_time)
        
        player_pos, ball_pos, intersect = shot_intersection(match,kick,stadium, pos_int)
        if intersect is None:
            on_goal = 0
        else:
            on_goal = shot_on_goal(match, kick, intersect, stadium)
        
        name = kick['fromName']
        player_speed = speed_player(match,kick, name, pos_speed)
        
        weighted_def_dist,closest_def = defender_feature_weighted(match,kick,stadium,pos_def,dist=4)
        
        defender_dist,closest_defender = defender_feature(match,kick,100)
        defenders_within_box,in_box = defender_box(match,stadium,kick)
        defenders_within_shot,in_shot = defender_cone(match,stadium,kick,1)
        ball_speed=speed_ball(match,kick,1)
        
        row = {
            "ag": 1 if is_scored_goal(kick) else 0,
            "index": i,
            "time": kick["time"],
            "x": x,
            "y": y,
            "goal_x": gx,
            "goal_y": gy,
            "goal_distance": dist,
            "goal_angle": angle,
            "team": kick["fromTeam"],
            "stadium": match["stadium"],
            #Edwins
            "defender_dist": defender_dist, 
            "closest_defender": closest_defender,
            "defenders_within_box": defenders_within_box, 
            "in_box": in_box, 
            "defenders_within_shot": defenders_within_shot, 
            "in_shot": in_shot, 
            "ball_speed": ball_speed,
            #Lynns
            "on_goal": on_goal,
            "player_speed": player_speed,
            "weighted_def_dist": weighted_def_dist,
            "closest_def": closest_def,
            "in_stadium": match["stadium"]
        }
        
        yield row