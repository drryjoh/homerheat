# homerheat
Understand how weather plays a role in baseball homeruns
pip install pybaseball
from pybaseball import statcast

# Get data for a single season
data = statcast(start_dt="2015-01-01", end_dt="2015-12-31")

# Filter to only home runs
home_runs = data[data['events'] == 'home_run']
