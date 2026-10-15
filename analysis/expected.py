"""PRIMARY model: distance residual on air balls.

Stage 1 (per tracking era): hit_distance_sc ~ EV x LA tensor splines + pull-angle splines
                            + season x month FE.   residual = actual - expected.
Stage 2: residual ~ humidity + temperature + surface pressure + wind (out, cross)
                    + park_period FE + season x month FE, SEs clustered by game_pk.
"""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from analysis.prep import RESULTS, air_balls, load_outdoor

STAGE1 = ("hit_distance_sc ~ bs(launch_speed, df=6) * bs(launch_angle, df=6)"
          " + bs(pull, df=6) + bs(pull, df=4):launch_angle + C(season_month)")
CONTROLS = "temperature_2m + surface_pressure + wind_out + wind_rf"
FE = "C(park_period) + C(season_month)"
# Physics (notes/physics.md): distance changes ~0.37% per 1% change in air density.
PHYS_ELASTICITY = -0.37


def ols_cluster(formula, df, cluster="game_pk"):
    d = df.dropna(subset=[cluster])
    return smf.ols(formula, d).fit(cov_type="cluster", cov_kwds={"groups": d[cluster].astype(int)})


def coef_row(fit, term, scale=1.0, label=None, **extra):
    b, se = fit.params[term] * scale, fit.bse[term] * scale
    return dict(model=label or term, term=term, scale=scale, estimate=b, ci_low=b - 1.96 * se,
                ci_high=b + 1.96 * se, se=se, p=fit.pvalues[term], n=int(fit.nobs),
                n_games=None, **extra)


def fit_expected(a):
    """Stage 1, separately per tracking era; adds expected/resid columns."""
    a = a.copy()
    for era, sub in a.groupby("tracking"):
        fit = smf.ols(STAGE1, sub).fit()
        a.loc[sub.index, "expected"] = fit.fittedvalues
        print(f"  stage 1 {era}: n={int(fit.nobs):,}  R2={fit.rsquared:.3f}  resid SD={np.sqrt(fit.scale):.1f} ft")
    a["resid"] = a["hit_distance_sc"] - a["expected"]
    a["density_pct"] = (a["air_density"] / a["air_density"].mean() - 1) * 100
    # Physics-predicted carry shift (ft) from this game's air density, for benchmarking.
    a["phys_pred"] = PHYS_ELASTICITY / 100 * a["hit_distance_sc"].mean() * a["density_pct"]
    return a


def stage2(a, humid="dew_point_2m", outcome="resid", controls=CONTROLS, fe=FE):
    rhs = " + ".join(t for t in [humid, controls, fe] if t)
    return ols_cluster(f"{outcome} ~ {rhs}", a)


def humidity_table(a, tag="primary"):
    """Main humidity coefficients plus physics benchmarks under identical controls."""
    rows = []
    specs = [  # (label, regressor, scale, controls)
        ("dew point, ft per +10 C", "dew_point_2m", 10, CONTROLS),
        ("vapor pressure, ft per +10 hPa", "vapor_pressure_hpa", 10, CONTROLS),
        ("RH (sensitivity), ft per +10 pts", "relative_humidity_2m", 10, CONTROLS),
        ("air density alone, ft per +1%", "density_pct", 1, "wind_out + wind_rf"),
    ]
    for label, term, scale, ctl in specs:
        f = stage2(a, term, controls=ctl)
        fp = stage2(a, term, outcome="phys_pred", controls=ctl)
        r = coef_row(f, term, scale, label, sample=tag)
        r["physics_pred"] = fp.params[term] * scale
        r["n_games"] = a.loc[f.model.data.row_labels, "game_pk"].nunique()
        rows.append(r)
    # Does humidity act beyond its density contribution? Split density into dry + vapour parts.
    a = a.assign(dry_density_pct=a["density_pct"] - (a["vapor_density_pct"] - a["vapor_density_pct"].mean()))
    f = stage2(a, "dry_density_pct + vapor_density_pct", controls="wind_out + wind_rf")
    for term in ["dry_density_pct", "vapor_density_pct"]:
        r = coef_row(f, term, 1, f"{term.split('_')[0]} part of density, ft per +1%", sample=tag)
        r["physics_pred"] = PHYS_ELASTICITY / 100 * a["hit_distance_sc"].mean()
        r["n_games"] = a["game_pk"].nunique()
        rows.append(r)
    return pd.DataFrame(rows)


def run():
    bb = load_outdoor()
    a = fit_expected(air_balls(bb))
    a[["game_pk", "batter", "pitcher", "venue_id", "park_period", "year", "month", "tracking",
       "launch_speed", "launch_angle", "pull", "hit_distance_sc", "expected", "resid", "is_hr",
       "dew_point_2m", "relative_humidity_2m", "temperature_2m", "humid_tercile"]].to_parquet(
        RESULTS / "air_balls_resid.parquet")

    tab = humidity_table(a)
    # Weather control coefficients from the primary spec, for context.
    f = stage2(a)
    ctl = [coef_row(f, "temperature_2m", 10, "temperature, ft per +10 C"),
           coef_row(f, "wind_out", 1, "wind out to CF, ft per +1 m/s"),
           coef_row(f, "wind_rf", 1, "wind toward RF, ft per +1 m/s"),
           coef_row(f, "surface_pressure", 10, "surface pressure, ft per +10 hPa")]
    ctl = pd.DataFrame(ctl).assign(sample="primary", n_games=a["game_pk"].nunique())
    ctl["physics_pred"] = [stage2(a, outcome="phys_pred").params[t] * s
                           for t, s in [("temperature_2m", 10), ("wind_out", 1), ("wind_rf", 1),
                                        ("surface_pressure", 10)]]
    out = pd.concat([tab, ctl], ignore_index=True)
    out.to_csv(RESULTS / "distance_model.csv", index=False)

    # Dry vs humid tercile (raw and model-adjusted difference).
    f = ols_cluster(f"resid ~ C(humid_tercile, Treatment('dry')) + {CONTROLS} + {FE}", a)
    t = "C(humid_tercile, Treatment('dry'))[T.humid]"
    terc = pd.DataFrame([coef_row(f, t, 1, "humid - dry tercile, ft (adjusted)")])
    raw = a.groupby("humid_tercile", observed=True)[["hit_distance_sc", "resid"]].mean()
    terc["raw_resid_diff"] = raw.loc["humid", "resid"] - raw.loc["dry", "resid"]
    terc["raw_distance_diff"] = raw.loc["humid", "hit_distance_sc"] - raw.loc["dry", "hit_distance_sc"]
    terc.to_csv(RESULTS / "distance_tercile.csv", index=False)
    return a, out, terc


if __name__ == "__main__":
    a, out, terc = run()
    pd.set_option("display.width", 200)
    print(out[["model", "estimate", "ci_low", "ci_high", "p", "physics_pred", "n", "n_games"]].round(3))
    print(terc.round(3).T)
