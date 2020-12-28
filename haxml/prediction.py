"""
Methods for preparing data and making XG predictions.
"""

import sys
sys.path.append("./")

from haxml.utils import (
    get_opposing_goalpost,
    stadium_distance,
    angle_from_goal,
    is_scored_goal
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
