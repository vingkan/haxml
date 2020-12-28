import sys
sys.path.append("./")

from decouple import config
from haxml.utils import (
    get_matches_metadata,
    replace_usernames_packed_matches
)
import json
import pyrebase
from tqdm import tqdm


# Get command line arguments.
if len(sys.argv) <= 1:
    raise IOError("Missing parameter: infile")
infile = sys.argv[1]
if len(sys.argv) <= 2:
    raise IOError("Missing parameter: outpath")
outpath = sys.argv[2]

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
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

# Read selected match IDs from match metadata dicts.
match_ids = []
metadata = get_matches_metadata(infile)
for meta in metadata:
    match_ids.append(meta["match_id"])

# Fetch packed match data from Firebase.
print("Downloading packed match data from Firebase...")
match_dict = {}
for match_id in tqdm(match_ids):
    snap = db.child(f"match/{match_id}").get()
    packed = snap.val()
    if packed is not None:
        match_dict[match_id] = packed

# Remove usernames.
print("Replacing usernames for {:,} matches...".format(len(match_dict)))
clean_matches = replace_usernames_packed_matches(match_dict, progress=True)

# Write matches to file.
for key in clean_matches.keys():
    match = clean_matches[key]
    # Add match ID as field.
    match["match"] = key
    outfile = "{}/{}.json".format(outpath, key)
    with open(outfile, "w") as file:
        json.dump(match, file)
print("Wrote {:,} match records to directory: {}".format(len(match_dict), outpath))
