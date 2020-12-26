all: data/all_time_kicks.json

data/all_time_kicks.json:
	python3 scripts/download_all_time_kicks.py "data/all_time_kicks.json"

clean:
	rm data/all_time_kicks.json
