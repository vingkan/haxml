"""
Methods for data visualization and plotting.
"""


import sys
sys.path.append("./")

from haxml.utils import (
    get_opposing_goalpost
)
import matplotlib.pyplot as plt


def plot_stadium(stadium):
    """
    Drawns bounds, midline, and goalposts of the stadium,
    Args:
        stadium: Stadium data (dict).
    Returns:
        Matplotlib plot object.
    """
    bounds = stadium["bounds"]
    plt.plot(
        bounds["minX"], bounds["minY"],
        color="black", marker="o"
    )
    plt.plot(
        bounds["minX"], bounds["maxY"],
        color="black", marker="o"
    )
    plt.plot(
        bounds["maxX"], bounds["minY"],
        color="black", marker="o"
    )
    plt.plot(
        bounds["maxX"], bounds["maxY"],
        color="black", marker="o"
    )
    plt.plot(
        [bounds["minX"], bounds["maxX"]],
        [bounds["minY"], bounds["minY"]],
        color="black", linestyle="-"
    )
    plt.plot(
        [bounds["minX"], bounds["maxX"]],
        [bounds["maxY"], bounds["maxY"]],
        color="black", linestyle="-"
    )
    plt.plot(
        [bounds["minX"], bounds["minX"]],
        [bounds["minY"], bounds["maxY"]],
        color="black", linestyle="-"
    )
    plt.plot(
        [bounds["maxX"], bounds["maxX"]],
        [bounds["minY"], bounds["maxY"]],
        color="black", linestyle="-"
    )
    plt.plot(
        [0, 0],
        [bounds["minY"], bounds["maxY"]],
        color="black", linestyle="-"
    )
    posts_red = get_opposing_goalpost(stadium, "blue")["posts"]
    plt.plot(posts_red[0]["x"], posts_red[0]["y"], "ro")
    plt.plot(posts_red[1]["x"], posts_red[1]["y"], "ro")
    plt.plot(
        [posts_red[0]["x"], posts_red[1]["x"]],
        [posts_red[0]["y"], posts_red[1]["y"]], "r"
    )
    posts_blue = get_opposing_goalpost(stadium, "red")["posts"]
    plt.plot(posts_blue[0]["x"], posts_blue[0]["y"], "bo")
    plt.plot(posts_blue[1]["x"], posts_blue[1]["y"], "bo")
    plt.plot(
        [posts_blue[0]["x"], posts_blue[1]["x"]],
        [posts_blue[0]["y"], posts_blue[1]["y"]], "b"
    )
    return plt


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
