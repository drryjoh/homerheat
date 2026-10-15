# homerheat
Does humidity change how often home runs are hit, or how far they go?

The folk claim is that humid air is "thinner," so the ball carries farther. That part is real physics: water vapor (18 g/mol) is lighter than dry air (29 g/mol), so humid air is slightly less dense. The question is whether the effect is big enough to show up in MLB data once temperature, altitude, park and era are accounted for.

## Status (live)
| Stage | Owner | Status | Output |
|---|---|---|---|
| 1. Pull Statcast batted balls 2015–2025 + park locations | Data agent | 🔄 running | `src/`, `data/` |
| 2. Join first-pitch weather (RH, dew point, temp, pressure, rain) | Data agent | 🔄 running | `data/processed/` |
| Physics of humid air + simple trajectory model | Physics agent | 🔄 running | `physics/`, `notes/physics.md` |
| Baseball context, confounders, skeptic's checklist | Baseball agent | 🔄 running | `notes/baseball.md` |
| 3–5. Normalization + models (HR rate, distance vs humidity, rain) | Normalizing agent | ⏳ waits on data | `analysis/`, `notes/normalization.md` |
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
The exact commands to rebuild the data and every figure will be added here as each stage lands.

## Data sources
- **Statcast** via [pybaseball](https://github.com/jldbc/pybaseball): batted balls, exit velocity, launch angle, distance
- **MLB StatsAPI**: game start times, venue coordinates, reported conditions (dome/roof, rain)
- **Open-Meteo historical archive** (ERA5 reanalysis): hourly humidity, dew point, temperature, pressure, precipitation
