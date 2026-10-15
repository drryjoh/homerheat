"""Fig 05: the punchline. Humidity vs the other things that move a fly ball, in feet of carry.

Forest plot of fitted effects on air-ball carry (distance beyond what exit velocity, launch angle and spray
predict), 95% CIs clustered by game, all from the same primary model (park-period + season-month FE), with
the physics prediction for each beside it:
  * +10 degC dew point (primary), and with the richest temperature control (robustness.csv);
  * humid vs dry tercile of games (distance_tercile.csv);
  * +10 degC temperature, +1 m/s ERA5 wind out to CF (distance_model.csv);
  * +1000 ft altitude = the surface-pressure coefficient x 36.1 hPa (ISA pressure drop for 1000 ft);
  * Coors Field mean residual vs league (map_by_park.csv), physics = its density-predicted carry.
Right column: EV/LA-adjusted HR-count change from the ball-level logit (hr_model.csv), where it exists.
Data: analysis/results/distance_model.csv, distance_tercile.csv, robustness.csv, map_by_park.csv, hr_model.csv.
Run:  .venv/bin/python figures/fig05_effect_sizes.py
"""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

from style import apply, C, SLIDE, title_block, footnote, save, load_csv
from air import pressure_at_altitude              # physics/air.py

apply()
dm = load_csv("distance_model.csv").set_index("term")
rb = load_csv("robustness.csv").set_index("model")
tc = load_csv("distance_tercile.csv").iloc[0]
pk = load_csv("map_by_park.csv").set_index("venue_id")
hr = load_csv("hr_model.csv").set_index("model")

dp_1000ft = (101325 - pressure_at_altitude(304.8)) / 100          # hPa, ~36.1
p = dm.loc["surface_pressure"]
k = -dp_1000ft / 10                                               # coefficient is per +10 hPa
rich = rb.loc["Richest T control (ERA5 FP x day/night + reported + ball-time T)"]
coors = pk.loc[19]


def hrpct(model):
    r = hr.loc[model]
    return f"{r['pct_change']:+.1f}%  ({r['ci_low']:+.1f} to {r['ci_high']:+.1f})".replace("-", "−")


rows = [  # label, est, lo, hi, physics, humidity?, HR text
    ("+10 °C dew point", dm.loc["dew_point_2m", "estimate"], dm.loc["dew_point_2m", "ci_low"],
     dm.loc["dew_point_2m", "ci_high"], dm.loc["dew_point_2m", "physics_pred"], True,
     hrpct("logit: per +10 C dew point")),
    ("… with richest temperature control", rich["estimate"], rich["ci_low"], rich["ci_high"], rich["physics_pred"],
     True, ""),
    ("Humid vs dry third of games", tc["estimate"], tc["ci_low"], tc["ci_high"], 0.7, True,
     hrpct("logit: humid vs dry tercile")),
    ("+1 m/s wind out to CF (ERA5 10 m)", dm.loc["wind_out", "estimate"], dm.loc["wind_out", "ci_low"],
     dm.loc["wind_out", "ci_high"], None, False, hrpct("logit: per +1 m/s wind out")),
    ("+10 °C temperature", dm.loc["temperature_2m", "estimate"], dm.loc["temperature_2m", "ci_low"],
     dm.loc["temperature_2m", "ci_high"], dm.loc["temperature_2m", "physics_pred"], False,
     hrpct("logit: per +10 C temperature")),
    ("+1,000 ft altitude (via pressure)", k * p["estimate"], k * p["ci_high"], k * p["ci_low"],
     k * p["physics_pred"], False, ""),
    ("Coors Field vs league", coors["mean_resid"], coors["mean_resid_ci_low"], coors["mean_resid_ci_high"],
     coors["physics_pred_ft"], False, ""),
]

fig = plt.figure(figsize=SLIDE)
ax = fig.add_axes([0.30, 0.17, 0.44, 0.64])
n = len(rows)
ax.set_xlim(-1, 23)
ax.set_ylim(-0.6, n - 0.4)


def fig_y(y):
    """Figure-fraction y of a data y on ax (limits are fixed above, so this is stable)."""
    return fig.transFigure.inverted().transform(ax.transData.transform((0, y)))[1]


for i, (lab, est, lo, hi, phys, humid, hrtxt) in enumerate(rows):
    y = n - 1 - i
    if humid:
        ax.add_patch(Rectangle((-1, y - 0.45), 24, 0.9, color=C["neutral"], zorder=0, lw=0))
    ax.plot([lo, hi], [y, y], color=C["blue"], lw=2.2, solid_capstyle="round", zorder=3)
    ax.plot(est, y, "o", color=C["blue"], ms=8, mec="white", mew=1.5, zorder=4)
    if phys is not None:
        ax.plot(phys, y + 0.28, marker="D", ms=6.5, color=C["aqua"], mec="white", mew=1, ls="none", zorder=4)
    txt = f"{est:+.1f}"
    if humid:
        txt += f"  (CI {lo:.1f}–{hi:.1f};  physics {phys:+.2f})"
    ax.text(hi + 0.4, y, txt, va="center", fontsize=10, color=C["ink"])
    fig.text(0.29, fig_y(y), lab, ha="right", va="center",
             fontsize=10.5, color=C["ink"], fontweight="bold" if humid and i != 1 else "normal")
    fig.text(0.765, fig_y(y), hrtxt or "—", ha="left",
             va="center", fontsize=9.5, color=C["ink2"] if hrtxt else C["muted"])

ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.grid(axis="y", visible=False)
ax.axvline(0, color=C["axis"], lw=0.9, zorder=1)
ax.set_xlabel("Extra carry of a well-hit fly ball (ft)")
fig.text(0.765, 0.835, "HR count, EV/LA-adjusted", fontsize=9.5, color=C["ink2"], fontweight="bold")
leg = [Line2D([], [], color=C["blue"], marker="o", mec="white", ms=8, lw=2.2),
       Line2D([], [], color=C["aqua"], marker="D", mec="white", ms=6.5, ls="none")]
fig.legend(leg, ["Measured, 95% CI (game-clustered)", "Physics prediction"], loc="lower left",
           bbox_to_anchor=(0.29, 0.805), ncol=2, fontsize=9.5)

title_block(fig, "Humidity is real but small next to temperature and altitude",
            "About 0.5–1 ft per +10 °C dew point, the size physics predicts. +10 °C of temperature is ~5×, "
            "Coors ~25×; ~1.5 m/s of wind out matches it.")
footnote(fig, "Outdoor games 2015–2025, 159,725 air balls. Altitude = pressure coefficient × 36 hPa. No wind physics marker: "
              "ERA5 10 m grid wind understates in-park wind (Nathan: ~8 ft per m/s).\n"
              "Game-level HR per fly ball (not EV/LA-adjusted) shows no detectable dew-point effect: −1.1% (−3.3 to +1.3).",
         y=0.008)
save(fig, "fig05_effect_sizes")
