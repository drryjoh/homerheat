"""Map-ready and figure-ready tables.

map_by_park.csv, map_by_month.csv, map_by_park_month.csv : one row per unit (see notes/normalization.md)
binned_dewpoint.csv, binned_rh.csv : residual / raw distance vs humidity bins with game-clustered 95% CIs
"""
import numpy as np
import pandas as pd

from analysis.expected import CONTROLS, FE, ols_cluster
from analysis.hr_rate import baseline_hr_prob
from analysis.prep import RESULTS


def clustered_mean(x, groups):
    """Mean and game-clustered SE of a mean."""
    x = np.asarray(x, float)
    if len(x) < 2:
        return np.nan, np.nan
    dev = pd.Series(x - x.mean()).groupby(np.asarray(groups)).sum()
    return x.mean(), np.sqrt((dev ** 2).sum()) / len(x)


def _summ(bb, a, keys):
    """Aggregate all-BIP (bb) and air-ball (a) stats by keys."""
    bb = bb.assign(hr_dist=bb["hit_distance_sc"].where(bb["is_hr"]))
    fb = bb[bb["is_fly_ball"]]
    t = bb.groupby(keys).agg(
        n_games=("game_pk", "nunique"), n_bip=("is_hr", "size"), n_hr=("is_hr", "sum"),
        mean_hr_distance=("hr_dist", "mean"), mean_dew_point=("dew_point_2m", "mean"),
        mean_rh=("relative_humidity_2m", "mean"), mean_temp_c=("temperature_2m", "mean"))
    t["hr_per_100_bip"] = 100 * t["n_hr"] / t["n_bip"]
    f = fb.groupby(keys).agg(n_fly=("is_hr", "size"), fb_hr=("is_hr", "sum"), fb_exp=("lg_fb_rate", "sum"))
    t["hr_per_fb"] = f["fb_hr"] / f["n_fly"]
    t["hr_per_fb_rel_league"] = f["fb_hr"] / f["fb_exp"]   # 1.0 = league (same-season) average
    t["n_fly"] = f["n_fly"]
    g = a.groupby(keys)
    t["n_air"] = g.size()
    # Adjusted HR rate: observed / expected from EV, LA, spray, season-month (no park, no weather).
    t["adj_hr_ratio"] = g["is_hr"].sum() / g["p_base"].sum()
    t["adj_hr_per_100_air"] = 100 * t["adj_hr_ratio"] * a["is_hr"].mean()
    stats = g.apply(lambda d: pd.Series(dict(
        zip(["mean_resid", "se_resid"], clustered_mean(d["resid"], d["game_pk"]))) | dict(
        zip(["mean_resid_partial", "se_partial"], clustered_mean(d["resid_partial"], d["game_pk"])))),
        include_groups=False)
    t = t.join(stats)
    for c, se in [("mean_resid", "se_resid"), ("mean_resid_partial", "se_partial")]:
        t[c + "_ci_low"], t[c + "_ci_high"] = t[c] - 1.96 * t[se], t[c] + 1.96 * t[se]
    t["physics_pred_ft"] = g["phys_pred"].mean() - a["phys_pred"].mean()
    # Within-unit humid-minus-dry difference in the temperature/wind-adjusted residual.
    hd = a.groupby(keys + ["humid_tercile"], observed=True)["resid_partial"].mean().unstack()
    t["resid_humid_minus_dry"] = hd.get("humid") - hd.get("dry")
    return t.drop(columns=["se_resid", "se_partial"]).reset_index()


def map_tables(bb, a, fit):
    """fit = primary stage-2 fit; used to remove temperature + wind for the partial residual."""
    lg = bb[bb["is_fly_ball"]].groupby("year")["is_hr"].mean()
    bb = bb.assign(lg_fb_rate=bb["year"].map(lg))
    a = a.assign(p_base=baseline_hr_prob(a))
    # Stage 1 already removed season x month means, so remove weather deviations from the season-month mean.
    sm_mean = a.groupby("season_month")[["temperature_2m", "wind_out", "wind_rf"]].transform("mean")
    adj = sum(fit.params[c] * (a[c] - sm_mean[c]) for c in ["temperature_2m", "wind_out", "wind_rf"])
    a["resid_partial"] = a["resid"] - adj
    names = bb.groupby("venue_id").agg(venue_name=("venue_name", "last"), lat=("lat", "first"),
                                       lon=("lon", "first"), elevation_ft=("elevation_ft", "first"),
                                       home_team=("home_team_abbr", "last"))
    park = _summ(bb, a, ["venue_id"]).merge(names.reset_index(), on="venue_id")
    month = _summ(bb, a, ["month"])
    # Stage-1 and baseline models include season x month FE, so by-month means of the residual and the
    # adjusted ratio are 0 / 1 by construction. Blank them so nobody maps them.
    blank = [c for c in month.columns if c.startswith(("mean_resid", "adj_hr"))]
    month[blank] = np.nan
    pm = _summ(bb, a, ["venue_id", "month"]).merge(names.reset_index(), on="venue_id")
    park.to_csv(RESULTS / "map_by_park.csv", index=False)
    month.to_csv(RESULTS / "map_by_month.csv", index=False)
    pm.to_csv(RESULTS / "map_by_park_month.csv", index=False)
    return park, month, pm


def binned(a, var, edges, name):
    """Raw means (clustered CI) + regression-adjusted bin effects (controls + FE, clustered CI)."""
    a = a.assign(bin=pd.cut(a[var], edges))
    rows = []
    for b, d in a.groupby("bin", observed=True):
        md, sd = clustered_mean(d["hit_distance_sc"], d["game_pk"])
        mr, sr = clustered_mean(d["resid"], d["game_pk"])
        rows.append(dict(bin=str(b), bin_mid=b.mid, n_balls=len(d), n_games=d["game_pk"].nunique(),
                         mean_var=d[var].mean(), mean_distance=md, distance_ci_low=md - 1.96 * sd,
                         distance_ci_high=md + 1.96 * sd, mean_resid=mr, resid_ci_low=mr - 1.96 * sr,
                         resid_ci_high=mr + 1.96 * sr, mean_temp_c=d["temperature_2m"].mean()))
    out = pd.DataFrame(rows)
    # Adjusted: resid ~ C(bin) + temperature + pressure + wind + park_period FE + season-month FE.
    controls = CONTROLS if var != "temperature_2m" else "surface_pressure + wind_out + wind_rf"
    a = a.assign(bin_s=a["bin"].astype(str))
    ref = out.loc[out["n_balls"].idxmax(), "bin"]
    for outcome, col in [("resid", "adj"), ("phys_pred", "physics")]:
        f = ols_cluster(f"{outcome} ~ C(bin_s, Treatment('{ref}')) + {controls} + {FE}", a)
        est, lo, hi = [], [], []
        for b in out["bin"]:
            t = f"C(bin_s, Treatment('{ref}'))[T.{b}]"
            e, s = (f.params[t], f.bse[t]) if t in f.params else (0.0, 0.0)
            est.append(e); lo.append(e - 1.96 * s); hi.append(e + 1.96 * s)
        out[f"{col}_effect"], out[f"{col}_ci_low"], out[f"{col}_ci_high"] = est, lo, hi
    out = out.drop(columns=["physics_ci_low", "physics_ci_high"])
    out["reference_bin"] = ref
    out.to_csv(RESULTS / f"binned_{name}.csv", index=False)
    return out


def run(bb, a, fit):
    map_tables(bb, a, fit)
    a2 = a.dropna(subset=["dew_point_2m"])
    lo, hi = np.floor(a2["dew_point_2m"].quantile(0.005)), np.ceil(a2["dew_point_2m"].quantile(0.995))
    dew = binned(a, "dew_point_2m", np.r_[-np.inf, np.arange(lo + 2, hi - 1, 2), np.inf], "dewpoint")
    rh = binned(a, "relative_humidity_2m", np.r_[-np.inf, np.arange(30, 100, 10), np.inf], "rh")
    return dew, rh
