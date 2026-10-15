# Physics notes: does humidity change home runs?

*Physics agent, homerheat. Code: `physics/air.py` (density), `physics/trajectory.py` (flight model, run `python physics/trajectory.py`). Figure: `physics/out/distance_vs_rh.png`.*

**Bottom line:** humid air really is lighter, so a fly ball carries a little farther. The effect is small: about **+1 to +3 ft** going from bone-dry to saturated air, against a ~415 ft home run. Temperature, altitude and wind each matter 5 to 20 times more, and humid days are also hot days.

## 1. Humid air is lighter

Treat air as an ideal gas. At a fixed temperature T and pressure P, a cubic metre holds the same number of molecules (n/V = P/RT) whether it is dry or moist. Water vapour does not get added on top. It **replaces** N2/O2 molecules, and a water molecule (M_v = 18.015 g/mol) weighs less than the average dry-air molecule (M_d = 28.965 g/mol). With vapour partial pressure e = RH x e_s(T) (Dalton's law):

    rho = [ (P - e) M_d + e M_v ] / (R T)  =  rho_dry x [ 1 - 0.378 e/P ]

Here 0.378 = 1 - M_v/M_d. The saturation pressure e_s(T) is about 1.8 kPa at 60 °F and 4.8 kPa at 90 °F (Bolton 1980), so humidity matters more on hot days.

| Change (sea level unless noted) | Air density change |
|---|---|
| 0 -> 100% RH at 60 °F | **-0.66%** |
| 0 -> 100% RH at 75 °F | **-1.11%** |
| 0 -> 100% RH at 90 °F | **-1.80%** |
| 60 °F -> 90 °F (50% RH) | -6.0% |
| Sea level -> Denver, 1600 m (75 °F, 50% RH) | -17.7% (Nathan quotes Denver air at ~82% of sea level) |

So the largest humidity swing possible is worth about one-third of an ordinary 30 °F temperature swing, and about a tenth of the Coors Field effect.

## 2. Trajectory model and results

**Reference (no air):** x(t) = v0 cos(theta) t, y(t) = h0 + v0 sin(theta) t - g t^2/2. For 103 mph at 28° from 3 ft, the ball lands at **593 ft**. Real home runs land near 400 ft, so the air removes roughly a third of the range. That is why density matters at all.

**With air (2D point mass):**

    m dv/dt = -1/2 rho C_d A |v| v   +   1/2 rho C_L A |v|^2 n_perp   -   m g

- Ball: m = 0.145 kg, circumference 9.125 in, so A = 42.7 cm².
- C_d = 0.35 (the value used with Nathan's trajectory calculator).
- C_L = 0.20, held constant. At 103 mph this is roughly 2000 rpm of backspin (spin parameter ~0.17), which falls inside the range Nathan et al. (2006) measured.
- Launch: 103 mph exit velocity, 28°, 3 ft. This is the "typical home run" launch from Nathan's temperature note.
- The model leaves out wind, spin decay and any change of C_d with speed. It is a lever for estimating sensitivity, not a distance predictor.

**Carry distance (ft) vs relative humidity, sea level:**

| RH | 60 °F | 75 °F | 90 °F |
|---|---|---|---|
| 0% | 411.0 | 415.4 | 419.6 |
| 50% | 411.5 | 416.2 | 420.9 |
| 100% | 412.0 | 417.1 | 422.3 |
| **0->100% RH** | **+1.0 ft** | **+1.7 ft** | **+2.7 ft** |

**Sensitivity:** **-1.5 ft per +1% air density** (distance changes about 0.37% for each 1% change in density, around 75 °F and 50% RH).

**Check against published values (Nathan's Statcast-tuned model):**

| Effect | This model | Literature |
|---|---|---|
| RH 25% -> 75% at 75 °F | +0.8 ft | +0.9 ft (Nathan 2016) |
| +10 °F | +3.1 ft | +3.3 ft (2016); 0.33 ft/°F (2017); "4-5 ft" (Illinois Q&A) |
| +1000 ft elevation | +5.5 ft | +5.9 ft |
| Sea level -> Denver | +28 ft (+6.8%) | +29 ft in 2015 Statcast data (430 vs 401 ft); "~5%" (Denver page) |

The simple model agrees with the published values to within about 10%. That is good enough for effect-size planning.

## 3. Expected effect on distance and HR rate

Home runs sit on the steep tail of the fly-ball distance distribution, so a small shift in distance moves a lot of balls across the fence. Published conversions:

- Nathan (2011, humidor study): **1 ft ≈ 2.3%** change in HR probability.
- Nathan (2017, temperature note, from 2015-17 Statcast): an 8.5 ft shift gives +25% HR, so **1 ft ≈ 3%**. That implies ~1% more HR per °F. Rob Arthur's empirical estimate is ~0.8% per °F.
- Older figure: Adair says +7% HR per 1% of distance. Nathan argues this is too low by about 2x.

(The "~1.5-2% per ft" figure in our brief is a bit below these. We use **2-3% per ft**.)

| Scenario (75 °F, sea level) | Δ distance | Δ HR rate |
|---|---|---|
| 0 -> 100% RH (extreme, unphysical in a ballpark) | +1.7 ft | **+4-5%** |
| Dry third vs humid third of games (~40 RH points apart) | +0.7 ft | **+1.5-2%** |
| For comparison: +10 °F | +3.1 ft | +7-10% |
| For comparison: humidor at Coors (ball stored 30% -> 50% RH) | -13 ft | -25 to -30% |

**Target the data must detect:** about **0.5-1 ft** in distance, or about **1.5-2% in HR rate**, between realistically dry and humid games, *after* temperature has been removed.

## 4. Confounders and skepticism

1. **Temperature (the dominant confound).** Humid summer days are hot days, and hot air is also thin. Temperature is worth 0.33 ft per °F, so a 2 °F error in the temperature adjustment is as large as the whole humidity signal. Fix: model **air density computed from T, P and RH together**, then test whether the humidity part of density has the slope physics predicts. Do not use raw RH in a regression alongside temperature.
2. **Humidor and ball moisture (opposite sign, larger, slower).** A ball that has absorbed moisture is heavier (+1.6%) and less bouncy (COR -3.7% for 30 -> 50% storage RH). Exit velocity drops by about 2.8 mph, about 13 ft of distance (Nathan 2011). This acts over days to weeks of storage, not on game day. Before humidors, balls in humid climates soaked up moisture, which predicts *fewer* HRs where it is humid. That is the opposite of the air effect. Humidors spread from Colorado (2002) to Arizona (2019) and 10 parks (2021). From 2022, all 30 parks must store balls ≥14 days in a humidor, with ≤2 h out before first pitch. Suggested fixes:
   - Split the data at 2022, and by park humidor status.
   - In distance analyses, control for measured exit velocity. That absorbs the COR effect. HR-count analyses cannot do this.
3. **Rain and wet balls.** Wet grip, wet balls and heavy air lead to delays and to different pitchers. Exclude rain-affected games or flag them. Rain also marks fronts that bring wind shifts.
4. **Wind.** An out-blowing wind of 5 mph adds about 19 ft, more than 10x the entire humidity effect. Wind is noisy and rarely measured well. It is the main source of game-level noise, and it correlates with weather systems that also carry humidity.
5. **Pressure and altitude.** About 6 ft per 1000 ft of elevation. Use station pressure, or park fixed effects. Coors alone can dominate a pooled fit.
6. **Domes and roofs.** Indoor conditions are not the outdoor weather. Drop these games, or use them as a placebo (no humidity effect should appear).
7. **Season and time of day.** Humidity tracks month and day versus night, and those also track player fatigue, roster changes and the ball's year-to-year drag (the 2016-19 "juiced"/low-drag balls changed carry by several feet). Use season and month fixed effects.

**Power (back of envelope).** These numbers rest on assumptions, stated here:

- Data: ~6,000 HR per year over 10 years gives N ≈ 60k HR. Using all well-hit fly balls (EV > 95 mph, LA 20-40°) gives several times more.
- Noise: residual distance SD after controlling for EV and launch angle is 10-15 ft (12 ft used).
- Comparison: dry third vs humid third of games.

Results:

- **Independent balls:** minimum detectable effect (80% power, α = 0.05) is **0.3-0.45 ft**.
- **Clustered by game** (weather is shared within a game). Assume a 5 ft game-level carry SD from wind and similar effects, ~2.5 HR per game, and ~20k games. The detectable gap is **≈0.45 ft**. As a regression on RH (SD of game RH ≈ 18 points), the detectable slope is **≈1.0 ft per 100% RH**.
- **HR counts only:** comparing ~20k HR per tercile, the MDE is **≈2.8%** in HR rate, before any overdispersion.

**Verdict:** the predicted +0.7 ft (+1.5-2% HR) is *just* detectable in Statcast distances with careful controls. It is **not** reliably detectable in HR counts alone. A clean "humidity -> more HRs" headline from HR counts would more likely reflect a confound than physics.

## 5. What the data must show to be believable

1. **Right sign and size.** Carry should rise by ~1-3 ft from dry to saturated air at fixed T (larger on hot days). An effect of 10 ft or more is not humidity.
2. **Consistency with density.** The humidity effect should fit on the same distance-vs-density line as temperature and altitude, at about -1.5 ft per 1% density. If humidity seems to matter "more than its density," look for a confound.
3. **Shows up in distance and EV-controlled carry, not only in HR counts.**
4. **Robust to splits:** pre- vs post-2022 humidors (any pre-2022 ball-moisture effect should have the *opposite* sign), outdoor vs dome (no effect indoors), and within park, comparing day to day (park fixed effects).
5. **Survives temperature control.** Ideally there is a dose-response in the vapour-pressure part of density (0.378 e/P), not in raw RH.

## References (URLs checked Oct 2026)

- A. M. Nathan, *Using Statcast Data to Study the Flight of a Baseball* (2016). Source for the +0.9 ft RH, 3.3 ft/10 °F, 5.9 ft/1000 ft, 18.8 ft/5 mph wind and Denver 430 vs 401 ft figures. https://baseball.physics.illinois.edu/THT-Fly-Ball-Distances-Statcast.pdf
- A. M. Nathan, *Effect of Temperature on Home Run Production* (2017). Source for 0.33 ft/°F, the 103 mph/28° launch, 8.5 ft → +25% HR and ~1%/°F. https://baseball.physics.illinois.edu/Effect%20of%20Temperature%20on%20Home%20Run%20Production.pdf
- A. M. Nathan, *Home Runs and Humidors: Is There a Connection?* Baseball Prospectus (2011). Source for COR -3.7%, mass +1.6%, -2.8 mph, -13 ft, 2.3%/ft. https://www.baseballprospectus.com/news/article/13057/baseball-proguestus-home-runs-and-humidors-is-there-a-connection/
- A. M. Nathan, *Baseball at High Altitude*. Source for Denver air at ~82% density, fly balls ~5% farther, and "humid air is less dense". https://baseball.physics.illinois.edu/Denver.html
- A. M. Nathan, *Baseball Aerodynamics* page, with links to the trajectory calculator. https://baseball.physics.illinois.edu/aero.html
- Illinois Physics Van "Ask the Van": *The Best Temperature for a Home-Run* (Nathan: 4-5 ft per 10 °F). https://van.physics.illinois.edu/ask/listing/938
- A. M. Nathan et al., *The Effect of Spin on the Flight of a Baseball* (2006). Measured C_L and C_D. https://arxiv.org/abs/physics/0605041
- SABR, *Alan Nathan on Humidors and Home Runs* (2011). Coors HR per game down 25% after the humidor. https://sabr.org/latest/alan-nathan-on-humidors-and-home-runs/
- AP (via KSAT), *MLB standardizing ball rubbing and removal from humidors* (June 2022). All 30 parks, ≥14 days storage, ≤2 h out. https://www.ksat.com/sports/2022/06/21/mlb-standardizing-ball-rubbing-and-removal-from-humidors/
- D. Bolton, *The Computation of Equivalent Potential Temperature*, Mon. Wea. Rev. 108 (1980). Saturation vapour pressure formula. https://doi.org/10.1175/1520-0493(1980)108<1046:TCOEPT>2.0.CO;2
