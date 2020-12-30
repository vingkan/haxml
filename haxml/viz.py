"""
Methods for data visualization and plotting.
"""


import sys
sys.path.append("./")

from haxml.utils import (
    get_opposing_goalpost
)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt


def plot_stadium(stadium):
    """
    Draws bounds, midline, and goalposts of the stadium.
    Args:
        stadium: Stadium data (dict).
    Returns:
        Tuple (fig, ax).
    """
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    bounds = stadium["bounds"]
    ax.plot(
        bounds["minX"], bounds["minY"],
        color="black", marker="o"
    )
    ax.plot(
        bounds["minX"], bounds["maxY"],
        color="black", marker="o"
    )
    ax.plot(
        bounds["maxX"], bounds["minY"],
        color="black", marker="o"
    )
    ax.plot(
        bounds["maxX"], bounds["maxY"],
        color="black", marker="o"
    )
    ax.plot(
        [bounds["minX"], bounds["maxX"]],
        [bounds["minY"], bounds["minY"]],
        color="black", linestyle="-"
    )
    ax.plot(
        [bounds["minX"], bounds["maxX"]],
        [bounds["maxY"], bounds["maxY"]],
        color="black", linestyle="-"
    )
    ax.plot(
        [bounds["minX"], bounds["minX"]],
        [bounds["minY"], bounds["maxY"]],
        color="black", linestyle="-"
    )
    ax.plot(
        [bounds["maxX"], bounds["maxX"]],
        [bounds["minY"], bounds["maxY"]],
        color="black", linestyle="-"
    )
    ax.plot(
        [0, 0],
        [bounds["minY"], bounds["maxY"]],
        color="black", linestyle="-"
    )
    posts_red = get_opposing_goalpost(stadium, "blue")["posts"]
    ax.plot(posts_red[0]["x"], posts_red[0]["y"], "ro")
    ax.plot(posts_red[1]["x"], posts_red[1]["y"], "ro")
    ax.plot(
        [posts_red[0]["x"], posts_red[1]["x"]],
        [posts_red[0]["y"], posts_red[1]["y"]], "r"
    )
    posts_blue = get_opposing_goalpost(stadium, "red")["posts"]
    ax.plot(posts_blue[0]["x"], posts_blue[0]["y"], "bo")
    ax.plot(posts_blue[1]["x"], posts_blue[1]["y"], "bo")
    ax.plot(
        [posts_blue[0]["x"], posts_blue[1]["x"]],
        [posts_blue[0]["y"], posts_blue[1]["y"]], "b"
    )
    return fig, ax


def zoom_stadium(bounds, zoom=0.01):
    """
    Scales the dimensions of a stadium for plotting.
    Args:
        bounds: Bounds data from a stadium (dict).
        zoom: Scale factor, full scale (1.0) is usually too big to display in a
            notebook, so the suggested default is 0.01.
    Returns:
        Tuple of (scaled_width, scaled_height).
    """
    width = abs(bounds["maxX"] - bounds["minX"])
    height = abs(bounds["maxY"] - bounds["minY"])
    return zoom * width, zoom * height


def get_xg_time_series(match):
    """
    Produces series for XG match time plot.
    Args:
        match: Inflated match data (dict).
    Returns:
        Tuple of (time, ags_red, ags_blue, xgs_red, xgs_blue).
    """
    time = []
    ags_red = []
    ags_blue = []
    xgs_red = []
    xgs_blue = []
    ag_red = 0
    ag_blue = 0
    xg_red = 0
    xg_blue = 0
    time.append(0)
    ags_red.append(ag_red)
    ags_blue.append(ag_blue)
    xgs_red.append(xg_red)
    xgs_blue.append(xg_blue)
    for kick in match["kicks"]:
        if kick["type"] == "goal":
            if kick["fromTeam"] == "red":
                ag_red += 1
            else:
                ag_blue += 1
        elif kick["type"] == "own_goal":
            if kick["fromTeam"] == "red":
                ag_blue += 1
            else:
                ag_red += 1
        if kick["fromTeam"] == "red":
            xg_red += kick["xg"]
        else:
            xg_blue += kick["xg"]
        time.append(kick["time"])
        ags_red.append(ag_red)
        ags_blue.append(ag_blue)
        xgs_red.append(xg_red)
        xgs_blue.append(xg_blue)
    time.append(match["score"]["time"])
    ags_red.append(ag_red)
    ags_blue.append(ag_blue)
    xgs_red.append(xg_red)
    xgs_blue.append(xg_blue)
    return (
        time,
        ags_red,
        ags_blue,
        xgs_red,
        xgs_blue
    )


def plot_xg_time_series(match):
    """
    Plots XG match time series for a match.
    Args:
        match: Inflated match data (dict).
    Returns:
        Tuple (fig, ax).
    """
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    xg_time_ser = get_xg_time_series(match)
    time, ags_red, ags_blue, xgs_red, xgs_blue = xg_time_ser
    ax.plot(time, ags_red, color="red", linestyle="-", label="Red Actual")
    ax.plot(time, xgs_red, color="red", linestyle="--", label="Red XG")
    ax.plot(time, ags_blue, color="blue", linestyle="-", label="Blue Actual")
    ax.plot(time, xgs_blue, color="blue", linestyle="--", label="Blue XG")
    title = "Final Score: {} Won {}-{}\n{}"
    red_score = match["score"]["red"]
    blue_score = match["score"]["blue"]
    winner = "Red" if red_score > blue_score else "Blue"
    stadium_name = match["stadium"]
    ax.set_title(title.format(winner, red_score, blue_score, stadium_name))
    ax.set_xlabel("Match Time (secs)")
    ax.set_ylabel("Goals")
    ax.legend()
    return fig, ax


def plot_positions(positions, stadium):
    """
    Draws a list of positions on the stadium.
    Args:
        positions: List of positions (dicts) to draw.
        stadium: Stadium data (dict).
    Returns:
        Tuple (fig, ax).
    """
    min_alpha = 0.1
    max_alpha = 0.9
    # Assume positions is sorted by time.
    start_time = positions[0]["time"]
    end_time = positions[-1]["time"]
    player_radius = 15
    ball_radius = stadium["ball"]["radius"]
    fig, ax = plot_stadium(stadium)
    for pos in positions:
        # Reduce opacity of positions that happened earlier.
        t = pos["time"]
        if t < end_time:
            time_frac = (t - start_time) / (end_time - start_time)
            alpha = min_alpha + (time_frac * (max_alpha - min_alpha))
        else:
            alpha = max_alpha
        is_player = pos["type"] == "player"
        style_kwargs = {
            "color": pos["team"] if is_player else "lime",
            "marker": "o",
            "markersize": player_radius if is_player else ball_radius,
            "alpha": alpha
        }
        if pos["type"] == "player":
            ax.plot(pos["x"], pos["y"], **style_kwargs)
        else:
            ax.plot(pos["x"], pos["y"], **style_kwargs)
    return fig, ax
