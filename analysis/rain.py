"""Rain (user question 3): distance residual and HR rate in rain-flagged games.

Each flag enters the primary specs as a dummy alongside dew point, temperature, pressure, wind and FE.
Flags: StatsAPI condition Rain/Drizzle (strict, reported at first pitch); ERA5 precipitation > 0.1 mm/h
(noisy, drizzle-biased); ERA5 > 1 mm/h (moderate rain); the dataset's combined is_raining (either).
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm

from analysis.expected import CONTROLS, FE, coef_row, stage2
from analysis.hr_rate import LAUNCH, glm_cluster
from analysis.prep import RESULTS

FLAGS = {
    "rain_statsapi": "StatsAPI condition Rain/Drizzle (strict)",
    "rain_era5": "ERA5 precip > 0.1 mm/h",
    "rain_era5_1mm": "ERA5 precip > 1 mm/h",
    "is_raining": "combined is_raining (either source)",
}


def run(a):
    a = a.assign(rain_era5_1mm=a["precipitation"] > 1.0, is_hr_i=a["is_hr"].astype(int))
    rows = []
    for flag, label in FLAGS.items():
        a[flag + "_i"] = a[flag].astype(int)
        f = stage2(a, f"{flag}_i + dew_point_2m")
        r = coef_row(f, f"{flag}_i", 1, label)
        lg = glm_cluster(f"is_hr_i ~ {LAUNCH} + {flag}_i + dew_point_2m + {CONTROLS} + {FE}", a,
                         sm.families.Binomial())
        p = lg.fittedvalues
        k = float((p * (1 - p)).sum() / p.sum())
        b, se = lg.params[f"{flag}_i"], lg.bse[f"{flag}_i"]
        sub = a[a[flag]]
        rows.append(dict(
            flag=flag, label=label,
            resid_ft=r["estimate"], resid_ci_low=r["ci_low"], resid_ci_high=r["ci_high"], resid_p=r["p"],
            hr_pct=100 * (np.exp(k * b) - 1), hr_ci_low=100 * (np.exp(k * (b - 1.96 * se)) - 1),
            hr_ci_high=100 * (np.exp(k * (b + 1.96 * se)) - 1), hr_p=lg.pvalues[f"{flag}_i"],
            raw_resid_rain=sub["resid"].mean(), raw_resid_dry=a.loc[~a[flag], "resid"].mean(),
            raw_hr_rate_rain=sub["is_hr"].mean(), raw_hr_rate_dry=a.loc[~a[flag], "is_hr"].mean(),
            n_games_rain=sub["game_pk"].nunique(), n_balls_rain=len(sub),
            n_hr_rain=int(sub["is_hr"].sum()), n_games_total=a["game_pk"].nunique()))
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "rain.csv", index=False)
    return out
