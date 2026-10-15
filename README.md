# homerheat
Does humidity change how often home runs are hit, or how far they go?

The folk claim is that humid air is "thinner," so the ball carries farther. That part is real physics: water vapor (18 g/mol) is lighter than dry air (29 g/mol), so humid air is slightly less dense. The question is whether the effect is big enough to show up in MLB data once temperature, altitude, park and era are accounted for.

## Status (live)
| Stage | Owner | Status | Output |
|---|---|---|---|
| 1. Pull Statcast batted balls 2015–2025 + park locations | Data agent | ✅ done | `src/`, `data/` |
| 2. Join first-pitch weather (RH, dew point, temp, pressure, rain) | Data agent | ✅ done | `data/processed/` |
| Physics of humid air + simple trajectory model | Physics agent | ✅ done | `physics/`, `notes/physics.md` |
| Baseball context, confounders, skeptic's checklist | Baseball agent | ✅ done | `notes/baseball.md` |
| 3–5. Normalization + models (HR rate, distance vs humidity, rain) | Normalizing agent | 🔄 running | `analysis/`, `notes/normalization.md` |
| Final 4-page report + one script per figure | Report agent | ⏳ last | `report/`, `figures/` |

## Questions being answered
1. Pull every home run (and every batted ball, for rates) as far back as possible. Statcast distance starts in 2015.
2. Are there more home runs on more humid days?
3. Do home runs happen on days with light rain? Map home run frequency across the US by month, adjusted for team and park quality.
4. Map average home run distance by US location.
5. Plot home run distance against humidity.

## Repo layout
```
src/        data pipeline (Statcast, MLB StatsAPI games/venues, Open-Meteo weather, air density)
analysis/   normalization and statistical models
physics/    trajectory model (python physics/trajectory.py)
figures/    one script per report figure -> figures/out/*.png
notes/      agent write-ups: data.md, physics.md, baseball.md, normalization.md
report/     final 4-page report
data/       downloaded and processed data (gitignored, rebuilt by scripts)
tests/      original exploration scripts
```

## Setup
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
Rebuild commands (more are added as each stage lands):
```bash
# data (~20 min first time; cached after) -> data/processed/{games,batted_balls}.parquet
.venv/bin/python src/fetch_statcast.py --years 2015-2025
.venv/bin/python src/fetch_games.py --years 2015-2025
.venv/bin/python src/fetch_weather.py
.venv/bin/python src/build_dataset.py

.venv/bin/python physics/trajectory.py   # distance vs RH table -> physics/out/distance_vs_rh.png
```

## Findings so far
- **Data:** 25,193 regular-season games and 1.30 M balls in play from 2015–2025, including 63,419 home runs. Statcast home run totals match MLB's official totals for every year from 2015 to 2024. Every game has first-pitch weather; ERA5 temperature agrees with the temperature MLB reports at r = 0.96. 21,140 games were played outdoors. Caveats are in `notes/data.md`.
- **Physics:** humid air is lighter (water is 18 g/mol, dry air 29 g/mol). Going from 0% to 100% RH lowers air density by 0.7–1.8% (60–90 °F), which adds **+1 to +3 ft** to a ~415 ft home run. By comparison, warming by 10 °F adds about 3 ft, Denver adds about 28 ft, and a 5 mph wind blowing out adds about 19 ft. Comparing the driest third of games with the most humid third predicts about +0.7 ft, or about 1.5–2% more home runs. That distance difference is only just detectable in Statcast. In home run counts alone, it is not reliably detectable.
- **Baseball:** season-to-season swings in home runs from changes to the ball (±15–20%) are about 10× any humidity effect. Humidity in the stored *ball* (before humidors were standard in 2022) works in the opposite direction and is much larger. Plan: use distance residuals after controlling for exit velocity and launch angle, use dew point rather than relative humidity, treat each park-and-period as its own unit, and use dome games as a placebo test.

## Data sources
- **Statcast** via [pybaseball](https://github.com/jldbc/pybaseball): batted balls, exit velocity, launch angle, distance
- **MLB StatsAPI**: game start times, venue coordinates, reported conditions (dome/roof, rain)
- **Open-Meteo historical archive** (ERA5 reanalysis): hourly humidity, dew point, temperature, pressure, precipitation
