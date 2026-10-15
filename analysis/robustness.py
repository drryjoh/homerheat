"""Robustness of the primary humidity coefficient (ft of residual distance per +10 C dew point)."""
import pandas as pd

from analysis.expected import CONTROLS, PHYS_ELASTICITY, coef_row, fit_expected, stage2
from physics.air import air_density
from analysis.prep import COORS, RESULTS, air_balls, ball_time_weather, load_outdoor

TROPICANA = 12  # the only sealed fixed dome with many games


def _row(a, spec, term="dew_point_2m", scale=10, unit="ft per +10 C dew point", controls=CONTROLS,
         outcome="resid", phys="phys_pred"):
    f = stage2(a, term, outcome=outcome, controls=controls)
    r = coef_row(f, term, scale, spec)
    r["unit"] = unit
    r["n_games"] = a.loc[f.model.data.row_labels, "game_pk"].nunique()
    if outcome == "resid":
        r["physics_pred"] = stage2(a, term, outcome=phys, controls=controls).params[term] * scale
    return r


def run(a):
    a = ball_time_weather(a)
    a["temp_reported_c"] = (a["temp_f_reported"] - 32) * 5 / 9
    rho = air_density(a["temperature_2m_ball"] * 9 / 5 + 32, a["relative_humidity_2m_ball"] / 100,
                      a["surface_pressure_ball"] * 100)
    a["phys_pred_ball"] = PHYS_ELASTICITY * a["hit_distance_sc"].mean() * (rho / rho.mean() - 1)
    wind = "surface_pressure + wind_out + wind_rf"
    rows = [
        _row(a, "Primary (all outdoor, 2015-2025)"),
        _row(a[a["year"] < 2022], "Pre-2022 (before universal humidor)"),
        _row(a[a["year"] >= 2022], "2022+ (all parks humidor)"),
        _row(a[a["tracking"] == "trackman"], "TrackMan era 2015-2019"),
        _row(a[a["tracking"] == "hawkeye"], "Hawk-Eye era 2020-2025"),
        _row(a[a["venue_id"] != COORS], "Excluding Coors Field"),
        _row(a[a["year"] != 2015], "Excluding 2015 (EV imputation)"),
        _row(a[~a["is_raining"]], "Excluding rain-flagged games"),
        _row(a, "Vapor pressure instead of dew point", "vapor_pressure_hpa", 10, "ft per +10 hPa"),
        _row(a, "RH instead of dew point (temp controlled)", "relative_humidity_2m", 10, "ft per +10 RH pts"),
        # Temperature measurement: dew point can proxy for in-game warmth that first-pitch ERA5 T misses.
        _row(a, "+ StatsAPI in-park reported temperature", controls=f"temperature_2m + temp_reported_c + {wind}"),
        _row(a, "Richest T control (ERA5 FP x day/night + reported + ball-time T)",
             controls=f"temperature_2m * C(day_night) + temp_reported_c + temperature_2m_ball + {wind}"),
        _row(a, "All ERA5 weather interpolated to ball time (inning)", "dew_point_2m_ball",
             controls="temperature_2m_ball + surface_pressure_ball + wind_out_ball + wind_rf_ball",
             phys="phys_pred_ball"),
        _row(a[a["day_night"] == "day"], "Day games only"),
        _row(a[a["day_night"] == "night"], "Night games only"),
        _row(a, "Dew point, NO temperature control (confounded)", controls="surface_pressure + wind_out + wind_rf"),
        _row(a, "Exit velocity as outcome (ball-moisture channel)", outcome="launch_speed",
             unit="mph per +10 C dew point"),
        _row(a[a["year"] < 2022], "Exit velocity as outcome, pre-2022", outcome="launch_speed",
             unit="mph per +10 C dew point"),
    ]
    # Placebo: roof-closed games, outdoor ERA5 humidity should not reach the ball.
    closed = fit_expected(air_balls(load_outdoor("closed")))
    rows.append(_row(closed, "PLACEBO: roof-closed games (outdoor ERA5 dew point)"))
    rows.append(_row(closed[closed["venue_id"] == TROPICANA], "PLACEBO: sealed fixed dome only (Tropicana)"))
    rows.append(_row(closed[closed["venue_id"] != TROPICANA], "PLACEBO: closed retractable roofs only"))
    rows.append(_row(closed, "PLACEBO: roof-closed games, outdoor temperature", "temperature_2m", 10,
                     "ft per +10 C temperature"))
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "robustness.csv", index=False)
    return out
