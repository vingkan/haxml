"""
Server to produce on-demand XG predictions.
"""

import sys
sys.path.append("./")

from decouple import config
from flask import (
    Flask,
    jsonify
)
from haxml.prediction import (
    generate_rows_demo,
    predict_xg_demo
)
from haxml.utils import (
    get_stadiums,
    inflate_match
)
import joblib
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
# Initialize Flask app.
app = Flask(__name__)

# Load demo model.
print("Loading models...")
demo_clf = joblib.load("models/demo_logistic_regression.pkl")
# Load stadium data.
print("Loading stadiums...")
stadiums = get_stadiums("data/stadiums.json")


"""
Basic hello world route to check if server is running.
"""
@app.route("/hello")
def hello():
    return "Welcome to HaxML."


"""
Fetch the match data for a given ID and then augment it with expected goals.
"""
@app.route("/xg/<mid>")
def get_xg(mid):
    # Fetch the packed match data from Firebase.
    r = db.child("match/{}".format(mid)).get()
    packed = r.val()
    # Check if stadium data is available.
    stadium_name = packed["stadium"]
    if not stadium_name in stadiums:
        return jsonify({
            "success": False,
            "message": "No stadium data for: {}".format(stadium_name)
        })
    # Inflate the packed data to get all the fields in the data schema.
    # Predict XG with demo model and augment response with predictions.
    match_xg = predict_xg_demo(
        inflate_match(packed),
        stadiums[stadium_name],
        generate_rows_demo,
        demo_clf
    )
    # Return the response as JSON.
    res = {
        "success": True,
        "mid": mid,
        "match": match_xg
    }
    return jsonify(res)


# Start the server on the default host.
if __name__ == "__main__":
    print("Starting server...")
    app.run(host="0.0.0.0")
