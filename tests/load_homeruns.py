#!python3
from pybaseball import statcast
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def get_city_state():
    return  {
    'CLE': 'Cleveland, OH',
    'CIN': 'Cincinnati, OH',
    'BAL': 'Baltimore, MD',
    'ATL': 'Atlanta, GA',
    'PIT': 'Pittsburgh, PA',
    'TEX': 'Arlington, TX',         # Rangers play in Arlington, not Dallas
    'MIL': 'Milwaukee, WI',
    'NYY': 'New York, NY',
    'HOU': 'Houston, TX',
    'KC': 'Kansas City, MO',
    'DET': 'Detroit, MI',
    'AZ': 'Phoenix, AZ',            # Diamondbacks
    'LAA': 'Anaheim, CA',           # Angels play in Anaheim
    'MIN': 'Minneapolis, MN',
    'STL': 'St. Louis, MO',
    'SF': 'San Francisco, CA',
    'COL': 'Denver, CO',
    'CWS': 'Chicago, IL',           # White Sox
    'NYM': 'New York, NY',
    'SD': 'San Diego, CA',
    'TB': 'St. Petersburg, FL',     # Rays play in St. Pete, not Tampa
    'PHI': 'Philadelphia, PA',
    'CHC': 'Chicago, IL',           # Cubs
    'MIA': 'Miami, FL',
    'LAD': 'Los Angeles, CA',
    'TOR': 'Toronto, ON',
    'ATH': 'Oakland, CA',           # A's — still listed as Oakland for now
    'WSH': 'Washington, DC',
    'SEA': 'Seattle, WA',
    'BOS': 'Boston, MA'
    }
def get_lat_lon():
    return {
    'BAL': (39.2833, -76.6167),
    'BOS': (42.3467, -71.0972),
    'NYY': (40.8296, -73.9262),
    'TB': (27.7683, -82.6534),
    'TOR': (43.6414, -79.3894),
    'CWS': (41.8300, -87.6339),
    'CLE': (41.4962, -81.6852),
    'DET': (42.3390, -83.0485),
    'KC': (39.0516, -94.4805),
    'MIN': (44.9817, -93.2783),
    'HOU': (29.7574, -95.3550),
    'LAA': (33.8003, -117.8827),
    'OAK': (37.7516, -122.2005),
    'ATH': (37.7516, -122.2005), # may be wrong
    'SEA': (47.5914, -122.3325),
    'TEX': (32.7513, -97.0822),
    'ATL': (33.7348, -84.3897),
    'MIA': (25.7781, -80.2197),
    'NYM': (40.7571, -73.8458),
    'PHI': (39.9057, -75.1665),
    'PIT': (40.4469, -80.0057),
    'WSH': (38.8730, -77.0074),
    'CHC': (41.9484, -87.6553),
    'CIN': (39.0972, -84.5075),
    'COL': (39.7559, -104.9942),
    'LAD': (34.0739, -118.2400),
    'SD': (32.7076, -117.1566),
    'SF': (37.7786, -122.3893),
    'STL': (38.6226, -90.1928),
    'AZ': (33.4453, -112.0668),
    'MIL': (43.0280, -87.9712)}

# Get data for a single season
home_runs = pd.read_pickle("home_runs_2025_first_half.pkl")

home_runs_summary = home_runs[[
    'game_date',            # Date of home run
    'hit_distance_sc',      # Statcast estimated distance (in feet)
    'away_team',            # Away team
    'home_team',            # For mapping to ballpark location
    'game_pk',              # Game ID (useful if needed later)
    'inning',               # (Optional: context)
    'launch_speed',         # (Optional: exit velocity)
    'launch_angle'          # (Optional: launch angle)
]]

print(home_runs_summary['game_date'])
print("home team:")
print(home_runs_summary['home_team'])
unique_team_locations = home_runs_summary['home_team'].unique()

city_state = get_city_state()
lat_lon = get_lat_lon()


for location in unique_team_locations:
    print(lat_lon[location])


# Create the plot
fig = plt.figure(figsize=(12, 8))
ax = plt.axes(projection=ccrs.LambertConformal())
ax.set_extent([-130, -65, 23, 50], crs=ccrs.Geodetic())

# Add map features
ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.5)
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=':')

# Plot each point
for team, (lat, lon) in lat_lon.items():
    ax.plot(lon, lat, 'ro', markersize=5, transform=ccrs.Geodetic())
    ax.text(lon + 0.5, lat + 0.5, team, fontsize=9, transform=ccrs.Geodetic())

plt.title("MLB Ballpark Locations", fontsize=14)
plt.show()



""" map locations
ballpark_coords = {
    'Yankee Stadium': (40.8296, -73.9262),
    'Dodger Stadium': (34.0739, -118.2400),
    'Coors Field': (39.7559, -104.9942),
    # Add more parks...
}

home_runs_summary['latitude'] = home_runs_summary['venue_name'].map(lambda x: ballpark_coords.get(x, (None, None))[0])
home_runs_summary['longitude'] = home_runs_summary['venue_name'].map(lambda x: ballpark_coords.get(x, (None, None))[1])

"""