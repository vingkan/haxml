import sys
sys.path.append("./")

from haxml.utils import (
    is_target_stadium,
    is_scored_goal
)
import json
from tqdm import tqdm


# Get command line arguments.
if len(sys.argv) <= 1:
    raise IOError("Missing parameter: infile")
infile = sys.argv[1]
if len(sys.argv) <= 2:
    raise IOError("Missing parameter: outfile")
outfile = sys.argv[2]

# Read all-time kicks from file.
with open(infile, "r") as file:
    all_time_kicks = json.load(file)

# Collect unique match IDs and metadata.
print("Saving metadata for {:,} all-time kicks...".format(len(all_time_kicks)))
metadata_dict = {}
# Each value is a tuple of (column_name, type_name).
metadata_cols = [
    ("match_id", "str"),
    ("stadium", "str"),
    ("time", "float"),
    ("kicks_red", "int"),
    ("kicks_blue", "int"),
    ("score_red", "int"),
    ("score_blue", "int"),
    ("scored_goals_red", "int"),
    ("scored_goals_blue", "int")
]
for kick in tqdm(all_time_kicks.values()):
    # Only include matches that took place in target stadiums.
    if not is_target_stadium(kick["stadium"]):
        continue
    key = kick["match"]
    if key not in metadata_dict:
        metadata_dict[key] = {
            "match_id": key,
            "stadium": kick["stadium"],
            "time": kick["time"],
            "kicks_red": 0,
            "kicks_blue": 0,
            "score_red": kick["scoreRed"],
            "score_blue": kick["scoreBlue"],
            "scored_goals_red": 0,
            "scored_goals_blue": 0
        }
    acc = metadata_dict[key]
    # Accumulate match state data from the latest kick record.
    if kick["time"] > acc["time"]:
        acc["time"] = kick["time"]
        acc["score_red"] = kick["scoreRed"]
        acc["score_blue"] = kick["scoreBlue"]
    # Save counts by team, totals can be reconstructed through addition.
    is_for_red = kick["fromTeam"] == "red"
    if is_for_red:
        acc["kicks_red"] += 1
    else:
        acc["kicks_blue"] += 1
    if is_scored_goal(kick):
        if is_for_red:
            acc["scored_goals_red"] += 1
        else:
            acc["scored_goals_blue"] += 1

# Write match IDs and metadata for train/test split to file.
with open(outfile, "w") as file:
    header = ",".join([c for c, t in metadata_cols]) + "\n"
    types = ",".join([t for c, t in metadata_cols]) + "\n"
    file.write(header)
    file.write(types)
    for meta in metadata_dict.values():
        line = ",".join([str(meta[c]) for c, t in metadata_cols]) + "\n"
        file.write(line)
print("Wrote {:,} match metadata to file: {}".format(len(metadata_dict), outfile))

