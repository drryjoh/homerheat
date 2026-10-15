# Baseball domain notes: humidity and home runs

For the normalizing and report agents. Bottom line: **humid air should help fly balls only a little. Moist air is less dense, but the drop is small, and era, park, temperature, wind and batter quality can each swamp it.** Design the analysis so that a null result counts as a real finding.

## 1. Prior work: what is known about humidity

- **Physics of humid air.** Water vapor (18 g/mol) displaces N2/O2 (~29 g/mol), so humid air is *less* dense: Δρ/ρ ≈ −0.378·e/p, where e is vapor pressure. A swing from bone-dry to saturated at 30 °C (e ≈ 42 hPa) is about −1.6% density, the same as ~5 °C of warming. Realistic game-to-game dew-point swings at a fixed temperature move density about 0.5–0.8%, which is roughly 1–2 ft on a 400-ft fly ball. Alan Nathan's estimate: "a 50 percent increase in relative humidity will increase the distance by roughly one foot", versus "a 10 degree [F] change in temperature … a little over three feet" and "a five mile an hour wind … blowing out will increase the carry … by like 18 or 20 feet" ([PopSci](https://www.popsci.com/best-weather-for-hitting-home-run-baseball/)).
- **Nathan 2012 (Baseball Prospectus).** Distance slope is about 0.25 ft/°F, and +10 °F gives about 6% more HRs. He judged humidity "rather weak" and left it out ([BP](https://www.baseballprospectus.com/?p=17249)).
- **Humidity in the *ball* is a different and larger effect, with the opposite sign.** Nathan, Smith, Faber & Russell (2011) measured it: going from 30% to 50% RH storage cuts the ball's bounciness (COR) by ~4.5%, which costs ~2.5 mph of exit velocity, ~14 ft of distance and ~25% of HR probability. Moist air's own aerodynamic gain over that range is only ~2 ft "in the wrong direction" ([arXiv 1009.2549](https://ar5iv.arxiv.org/html/1009.2549)). The Coors humidor (since 2002, stores balls at 50% RH) cut HR/game by 25% (3.20 to 2.39, 2002–10), close to the predicted 27±4% ([Nathan, THT 2017](https://tht.fangraphs.com/a-humidor-at-chase-field-whats-up-with-that)). **Implication:** before humidors, balls stored in a humid climate were heavier and deader, so humid parks could show *fewer* HRs even though humid air helps carry. That effect is lagged by days, because balls take days to equilibrate.
- **Altitude.** Denver's air is ~80% as dense as at sea level ([arXiv 1009.2549](https://ar5iv.arxiv.org/html/1009.2549)). Chambers, Page & Zaidins (Colorado) found that at Coors **wind, especially the E–W component, was the only statistically significant weather variable** for fly-ball distance. It explained ~20% of the variance ([SABR](https://sabr.org/journal/article/into-thin-air-whats-all-the-fuss-about-coors-field/)).
- **Callahan, Dominy, DeSilva & Mankin (BAMS 2023, Dartmouth).** ~2% more HRs per +1 °C of daily maximum temperature, 2.4% in day games versus 1.7% at night. They used open-air or roof-open games: >100k games (1962–2019) plus >220k Statcast batted balls (2015–19). The effect held when comparing balls with the same exit velocity and launch angle. Humidity was not studied ([Eos](https://eos.org/?p=208091), [Dartmouth](https://geography.dartmouth.edu/news/2023/04/climate-crisis-causing-more-home-runs-baseball), [WQLN/NPR](https://www.wqln.org/2023-04-07/warmer-temperatures-may-be-linked-to-a-rise-in-baseball-home-runs-study-finds)).
- **Practitioner claims.** One DFS writer claims "HR rates increase by 20% when the dewpoint is over 70 at Citi Field" ([RotoGrinders](https://rotogrinders.com/articles/mlb-weather-101-why-weather-matters-in-mlb-dfs-3008754)). That is anecdotal, confounded with temperature, and an order of magnitude above the physics.

**Prior ranking of effect sizes:** altitude >> wind > temperature >> humid air. Ball storage humidity (pre-2022) is large but works through the ball, not the air.

## 2. Era effects that dwarf weather

League HR totals ([Baseball-Reference](https://www.baseball-reference.com/leagues/majors/bat.shtml)): 2015 4,909 · 2016 5,610 · 2017 6,105 · 2018 5,585 · **2019 6,776 (record)** · 2020 2,304 (60 games) · 2021 5,944 · 2022 5,215 · 2023 5,868 · 2024 5,453 · 2025 5,650. Year-to-year swings of ±15–20% are about 10× any plausible humidity effect.

- **2015–19 surge.** MLB's Nathan-chaired committee blamed lower ball drag (~60% of the 2018–19 rise) plus launch-angle changes (~40%) ([MLB.com](https://www.mlb.com/news/mlb-releases-independent-study-of-home-run-surge)). Drag varied within seasons and between ball lots.
- **2021 deadened ball.** COR was lowered 0.01–0.02 and the ball made 2.8 g lighter, for ~1–2 ft less on 375+ ft fly balls. Some 2021 games may have used both old and new balls ([CBS](https://www.cbssports.com/mlb/news/mlb-planning-small-changes-to-deaden-the-baseball-for-2021-season-per-report/), [FanGraphs](https://blogs.fangraphs.com/an-early-look-at-the-new-baseball/)).
- **Humidors.** COL from 2002; ARI 2018 (some sources say 2019; verify); 3 more parks in 2020; 10 in 2021; **all 30 in 2022** ([KING5/AP](https://king5.com/article/sports/mlb-humidors-weather-impact-baseballs/281-bc328573-2988-426c-bb21-d82fd6d7345d)). This is a direct confound for humidity: once humidors were in place, local humidity no longer reached the ball.
- **2020.** A 60-game season with no fans, regional schedules (so a different mix of opponent parks) and a July–Sept calendar (no cold April/May games). **Statcast moved from TrackMan radar to Hawk-Eye optical tracking** ([builtin](https://builtin.com/consumer-tech/mlb-statcast-tech-update-hawk-eye-integration)). Distances were partly *projected* by physics under TrackMan when radar lost the ball ([NY Post/Tango](https://www.pressreader.com/usa/new-york-post/20170613/282767766586669)). I found no public study of a distance level shift at the switch, so **treat 2020 as a measurement break.**
- **2015 Statcast gaps.** 25% of batted balls lacked exit velocity by the 2015 All-Star break, mostly popups and weak grounders, and SF was worst at 38% ([FanGraphs](https://blogs.fangraphs.com/the-limitations-of-the-statcast-data)). From 2016 on, missing values were imputed. Flag imputed rows if you can identify them, or drop 2015 for the EV/LA models.
- **2023 rules** (pitch clock, shift ban, 18-in bases, pickoff limits) ([ESPN](https://www.espn.com.au/mlb/story/_/id/35629997/mlb-new-2023-season-rules-shift-pitch-clock)). These affect the batted-ball mix and approach more than carry, but they still require season effects.

## 3. Park units (park × period = separate unit)

Verified changes:
- **MIA Marlins/loanDepot park:** 2016 (CF 418→407, walls 11.5→7 ft) and a second move-in (CF 407→400, RC 399→387, described only as "the 2020 offseason", so the start year, 2020 or 2021, is unverified: check HR/FB at MIA by year) ([MLB.com](https://www.mlb.com/news/fences-being-moved-in-lowered-at-marlins-park-c162809448), [Ballpark Digest](https://ballparkdigest.com/2015/12/11/marlins-to-move-in-fences-for-2016/)).
- **NYM Citi:** 2015 (RF/RC moved in) and 2023 (RF ~8 ft in) ([SI/AP](https://www.si.com/mlb/2014/11/18/ap-bbn-citi-field), [Ballpark Digest](https://ballparkdigest.com/2022/11/11/mets-tigers-reportedly-looking-at-2023-ballpark-changes/)).
- **SF Oracle:** 2020 (CF 399→391, Triples Alley 421→415, bullpens moved) ([Ballpark Digest](https://ballparkdigest.com/2019/12/13/giants-unveil-2020-oracle-park-dimensions/)).
- **BAL Camden:** 2022 (LF ~30 ft deeper and 13 ft high) and 2025 (pulled in 9–20 ft, lowered) ([MLB.com](https://www.mlb.com/orioles/news/orioles-camden-yards-left-field-wall-modifications)).
- **TOR Rogers Centre:** 2023 (alleys in, walls raised) ([CBS](https://www.cbssports.com/mlb/news/blue-jays-to-move-fences-in-at-rogers-centre-but-raise-walls-per-report/)).
- **DET Comerica:** 2023 (CF 10 ft in, walls to 7 ft) ([MLB.com](https://www.mlb.com/tigers/news/tigers-changing-outfield-dimensions-at-comerica-park)).
- **KC Kauffman:** 2026 (out of scope) ([MLB.com](https://www.mlb.com/news/royals-moving-outfield-walls-at-kauffman-stadium)).

Moves, temporary venues and special sites:
- New stadiums: TEX Globe Life Park (open air, 2015–19) → Globe Life Field (retractable, 2020+). ATL Turner Field → Truist Park (2017).
- **OAK Coliseum → Sutter Health Park, Sacramento (2025, AAA park, HR factor ~112 versus Coliseum ~84)** ([AOL/Yahoo](https://www.aol.com/sports/key-stats-every-american-league-144208657.html)).
- **TB Tropicana (fixed dome) → Steinbrenner Field, Tampa (2025, open air, Yankee Stadium dimensions, hot and humid; played big at night)** ([MLB.com](https://www.mlb.com/news/rays-steinbrenner-field-2025-season), [ESPN](https://africa.espn.com/flb/story/_/id/45140863/fantasy-baseball-mlb-espn-trends-25-percent-stats-matchups-exploit-14-2025)). This is the cleanest humid-outdoor natural experiment in the dataset, but it has n = 1 season.
- TOR home games in Buffalo (2020, part of 2021) and Dunedin (2021), from memory.
- **Drop** neutral and special sites: London, Mexico City/Monterrey, Tokyo, Seoul, Field of Dreams, Rickwood, Williamsport, Fort Bragg and Bristol. Key on the game's `venue_id` from the MLB Stats API, not on `home_team`.

**Roofs:**
- Retractable: ARI, HOU, MIA, MIL, TOR, TEX (2020+).
- SEA has a roof that covers the field but leaves the sides open, so the air is outdoor air.
- Fixed dome: TB Tropicana.
- Roof status per game is in the MLB Stats API `gameData.weather.condition` field ("Roof Closed", "Dome"). Exclude closed-roof games from the weather analysis, or use them as a **placebo** where ERA5 humidity should show no effect.

Altitude outliers: Coors (~5,200 ft) and Chase (~1,100 ft). Analyze with Coors excluded as a robustness check.

## 4. Team-quality bias: normalizations, from most to least trusted

1. **Distance residual (my top choice).** Model `hit_distance_sc` as a smooth function of exit velocity, launch angle and spray angle (GAM or gradient boosting, fit separately for TrackMan 2015–19 and Hawk-Eye 2020+), with **season (ideally month) fixed effects** for the ball. Then regress the residual on weather. EV and LA absorb most batter and pitcher quality. Restrict to **fly balls / line drives with LA 20–40° and EV ≥ 90 mph**: humid air can only matter there, and grounders add noise. Callahan et al. used this same check.
2. **P(HR | EV, LA, spray, park-period).** A logistic model on the same batted-ball set captures fence geometry, which the distance model ignores.
3. **Rate models with fixed effects.** Use HR per fly ball (or per batted ball with LA > 10°), never HR/game. Include park-period × season FE and month FE. Add batter FE or the batter's season HR/PA (leave-one-out), and the pitcher's HR/FB allowed, as covariates. This model is the one most exposed to selection on approach and lineup construction.

Never compare raw HR counts across teams or parks. The home team's hitters appear in about half the sample at every park, so park and team-roster power are confounded unless there are batter terms.

## 5. Seasonal and geographic structure and the map

Humidity, temperature, month and region co-vary: the Southeast is humid and hot, July–Aug is humid and hot, and the domes cluster in hot or humid cities (MIA, HOU, TB, TEX, ARI). A raw "HRs by state × month" map will show park factors (Coors, GABP, Yankee Stadium), season length and temperature. Recommendations:
- Map the **mean distance residual** from §4.1 (in feet) per park, ideally as a **partial residual after temperature and wind**, with n and a CI encoded.
- Alternatively map **HR/FB relative to the park-period's own average**, for example deviation in humid versus dry games within the same park-month.
- Show one point per stadium, not state choropleths: states have 0–2 parks, and the shading misleads.
- Gray out or omit domes and closed-roof games.
- Use a diverging scale centered at 0, and put the physics-predicted map (from the density formula) next to it.

## 6. Skeptic's checklist

1. **RH–temperature collinearity.** RH falls as the day heats up while dew point stays flat. **Use vapor pressure or dew point (or computed air density) plus temperature and pressure, not RH alone.** Test whether humidity has an effect *beyond* its density contribution (physics predicts ≈0.378·e/p).
2. **ERA5 grid (~31 km) versus the stadium.** Coastal parks (SF, SD, SEA, BOS) have marine layers and sea breezes the grid smooths out. Elevation must match the stadium (Denver), so correct pressure to stadium altitude.
3. **Timing.** First-pitch weather versus the inning of the HR: a 3-hour game spans the diurnal cycle, so interpolate hourly ERA5 to the estimated pitch time.
4. **Roof misclassification**, including roofs opened or closed mid-game and SEA's semi-open roof.
5. **Wind is the biggest omitted variable.** Include ERA5 10 m u/v projected onto each park's center-field bearing, while noting that 10 m grid wind ≠ in-bowl wind.
6. **Selection.** Distance is observed for every tracked batted ball, so don't condition on HR. Also, launch decisions may respond to conditions.
7. **Ball-storage humidity** before full humidor rollout (≤2021) works in the opposite direction from air humidity, and with a lag. Split pre- and post-2022.
8. **Measurement breaks**: 2015 missing and imputed EV, the 2020 TrackMan→Hawk-Eye switch, and possible park-specific calibration.
9. **Era and ball-lot drift within seasons**: use month × season FE, not just season.
10. **Multiple comparisons** across humidity metrics, outcomes, parks and subsets. Pre-register one primary model (distance residual ~ vapor pressure + temp + pressure + wind, park-period & season-month FE, clustered by game) and label everything else exploratory.
11. **Clustering.** Batted balls within a game share the same weather, so the effective n is games (~24k), not ~1M balls. Cluster standard errors by game, or by park-date.
12. **Power.** The expected effect is about 1 ft, so check the minimum detectable effect before interpreting a null. Use closed-roof games as a placebo and Coors as a sanity check, since its density effect should be large and visible.
