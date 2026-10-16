"""Build the interactive HTML report: report/interactive.html.

Reads only analysis/results/*.csv (like the figure scripts), projects US state outlines and park
locations to SVG coordinates, and drops everything as JSON into report/interactive_template.html.
Run from the repo root:  .venv/bin/python report/build_html.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader
from shapely.geometry import box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "analysis" / "results"
sys.path.insert(0, str(ROOT / "physics"))
from air import pressure_at_altitude  # noqa: E402

RETRACTABLE = {15, 14, 32, 2392, 4169, 5325}   # same lists as figures/style.py
TEMPORARY = {2536, 2756}
W, H = 960, 560                                 # SVG viewBox for the map


def csv(name):
    return pd.read_csv(RES / name)


def clean(v):
    if isinstance(v, (float, np.floating)):
        return None if not np.isfinite(v) else round(float(v), 4)
    if isinstance(v, np.integer):
        return int(v)
    return v


def records(df, cols):
    return [{c: clean(r[c]) for c in cols} for _, r in df.iterrows()]


# --- map geometry -----------------------------------------------------------------------------
proj = ccrs.LambertConformal(central_longitude=-96, central_latitude=39, standard_parallels=(33, 45))
pc = ccrs.PlateCarree()
lon, lat = np.meshgrid(np.linspace(-123, -70, 30), np.linspace(25, 48, 30))
xy = proj.transform_points(pc, lon.ravel(), lat.ravel())
x0, x1, y0, y1 = xy[:, 0].min(), xy[:, 0].max(), xy[:, 1].min(), xy[:, 1].max()
pad = 0.03
x0, x1 = x0 - pad * (x1 - x0), x1 + pad * (x1 - x0)
y0, y1 = y0 - pad * (y1 - y0), y1 + pad * (y1 - y0)
scale = min(W / (x1 - x0), H / (y1 - y0))
frame = box(x0, y0, x1, y1)


def to_svg(x, y):
    return (x - x0) * scale, H - (y - y0) * scale


def path_d(geom):
    polys = getattr(geom, "geoms", [geom])
    out = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            pts = [to_svg(x, y) for x, y in ring.coords]
            if len(pts) > 2:
                out.append("M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + "Z")
    return "".join(out)


states = shpreader.natural_earth("50m", "cultural", "admin_1_states_provinces_lakes")
shapes = []
for rec in shpreader.Reader(states).records():
    if rec.attributes.get("admin") not in ("United States of America", "Canada", "Mexico"):
        continue
    g = proj.project_geometry(rec.geometry, pc).intersection(frame)
    if g.is_empty:
        continue
    g = g.simplify(2500)
    if not g.is_empty:
        shapes.append(path_d(g))

# --- tables -----------------------------------------------------------------------------------
park_cols = ["venue_id", "venue_name", "home_team", "lat", "lon", "elevation_ft", "n_games", "n_hr",
             "n_air", "mean_hr_distance", "hr_per_fb", "hr_per_fb_rel_league", "adj_hr_ratio",
             "mean_resid_partial", "mean_resid_partial_ci_low", "mean_resid_partial_ci_high",
             "physics_pred_ft", "mean_dew_point", "mean_rh", "mean_temp_c"]


def with_xy(df):
    p = proj.transform_points(pc, df["lon"].to_numpy(), df["lat"].to_numpy())
    df = df.copy()
    df["x"], df["y"] = zip(*[to_svg(a, b) for a, b in p[:, :2]])
    df["roof"] = df["venue_id"].isin(RETRACTABLE)
    df["temporary"] = df["venue_id"].isin(TEMPORARY)
    return df


parks = with_xy(csv("map_by_park.csv"))
pm = with_xy(csv("map_by_park_month.csv"))
pm = pm[pm["month"].between(4, 9) & (pm["n_games"] >= 5)]
extra = ["x", "y", "roof", "temporary"]

dm = csv("distance_model.csv").set_index("term")
rb = csv("robustness.csv")
tc = csv("distance_tercile.csv").iloc[0]
hr = csv("hr_model.csv").set_index("model")
coors = parks.set_index("venue_id").loc[19]
k = -((101325 - pressure_at_altitude(304.8)) / 100) / 10          # +1000 ft as surface-pressure change
p = dm.loc["surface_pressure"]
rich = rb.set_index("model").loc["Richest T control (ERA5 FP x day/night + reported + ball-time T)"]


def hrfx(model):
    r = hr.loc[model]
    return [clean(r["pct_change"]), clean(r["ci_low"]), clean(r["ci_high"])]


def row(label, est, lo, hi, phys, humid, hrv=None, note=""):
    return dict(label=label, est=clean(est), lo=clean(lo), hi=clean(hi), phys=clean(phys),
                humid=humid, hr=hrv, note=note)


effects = [
    row("+10 °C dew point", *dm.loc["dew_point_2m", ["estimate", "ci_low", "ci_high", "physics_pred"]], True,
        hrfx("logit: per +10 C dew point"), "Primary model"),
    row("… with richest temperature control", rich["estimate"], rich["ci_low"], rich["ci_high"],
        rich["physics_pred"], True, None, "Adds in-park reported and ball-time temperature"),
    row("Humid vs dry third of games", tc["estimate"], tc["ci_low"], tc["ci_high"], 0.7, True,
        hrfx("logit: humid vs dry tercile"), "Physics from notes/physics.md"),
    row("+1 m/s wind out to CF", *dm.loc["wind_out", ["estimate", "ci_low", "ci_high"]], None, False,
        hrfx("logit: per +1 m/s wind out"), "ERA5 10 m grid wind; no like-for-like physics value"),
    row("+10 °C temperature", *dm.loc["temperature_2m", ["estimate", "ci_low", "ci_high", "physics_pred"]],
        False, hrfx("logit: per +10 C temperature")),
    row("+1,000 ft altitude", k * p["estimate"], k * p["ci_high"], k * p["ci_low"], k * p["physics_pred"],
        False, None, "Surface-pressure coefficient × 36 hPa"),
    row("Coors Field vs league", coors["mean_resid"], coors["mean_resid_ci_low"], coors["mean_resid_ci_high"],
        coors["physics_pred_ft"], False, None, "Park mean residual; physics = density-predicted carry"),
]

bin_cols = ["bin_mid", "mean_var", "n_balls", "n_games", "mean_distance", "mean_resid", "mean_temp_c",
            "adj_effect", "adj_ci_low", "adj_ci_high", "physics_effect", "reference_bin", "bin"]


def bins(name):
    b = csv(name)
    ref = b[b["bin"] == b["reference_bin"].iloc[0]].iloc[0]
    b["raw_vs_ref"] = b["mean_distance"] - ref["mean_distance"]
    return records(b, bin_cols + ["raw_vs_ref"])


hrm = csv("hr_model.csv")
data = dict(
    states=shapes, W=W, H=H,
    parks=records(parks, park_cols + extra),
    park_month=records(pm, park_cols + ["month"] + extra),
    effects=effects,
    bins_dp=bins("binned_dewpoint.csv"), bins_rh=bins("binned_rh.csv"),
    rain=records(csv("rain.csv"), ["flag", "label", "resid_ft", "resid_ci_low", "resid_ci_high", "hr_pct",
                                   "hr_ci_low", "hr_ci_high", "n_games_rain", "n_hr_rain", "raw_resid_rain"]),
    robust=records(rb, ["model", "estimate", "ci_low", "ci_high", "n_games", "unit", "physics_pred"]),
    hr_models=records(hrm, ["model", "pct_change", "ci_low", "ci_high", "n_games", "n_hr"]),
    density=records(dm.reset_index(), ["model", "term", "estimate", "ci_low", "ci_high", "physics_pred"]),
    by_month=records(csv("map_by_month.csv"), ["month", "n_games", "n_hr", "hr_per_fb", "mean_hr_distance",
                                                "mean_dew_point", "mean_temp_c"]),
)

tpl = (ROOT / "report" / "interactive_template.html").read_text()
out = ROOT / "report" / "interactive.html"
out.write_text(tpl.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":"))))
print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1e3:.0f} kB, {len(shapes)} state shapes, "
      f"{len(parks)} parks, {len(pm)} park-months)")
