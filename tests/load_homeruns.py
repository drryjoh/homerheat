#!python3
from pybaseball import statcast

# Get data for a single season
data = statcast(start_dt="2025-01-01", end_dt="2025-06-30")

# Filter to only home runs
home_runs = data[data['events'] == 'home_run']
home_runs.to_pickle("home_runs_2025_first_half.pkl")
