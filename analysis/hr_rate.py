"""SECONDARY model: home-run probability.

(a) Ball-level logit on air balls: is_hr ~ EV x LA splines + pull splines + weather
    + park_period FE + season x month FE, SEs clustered by game.
(b) Game-level Poisson: n_hr ~ weather + park_period FE + season x month FE
    + home team-season FE + away team-season FE, offset log(n_fly_balls), clustered by game.
Team quality: (a) conditions on each ball's exit velocity / launch angle / spray, so a strong
lineup's harder contact is in the expected part, not the weather part. (b) has no launch data,
so it uses home and away team-season FE to absorb roster power/pitching quality instead.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from analysis.expected import CONTROLS, FE
from analysis.prep import RESULTS, load_games

LAUNCH = ("bs(launch_speed, df=6) * bs(launch_angle, df=6) + bs(pull, df=6)"
          " + bs(pull, df=4):launch_angle")


def glm_cluster(formula, df, family, offset=None, cluster="game_pk"):
    return smf.glm(formula, df, family=family, offset=offset).fit(
        maxiter=200, cov_type="cluster", cov_kwds={"groups": df[cluster].astype(int)})


def pct_row(fit, term, scale, label, **extra):
    b, se = fit.params[term] * scale, fit.bse[term] * scale
    pct = lambda x: 100 * (np.exp(x) - 1)
    return dict(model=label, term=term, pct_change=pct(b), ci_low=pct(b - 1.96 * se),
                ci_high=pct(b + 1.96 * se), log_coef=b, se=se, p=fit.pvalues[term],
                n=int(fit.nobs), **extra)


def logit_models(a):
    """Odds ratios conditional on launch are not HR-rate changes (many air balls have p near 0 or 1).
    We also report the implied % change in the expected HR count: d log(sum p) = k * d logit,
    k = sum p(1-p) / sum p (average-marginal-effect linearisation)."""
    rows = []
    a = a.assign(is_hr=a["is_hr"].astype(int))
    fam = sm.families.Binomial()
    terc = "C(humid_tercile, Treatment('dry'))"
    f = glm_cluster(f"is_hr ~ {LAUNCH} + {terc} + {CONTROLS} + {FE}", a, fam)
    p = f.fittedvalues
    k = float((p * (1 - p)).sum() / p.sum())
    rows.append(pct_row(f, f"{terc}[T.humid]", 1, "logit: humid vs dry tercile"))
    rows.append(pct_row(f, f"{terc}[T.mid]", 1, "logit: mid vs dry tercile"))
    f = glm_cluster(f"is_hr ~ {LAUNCH} + dew_point_2m + {CONTROLS} + {FE}", a, fam)
    rows.append(pct_row(f, "dew_point_2m", 10, "logit: per +10 C dew point"))
    rows.append(pct_row(f, "temperature_2m", 10, "logit: per +10 C temperature"))
    rows.append(pct_row(f, "wind_out", 1, "logit: per +1 m/s wind out"))
    out = pd.DataFrame(rows).rename(columns={"pct_change": "odds_pct", "ci_low": "odds_ci_low",
                                             "ci_high": "odds_ci_high"})
    pct = lambda x: 100 * (np.exp(k * x) - 1)
    out["pct_change"] = pct(out["log_coef"])
    out["ci_low"] = pct(out["log_coef"] - 1.96 * out["se"])
    out["ci_high"] = pct(out["log_coef"] + 1.96 * out["se"])
    out["k_ame"] = k
    out["n_games"] = a["game_pk"].nunique()
    out["n_hr"] = int(a["is_hr"].sum())
    return out


def poisson_models(g):
    """Game-level HR per fly ball. Two FE sets, to show what team-quality FE change:
    'park+season-month': park_period + season x month FE only;
    'team-season': home team-season x park_period FE + away team-season FE + month-of-year FE.
    (Home team-season is nested in park, and home/away team-season dummies both sum to the season
    indicator, so the team spec folds park into home FE, uses one reference away team per season,
    and month-of-year in place of season x month. Continuous covariates are centered so IRLS converges.)"""
    need = ["n_hr", "n_fly_balls", "dew_point_2m", "temperature_2m", "surface_pressure", "wind_out",
            "wind_rf", "humid_tercile"]
    g = g.dropna(subset=need)
    g = g[g["n_fly_balls"] > 0].copy()
    g["n_hr"] = g["n_hr"].astype(float)
    g["home_tsp"] = g["home_team_abbr"] + g["season"].astype(str) + "|" + g["park_period"]
    # Drop tiny cells (2020-21 "home" games in another team's park, a few games each).
    g = g[g.groupby("home_tsp")["game_pk"].transform("size") >= 20].copy()
    for c in ["dew_point_2m", "temperature_2m", "surface_pressure"]:
        g[c] = g[c] - g[c].mean()
    ref = g.groupby("season")["away_team_abbr"].transform("min")
    g["away_ts"] = np.where(g["away_team_abbr"] == ref, "ref", g["away_team_abbr"] + g["season"].astype(str))
    off = np.log(g["n_fly_balls"].to_numpy(dtype=float))
    fes = {"park+season-month FE": FE,
           "team-season FE": "C(month) + C(home_tsp) + C(away_ts)"}
    terc = "C(humid_tercile, Treatment('dry'))"
    rows = []
    for fe_name, fe in fes.items():
        f = glm_cluster(f"n_hr ~ dew_point_2m + {CONTROLS} + {fe}", g, sm.families.Poisson(), offset=off)
        rows.append(pct_row(f, "dew_point_2m", 10, f"Poisson ({fe_name}): per +10 C dew point, % HR/FB"))
        rows.append(pct_row(f, "temperature_2m", 10, f"Poisson ({fe_name}): per +10 C temperature, % HR/FB"))
        f = glm_cluster(f"n_hr ~ {terc} + {CONTROLS} + {fe}", g, sm.families.Poisson(), offset=off)
        rows.append(pct_row(f, f"{terc}[T.humid]", 1, f"Poisson ({fe_name}): humid vs dry tercile, % HR/FB"))
        rows[-1]["converged"] = f.converged
    out = pd.DataFrame(rows)
    out["n_games"] = len(g)
    out["n_hr"] = int(g["n_hr"].sum())
    return out


def baseline_hr_prob(a):
    """P(HR | EV, LA, spray, season-month) with NO park or weather terms.
    Used for the map: observed/expected HRs per park = park + weather effect net of batted-ball quality."""
    a = a.assign(is_hr=a["is_hr"].astype(int))
    f = smf.glm(f"is_hr ~ {LAUNCH} + C(season_month)", a, family=sm.families.Binomial()).fit()
    return f.fittedvalues


def run(a=None):
    if a is None:
        from analysis.expected import fit_expected
        from analysis.prep import air_balls, load_outdoor
        a = fit_expected(air_balls(load_outdoor()))
    out = pd.concat([logit_models(a), poisson_models(load_games(True))], ignore_index=True)
    out["outcome"] = np.where(out["model"].str.startswith("logit"),
                              "% change in expected HR count among air balls (EV/LA-adjusted)",
                              "% change in HR per fly ball (game level)")
    out.to_csv(RESULTS / "hr_model.csv", index=False)
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    print(run()[["model", "pct_change", "ci_low", "ci_high", "p", "n", "n_games"]].round(3))
