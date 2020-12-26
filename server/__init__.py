from decouple import config
from haxclass import (
    inflate,
    is_shot
)
from flask import (
    Flask,
    jsonify
)
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
# Open connection to database and initialize Flask app.
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()
app = Flask(__name__)


"""
Basic hello world route to check if server is running.
"""
@app.route("/")
def hello():
    return "Welcome to HaxML."


"""
Fetch the match data for a given ID and then augment it with expected goals.
"""
@app.route("/xg/<mid>")
def get_xg(mid):
    # Fetch the packed match data from Firebase.
    r = db.child("match/{}".format(mid)).get()
    # Inflate the packed data to get all the fields in the data schema.
    match = inflate(r.val())
    # Find the kicks that count as shots.
    for kick in match["kicks"]:
        if is_shot(kick):
            # TODO: Placeholder, add prediction logic here.
            kick["expected_goal"] = 0.71
    # Return the response as JSON.
    res = {
        "success": True,
        "mid": mid,
        "match": match
    }
    return jsonify(res)


# Start the server on the default host.
if __name__ == "__main__":
    app.run(host="0.0.0.0")
