"""
Server to produce on-demand XG predictions.
"""

import sys
sys.path.append("./")

from decouple import config
from flask import (
    Flask,
    jsonify,
    request,
    Response,
    send_file
)
from flask_cors import CORS
from haxml.prediction import (
    generate_rows_demo,
    predict_xg_demo,
    generate_rows_edwin,
    predict_xg_edwin
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
# Define the models to load in production.
DEFAULT_MODEL = "edwin_rf_12"
MODEL_CONFIGS = [
    {
        "name": "demo_logit",
        "path": "models/demo_logistic_regression.pkl",
        "generator": generate_rows_demo,
        "predictor": predict_xg_demo
    },
    {
        "name": "demo_tree",
        "path": "models/demo_DecisionTree.pkl",
        "generator": generate_rows_demo,
        "predictor": predict_xg_demo
    },
    {
        "name": "demo_knn5",
        "path": "models/demo_knn5.pkl",
        "generator": generate_rows_demo,
        "predictor": predict_xg_demo
    },
    {
        "name": "edwin_classic_rf_12",
        "path": "models/random_forest_max_depth_12_classic.pkl",
        "generator": generate_rows_edwin,
        "predictor": predict_xg_edwin
    },
    {
        "name": "edwin_classic_rf_8",
        "path": "models/random_forest_max_depth_8_classic.pkl",
        "generator": generate_rows_edwin,
        "predictor": predict_xg_edwin
    },
    {
        "name": "edwin_rf_12",
        "path": "models/random_forest_max_depth_12.pkl",
        "generator": generate_rows_edwin,
        "predictor": predict_xg_edwin
    },
    {
        "name": "edwin_rf_8",
        "path": "models/random_forest_max_depth_8.pkl",
        "generator": generate_rows_edwin,
        "predictor": predict_xg_edwin
    }
]
# Dict of production models, key: model name, value: tuple (clf, generator_fn, predictor_fn).
production_models = {}
for model_config in MODEL_CONFIGS:
    clf = joblib.load(model_config["path"])
    gen = model_config["generator"]
    pred = model_config["predictor"]
    production_models[model_config["name"]] = (clf, gen, pred)

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


def get_model_name(request):
    """
    Helper method to get model name from request args.
    """
    model_name = request.args.get("clf")
    return model_name if model_name is not None else DEFAULT_MODEL


def get_model_by_name(model_name=DEFAULT_MODEL):
    """
    Gets the classifier and generator function based on the given name.
    Args:
        model_name: Name of the model in MODEL_CONFIGS (str).
    Returns:
        Tuple (clf, generator_fn, predictor_fn).
    """
    if model_name not in production_models:
        raise KeyError("No model named: {}".format(model_name))
    clf, gen, pred = production_models[model_name]
    return clf, gen, pred


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
    model_name = get_model_name(request)
    try:
        clf, gen, pred = get_model_by_name(model_name)
    except KeyError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
    match_xg = pred(inflate_match(packed), stadium, gen, clf)
    # Return inflated match data with XG as JSON.
    res = {
        "success": True,
        "mid": mid,
        "model_name": model_name,
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
    model_name = get_model_name(request)
    try:
        clf, gen, pred = get_model_by_name(model_name)
    except KeyError as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })
    match_xg = pred(inflate_match(packed), stadium, gen, clf)
    # Create and save XG time plot.
    fig, ax = plot_xg_time_series(match_xg)
    # Add model name to a line in the chart title.
    ax.set_title("{}\nXG Model: {}".format(ax.title.get_text(), model_name))
    fig.set_size_inches(10, 6)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")


# Start the server on the default host.
if __name__ == "__main__":
    print("Starting server...")
    app.run(host="0.0.0.0", port=int(config("PORT")))
