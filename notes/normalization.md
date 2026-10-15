# Normalization and statistics: does humidity move fly balls?

*Normalizing agent. Code: `analysis/` (run `.venv/bin/python -m analysis.run_all`, ~5 min). Results: `analysis/results/*.csv`.*

**Bottom line.** Humid air carries fly balls slightly farther, and the effect is detectable. Holding exit velocity, launch angle, spray, temperature, pressure, wind, park and season-month fixed, **+10 °C of dew point adds about +0.9 ft (95% CI 0.7–1.1)**. Physics predicts +0.55 ft. The humid third of games carries **+0.7 ft (0.4–1.0)** more than the dry third, which matches the physics note's ~+0.7 ft. Some of the excess over physics looks like leftover temperature confounding: with better in-park temperature control the estimate drops to **0.69 (0.46–0.92)**, and that CI includes physics. In **home-run counts** the effect is too small to see. EV/LA-adjusted HR rate rises **+1.9% per 10 °C dew point (0.6–3.3)**, against 1.1–1.7% predicted. Game-level HR per fly ball shows **no detectable increase (−1.1%, −3.4 to +1.1)**. Rain has no effect of its own.

## Methods (why each normalization is there)

- **Sample.** We use outdoor games at real home parks only. That means 2015–2025, excluding `roof_closed` and the neutral or special sites (London, Mexico, Tokyo, Seoul, Field of Dreams, Rickwood, Williamsport, Fort Bragg, Omaha, Bristol, San Juan). The primary unit is the **air ball**: launch angle 20–40°, EV ≥ 90 mph, distance tracked. That leaves 159,725 balls in 20,744 games, holding 46,128 of the 50,111 outdoor HRs. Humid air can only matter for balls in the air long enough. Grounders add noise.
- **Launch conditions, and team/batter quality (main fix).** Stage 1 predicts each ball's `hit_distance_sc` from EV × LA tensor splines plus pull-side spray splines, with **separate fits for TrackMan (2015–19) and Hawk-Eye (2020+)** because 2020 was a measurement break. R² is 0.81–0.83 and residual SD ≈ 15 ft. The **residual** (actual − expected) is how far the ball carried beyond what its launch implies. A stronger lineup hits the ball harder, and that ends up in "expected", not in the residual, so team and batter quality drop out without team terms.
- **Era / ball.** Season × month FE appear in both stages. They absorb the juiced (2016–19) and deadened (2021) balls, within-season ball-lot drift, and the humidor rollout. Splits are reported pre/post 2022 and by tracking system.
- **Park.** We use `park_period` FE: `venue_id` split at the fence changes (BAL 2022/2025, TOR 2023, DET 2023, SF 2020, NYM 2023, MIA 2016/2021). Weather effects are therefore estimated *within a park*, day to day. Altitude and fence distance cannot leak in.
- **Temperature, pressure, wind.** Humid days are hot days. With no temperature control the "humidity" coefficient triples (2.6 ft, table below). Every model includes ERA5 temperature, surface pressure, and the 10 m wind projected onto the park's home→CF bearing (out-to-CF and crosswind). Wind convention check: the ERA5 out-component tracks StatsAPI "Out/In" strings, and Wrigley HR/FB runs from 12.5% to 28% from the bottom to the top wind quintile. We use dew point (or vapour pressure), not RH, because RH falls as air warms even when the moisture content is unchanged.
- **Inference.** SEs are clustered by game (weather is shared within a game). **Physics benchmark:** we compute each game's density-predicted carry shift (−0.37% of distance per +1% density, from `notes/physics.md`) and run the *identical* regression on it. That gives the coefficient physics expects under the same controls.
- **HR models.** (a) Ball-level logit `is_hr ~ launch splines + weather + park_period FE + season-month FE`. Odds ratios conditional on launch overstate rate changes, so we report the implied % change in expected HR count (average-marginal-effect linearisation). (b) Game-level Poisson for `n_hr` with offset log(fly balls). Its **team-quality handling** uses home team-season×park FE plus away team-season FE (with park FE and month FE), compared against park + season-month FE only.

## Main results

| Quantity | Estimate | 95% CI | Physics | n balls / games |
|---|---|---|---|---|
| Distance residual, per +10 °C dew point | **+0.89 ft** | 0.67 – 1.12 | +0.55 | 159,725 / 20,744 |
| ... per +10 hPa vapour pressure | +0.84 ft | 0.62 – 1.06 | +0.56 | same |
| ... humid vs dry tercile of games | +0.68 ft | 0.37 – 0.98 | ≈ +0.7 | same |
| ... per +10 RH points (sensitivity, T controlled) | +0.29 ft | 0.22 – 0.36 | +0.15 | same |
| Air density alone, per +1% | **−1.41 ft** | −1.46 – −1.35 | −1.35 | same |
| ... dry-air part of density, per +1% | −1.36 ft | −1.42 – −1.30 | −1.35 | same |
| ... water-vapour part of density, per +1% | −2.22 ft | −2.80 – −1.64 | −1.35 | same |
| Temperature, per +10 °C | +4.37 ft | 4.14 – 4.61 | +4.55 | same |
| Wind out to CF (ERA5 10 m), per +1 m/s | +0.62 ft | 0.57 – 0.66 | — | same |
| HR (logit, EV/LA-adjusted), per +10 °C dew point | **+1.9%** | 0.6 – 3.3 | +1.1 – 1.7 | 159,725 / 46,128 HR |
| HR (logit), humid vs dry tercile | +1.0% | −0.8 – 2.8 | +1.5 – 2 | same |
| HR (logit), per +10 °C temperature | +14.9% | 13.2 – 16.5 | +11 – 14 | same |
| HR/FB Poisson, per +10 °C dew point (park + season-month FE) | −1.2% | −3.4 – 1.1 | +1.1 – 1.7 | 20,806 games / 49,416 HR |
| HR/FB Poisson, per +10 °C dew point (team-season FE) | −1.1% | −3.3 – 1.3 | | same |
| HR/FB Poisson, humid vs dry tercile (team-season FE) | −3.0% | −8.1 – 2.5 | | same |
| HR/FB Poisson, per +10 °C temperature (team-season FE) | +16.6% | 13.7 – 19.5 | ≈ +20 (Callahan) | same |

**Against physics.** The model reproduces the density physics almost exactly: air density −1.41 vs −1.35 ft per %, and temperature +4.37 vs +4.55 ft per 10 °C. Coors' mean residual (+19.7 ft) matches its density prediction (+20.3 ft). Humidity has the **right sign and the right order of magnitude**, but the point estimate is ~1.6× physics, and the vapour part of density (−2.2) is steeper than the dry part (−1.4). The table below points to temperature measurement as the reason. Holding first-pitch ERA5 temperature fixed, +10 °C of dew point means the game window averages +0.57 °C warmer, because humid air masses cool less after dark. Adding the in-park StatsAPI thermometer reading and ball-time temperature pulls the estimate to 0.69 (0.46–0.92), and that CI includes physics. Treat **~0.5–0.9 ft per 10 °C dew point** as the honest range.

**Why the HR-count models disagree.** The logit holds EV fixed. The Poisson does not, and **exit velocity is 0.12 mph lower per +10 °C dew point (0.05–0.19)**. That is worth roughly −0.5 ft, which cancels most of the aerodynamic gain. The cause could be ball moisture, which persists after the humidors went in because balls are out for ≤2 h; the measurement is also on a truncated EV ≥ 90 sample. Team-season FE barely move the Poisson (−1.15 → −1.07). Team quality is not what hides or creates the humidity effect. The Poisson MDE (~±2–3%) is above the physics effect, so the Poisson null is uninformative, not a contradiction.

## Rain (`rain.csv`; rain dummy added to the primary specs, dew point controlled)

| Flag | Games / air balls | Distance resid | HR (EV/LA-adj.) |
|---|---|---|---|
| StatsAPI "Rain/Drizzle" at first pitch (strict) | 264 / 1,917 | −0.07 ft (−0.90, +0.76) | −2.8% (−7.5, +2.2) |
| ERA5 precip > 1 mm/h | 479 / 3,584 | −0.06 ft (−0.69, +0.57) | −1.8% (−5.4, +2.0) |
| ERA5 precip > 0.1 mm/h (noisy) | 1,846 / 14,029 | +0.28 ft (−0.05, +0.61) | +0.0% (−1.9, +2.0) |

Raw residuals in StatsAPI-rain games are −2.7 ft, but that comes entirely from the cooler air. After weather controls, rain has no detectable effect. Only games that were actually played are included, and weather is measured at first pitch.

## Robustness (`robustness.csv`; ft of residual per +10 °C dew point unless noted)

| Spec | Est. | 95% CI | Physics |
|---|---|---|---|
| Primary | 0.89 | 0.67 – 1.12 | 0.55 |
| Pre-2022 / 2022+ (humidors) | 0.76 / 1.18 | 0.47–1.05 / 0.83–1.53 | 0.56 / 0.54 |
| TrackMan / Hawk-Eye | 0.58 / 1.24 | 0.25–0.91 / 0.94–1.54 | 0.56 / 0.55 |
| Excluding Coors / excluding 2015 / excluding rain | 0.90 / 0.93 / 0.85 | ±0.24 each | ~0.55 |
| Day / night games | 1.03 / 0.80 | 0.62–1.43 / 0.53–1.07 | 0.55 |
| + in-park reported temperature | 0.84 | 0.61 – 1.06 | 0.55 |
| Richest temperature control | 0.69 | 0.46 – 0.92 | 0.55 |
| All ERA5 weather interpolated to the ball's inning | 1.36 | 1.13 – 1.59 | 0.56 |
| No temperature control (confounded) | 2.59 | 2.37 – 2.81 | 2.32 |
| Exit velocity (mph per +10 °C dew point) | −0.12 | −0.19 – −0.05 | 0 |
| **Placebo**: sealed dome (Tropicana), outdoor dew point | **−0.02** | −1.49 – 1.44 | 0 if sealed |
| Placebo: closed *retractable* roofs | 0.57 | 0.14 – 1.00 | 0 if sealed |

The sealed dome gives a clean null. Closed retractable roofs do not: they show a dew-point effect (and +0.67 ft per 10 °C of *outdoor* temperature), so outdoor air gets in, mostly at Chase. TrackMan's smaller coefficient fits with its physics-*projected* distances, which ignore the weather. The pre-2022 figure is below 2022+, which is the direction the physics note predicts for ball moisture before humidors. The CIs overlap, though.

## Caveats for the report

1. Present the distance result as "~0.5–1 ft per 10 °C dew point, consistent in sign and size with physics". Do not quote the +0.9 point estimate as the true effect: it moves with how temperature is measured (0.69–1.36).
2. Humidity is a **small** effect. +10 °C dew point ≈ 1/5 of +10 °C temperature, and ≈ 1.5 m/s of wind out. Do not headline "humidity → more HRs" from counts. That effect is not detectable in HR/FB.
3. Map tables: `mean_resid` per park *includes* altitude, park carry, ERA5 wind bias and the park's climate, so it is not a humidity map. Use `resid_humid_minus_dry` (within park, temperature- and wind-adjusted) for the humidity map. Per-park values are noisy (SD ≈ 1.7 ft across parks, mean +0.4), so show n. In `map_by_month.csv` the residual and adjusted-rate columns are blank on purpose: season×month FE make them 0 or 1 by construction.
4. Weather is ERA5 at about 30 km resolution and 10 m wind, not the in-bowl conditions. Wind out is +0.6 ft per m/s, far below Nathan's in-park values. Roof status is assumed open unless reported closed.
5. Model 1 is pre-registered as primary: residual ~ dew point + T + P + wind + park_period FE + season-month FE, clustered by game. Everything else is exploratory, and many specs were run.
