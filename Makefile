DATA_DIR := data
MATCH_DIR := data/packed_matches

all: data/stadiums.json $(MATCH_DIR)

$(MATCH_DIR): data/matches_metadata.csv | $(DATA_DIR)
	mkdir $(MATCH_DIR)
	python3 scripts/download_packed_matches.py "data/matches_metadata.csv" "data/packed_matches"

data/matches_metadata.csv: data/all_time_kicks.json | $(DATA_DIR)
	python3 scripts/make_matches_metadata.py "data/all_time_kicks.json" "data/matches_metadata.csv"

data/all_time_kicks.json: | $(DATA_DIR)
	python3 scripts/download_all_time_kicks.py "data/all_time_kicks.json"

data/stadiums.json: | $(DATA_DIR)
	wget -O "data/stadiums.json" "https://vingkan.github.io/haxclass/stadium/map_data.json"

$(DATA_DIR):
	mkdir $(DATA_DIR)

clean:
	rm -rf data