import sys
sys.path.append("./")


from decouple import config
from haxml.utils import (
    replace_usernames_all_time_kicks
)
import json
import pyrebase


# Get command line arguments.
if len(sys.argv) <= 1:
    raise IOError("Missing parameter: outfile")
outfile = sys.argv[1]


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


# Fetch all-time kicks data.
kicks_ref = db.child("kick").get()
all_kicks = kicks_ref.val()

# Remove usernames.
clean_kicks = replace_usernames_all_time_kicks(all_kicks)

# Add kick ID as field.
for key in clean_kicks.keys():
    clean_kicks[key]["kick"] = key

# Write to JSON file.
with open(outfile, "w") as file:
    json.dump(clean_kicks, file)
print("Wrote {:,} records to file: {}".format(len(clean_kicks), outfile))
