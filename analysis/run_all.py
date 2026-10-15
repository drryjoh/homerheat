"""Run the whole normalization/statistics pipeline and print a summary.

    .venv/bin/python -m analysis.run_all        (from repo root; ~10 min)
"""
import warnings

import pandas as pd

from analysis import expected, hr_rate, rain, robustness, tables
from analysis.prep import RESULTS, air_balls, load_outdoor

warnings.filterwarnings("ignore")
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 60)


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    print("[1/5] primary distance-residual model")
    a, dist, terc = expected.run()
    bb = load_outdoor()
    print(dist[["model", "estimate", "ci_low", "ci_high", "p", "physics_pred", "n", "n_games"]].round(3))
    print(terc[["model", "estimate", "ci_low", "ci_high", "raw_resid_diff", "raw_distance_diff"]].round(3))

    print("[2/5] HR probability models")
    hr = hr_rate.run(a)
    print(hr[["model", "pct_change", "ci_low", "ci_high", "p", "n", "n_hr"]].round(3))

    print("[3/5] rain")
    r = rain.run(a)
    print(r[["label", "resid_ft", "resid_ci_low", "resid_ci_high", "hr_pct", "hr_ci_low", "hr_ci_high",
             "n_games_rain", "n_balls_rain"]].round(3))

    print("[4/5] robustness")
    rb = robustness.run(a)
    print(rb[["model", "estimate", "ci_low", "ci_high", "p", "physics_pred", "unit", "n", "n_games"]].round(3))

    print("[5/5] map + binned tables")
    fit = expected.stage2(a)
    dew, rh = tables.run(bb, a, fit)
    print(dew[["bin", "n_balls", "mean_distance", "mean_resid", "adj_effect", "adj_ci_low", "adj_ci_high",
               "physics_effect"]].round(2))
    print("results in", RESULTS)


if __name__ == "__main__":
    main()
