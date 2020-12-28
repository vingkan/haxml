"""
Server to produce on-demand XG predictions.
"""

import sys
sys.path.append("./")

from decouple import config
from flask import (
    Flask,
    jsonify,
    Response,
    send_file
)
from flask_cors import CORS
from haxml.prediction import (
    generate_rows_demo,
    predict_xg_demo
)
from haxml.utils import (
    get_stadiums,
    inflate_match
)
from haxml.viz import (
    plot_xg_time_series
)
import io
import joblib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import os
import pyrebase


# Load Firebase credentials from .env file.
firebase_config = {
    "apiKey": config("firebase_apiKey"),
    "authDomain": config("firebase_authDomain"),
    "databaseURL": config("firebase_databaseURL"),
    "projectId": config("firebase_projectId"),
    "storageBucket": config("firebase_storageBucket"),
    "messagingSenderId": config("firebase_messagingSenderId"),
    "appId": config("firebase_appId")
}
# Open connection to Firebase.
print("Connecting to database...")
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()
# Initialize Flask app and enable CORS.
app = Flask(__name__)
allow_list = [
    "http://localhost:2000",
    "https://vingkan.github.io"
]
cors = CORS(app, resource={"/*": {"origins": allow_list}})

# Load demo model.
print("Loading models...")
demo_clf = joblib.load("models/demo_logistic_regression.pkl")
# Load stadium data.
print("Loading stadiums...")
stadiums = get_stadiums("data/stadiums.json")


def get_match_packed(mid):
    """
    Fetch packed match data from Firebase.
    """
    r = db.child("match/{}".format(mid)).get()
    packed = r.val()
    if packed is None:
        raise ValueError("Match data not found for: {}".format(mid))
    return packed


def get_stadium_data(stadium_name):
    """
    Checks if stadium data is available.
    """
    if stadium_name not in stadiums:
        raise ValueError("No stadium data for: {}".format(stadium_name))
    return stadiums[stadium_name]


def get_match_and_stadium(mid):
    """
    Helper method to get packed match data and stadium.
    """
    packed = get_match_packed(mid)
    stadium = get_stadium_data(packed["stadium"])
    return packed, stadium


def get_match_xg(packed, stadium):
    """
    Predict XG with demo model and augment response with predictions.
    """
    return predict_xg_demo(
        inflate_match(packed),
        stadium,
        generate_rows_demo,
        demo_clf
    )


@app.route("/hello")
def hello():
    """
    Basic hello world route to check if server is running.
    """
    return "Welcome to HaxML."


@app.route("/xg/<mid>")
def get_xg(mid):
    """
    Fetch the match data for a given ID and then augment it with expected goals.
    """
    try:
        packed, stadium = get_match_and_stadium(mid)
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
    match_xg = get_match_xg(packed, stadium)
    # Return inflated match data with XG as JSON.
    res = {
        "success": True,
        "mid": mid,
        "match": match_xg
    }
    return jsonify(res)


@app.route("/xgtimeplot/<mid>.png")
def get_xg_time_plot(mid):
    """
    Create and serve XG time plot for the given match.
    """
    try:
        packed, stadium = get_match_and_stadium(mid)
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
    match_xg = get_match_xg(packed, stadium)
    # Create and save XG time plot.
    fig = plot_xg_time_series(match_xg)
    fig.set_size_inches(10, 6)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")


# Start the server on the default host.
if __name__ == "__main__":
    print("Starting server...")
    app.run(host="0.0.0.0")
