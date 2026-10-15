# Data

## Sources
- **Statcast** (Baseball Savant via `pybaseball.statcast`, cache enabled): every regular-season
  ball in play (`type == 'X'`, `game_type == 'R'`), 2015-2025.
- **MLB StatsAPI** schedule (`/api/v1/schedule?sportId=1&season=YYYY&gameType=R&hydrate=weather,venue(location),team`):
  one row per completed game with scheduled UTC first pitch (`gameDate`), venue id/name/lat/lon/elevation,
  and the reported weather (condition, temp F, wind string). The hydrate returned weather for 100% of games;
  the per-game `/api/v1.1/game/{pk}/feed/live` fallback is coded but only filled coordinates.
- **ERA5 reanalysis** via Open-Meteo archive (`archive-api.open-meteo.com/v1/archive`, `models=era5`):
  one request per venue per season, hourly temperature_2m, relative_humidity_2m, dew_point_2m,
  surface_pressure, pressure_msl, precipitation, rain, wind_speed_10m (m/s), wind_direction_10m.
  The stadium elevation is passed so surface_pressure/temperature are downscaled to the park.
  The hour nearest the scheduled first pitch (UTC) is used. Raw JSON is cached in `data/raw/weather/`.
- **Air density** from `physics/air.py` (moist-air ideal gas, Magnus/Bolton e_s) using ERA5 T, RH, surface pressure.

## Rerun (from repo root, with the venv)
```
.venv/bin/python src/fetch_statcast.py --years 2015-2025   # slow (tens of minutes), resumable, skips saved years
.venv/bin/python src/fetch_games.py --years 2015-2025      # ~1 min
.venv/bin/python src/fetch_weather.py                      # ~10 min first time, cached afterwards
.venv/bin/python src/build_dataset.py
```
Quick Statcast test: `.venv/bin/python src/fetch_statcast.py --start 2024-04-01 --end 2024-04-02`.

## Outputs
- `data/raw/statcast_{year}.parquet`, `data/raw/games.parquet`, `data/raw/game_weather.parquet`, `data/raw/weather/*.json`
- `data/processed/batted_balls.parquet`: 1,302,161 rows, one per ball in play, with all game/weather columns, `is_hr`, `is_fly_ball`, `year`, `month`.
- `data/processed/games.parquet`: 25,193 rows, one per game, weather + `n_hr`, `n_batted_balls`,
  `n_fly_balls`, `mean_hr_distance`, `air_density`, `vapor_pressure_hpa`, `dew_point_2m`,
  `roof_closed`, `is_dome_venue`, `has_retractable_roof`, `is_raining`.

Units: ERA5 temperature/dew point in deg C, RH in %, pressure in hPa, precip in mm/h, wind m/s
(direction = where wind comes FROM, degrees). `temp_f_reported`/`wind_mph_reported` are StatsAPI.
`azimuth_deg` (StatsAPI) is the park's orientation, for projecting wind onto the CF direction.

## Sanity table
| year | games | % weather | % indoor (roof_closed) | balls in play | HR (Statcast) | known MLB HR | % HR missing distance | % all BIP missing distance |
|---|---|---|---|---|---|---|---|---|
| 2015 | 2429 | 100 | 14.6 | 130,475 | 4,909 | 4,909 | 3.1 | 13.1 |
| 2016 | 2428 | 100 | 14.5 | 128,821 | 5,610 | 5,610 | 2.1 | 12.2 |
| 2017 | 2430 | 100 | 14.4 | 127,556 | 6,105 | 6,105 | 2.5 | 10.9 |
| 2018 | 2431 | 100 | 14.5 | 126,284 | 5,585 | 5,585 | 2.1 | 8.9 |
| 2019 | 2429 | 100 | 15.2 | 125,755 | 6,776 | 6,776 | 1.3 | 9.0 |
| 2020 | 898 | 100 | 17.1 | 43,972 | 2,304 | 2,304 | 0.2 | 0.7 |
| 2021 | 2429 | 100 | 16.8 | 121,706 | 5,944 | 5,944 | 0.2 | 0.3 |
| 2022 | 2430 | 100 | 18.1 | 124,267 | 5,215 | 5,215 | 0.0 | 0.4 |
| 2023 | 2430 | 100 | 18.3 | 124,234 | 5,868 | 5,868 | 0.1 | 0.3 |
| 2024 | 2429 | 100 | 18.8 | 124,203 | 5,453 | 5,453 | 0.2 | 0.3 |
| 2025 | 2430 | 100 | 15.3 | 124,888 | 5,650 | (not independently checked) | 0.1 | 0.3 |

HR counts match published MLB season totals exactly for 2015-2024. Every game has Statcast rows,
and every batted ball matched a game. ERA5 vs StatsAPI reported temperature (outdoor games):
mean difference +0.1 F, SD 3.3 F, r = 0.955.

## Caveats
- **Distance/EV gaps 2015-2019**: Trackman-era Statcast misses `hit_distance_sc` for 9-13% of balls in play
  (and `launch_speed` for 1.4-3.4%), non-randomly (weak contact, some parks). HR distance is missing for 1-3%.
  Hawk-Eye from 2020 is nearly complete. The tracking-system change in 2020 can shift distance levels.
- **2020**: 60-game season, no fans, regional schedule; 2020-21 Blue Jays played in Buffalo (Sahlen Field)
  and Dunedin (TD Ballpark).
- **ERA5 is ~0.25 deg (~25-30 km) grid reanalysis**, not a stadium sensor. Coastal parks (Oracle, Petco,
  T-Mobile, Fenway) can be biased by land/sea mixing. `era5_grid_lat/lon` give the cell used.
- **First pitch time** is the scheduled `gameDate`, not the actual first pitch: rain delays shift it, and some
  doubleheader game 2 times are estimates. Weather is the nearest whole hour.
- **Indoor games**: `roof_closed` = StatsAPI condition 'Dome'/'Roof Closed' OR fixed dome (Tropicana, Tokyo Dome,
  Gocheok Sky Dome). 14-19% of games per year. A retractable-roof game with an ordinary condition is
  assumed open; the ERA5 values for indoor games describe outside air, not the park. T-Mobile Park's roof
  is an open-sided umbrella. Exclude `roof_closed` for weather analyses.
- **is_raining** = condition contains Rain/Drizzle (269 games) OR ERA5 precipitation > 0.1 mm/h (2,790 games;
  only 165 overlap). ERA5 has a known drizzle bias, so this flag fires on ~11% of games; use `condition` or
  a higher `precipitation` threshold for a stricter definition.
- **Venue coordinate fixes** (`VENUE_FIX` in `src/fetch_games.py`): StatsAPI was missing or wrong for Turner Field,
  London Stadium (pointed at central London), Bristol Motor Speedway (latitude off by 5 deg), Mexico City,
  Monterrey, Fort Bragg, Omaha, Field of Dreams, Rickwood, Williamsport, Tokyo, Seoul and San Juan. Elevations
  for those are approximate (to ~100 ft). Mexico City (7,350 ft) is the thinnest air in the set, below even Coors.
- **Park changes** that confound year-over-year comparisons: Rogers Centre fence moves/height changes (2023),
  Camden Yards LF wall moved back (2022) and partly back in (2025), Comerica CF in (2023), smaller
  dimension changes elsewhere (e.g. Citi Field, Marlins Park); new parks
  Truist (2017), Globe Life Field (2020, roof), A's at Sutter Health Park (2025), Rays at Steinbrenner Field (2025),
  Astros' park renamed Daikin (2025). `venue_id` is stable across renames; use it, not `venue_name`.
- **Ball changes** (2016-2019 livelier ball, 2021 deadened ball, humidors in all parks from 2022) produce
  league-wide HR swings that dwarf weather effects; control for year.
- `is_hr` includes inside-the-park home runs.
