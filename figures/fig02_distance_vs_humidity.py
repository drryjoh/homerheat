"""Fig 02 (Q5): fly-ball distance vs humidity: raw, adjusted, and physics.

Shows, for well-hit air balls (launch angle 20-40 deg, EV >= 90 mph, outdoor games 2015-2025), the change in
carry relative to a reference humidity bin:
  * raw mean distance (with 95% game-clustered CI band),
  * what temperature alone would produce (bin mean temperature x the fitted +0.437 ft/degC slope),
  * the adjusted bin effect with 95% CI (controls: EV x LA x spray, temperature, pressure, wind,
    park-period FE, season-month FE),
  * the physics prediction under the same controls.
Left: dew point (primary humidity measure). Right: relative humidity (sensitivity; RH falls as air warms).
Data: analysis/results/binned_dewpoint.csv, binned_rh.csv, distance_model.csv (temperature slope).
Run:  .venv/bin/python figures/fig02_distance_vs_humidity.py
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from style import apply, C, SLIDE, title_block, footnote, save, load_csv

apply()
dm = load_csv("distance_model.csv").set_index("term")
T_SLOPE = dm.loc["temperature_2m", "estimate"] / 10          # ft per degC

YLIM = (-3.5, 5.2)


def panel(ax, df, xlabel):
    ref = df[df["bin"] == df["reference_bin"].iloc[0]].iloc[0]
    x = df["mean_var"].to_numpy()
    raw = df["mean_distance"] - ref["mean_distance"]
    lo, hi = df["distance_ci_low"] - ref["mean_distance"], df["distance_ci_high"] - ref["mean_distance"]
    temp_only = T_SLOPE * (df["mean_temp_c"] - ref["mean_temp_c"])

    ax.axhline(0, color=C["axis"], lw=0.9, zorder=1)
    ax.fill_between(x, lo, hi, color=C["orange"], alpha=0.15, lw=0, zorder=2)
    ax.plot(x, raw.clip(*YLIM), color=C["orange"], lw=2, marker="o", ms=5, mec="white", mew=1, zorder=3)
    ax.plot(x, temp_only, color=C["muted"], lw=1.6, ls=(0, (4, 2)), zorder=3)
    ax.plot(x, df["physics_effect"], color=C["aqua"], lw=2.2, zorder=4)
    ax.errorbar(x, df["adj_effect"], yerr=[df["adj_effect"] - df["adj_ci_low"],
                                           df["adj_ci_high"] - df["adj_effect"]],
                fmt="o", color=C["blue"], ms=6, mec="white", mew=1, elinewidth=1.4, capsize=0, zorder=5)
    # Mark any raw point clipped off the top.
    for xi, r in zip(x, raw):
        if r > YLIM[1]:
            ax.annotate(f"raw {r:+.1f} ft\n(dry desert/\naltitude parks)", (xi, YLIM[1]), xytext=(34, -4),
                        textcoords="offset points", fontsize=8.5, color=C["ink2"], va="top",
                        bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))
            ax.plot(xi, YLIM[1], marker="^", color=C["orange"], ms=7, clip_on=False, zorder=6)
    ax.set_ylim(*YLIM)
    ax.set_xlabel(xlabel)
    return x


dew = load_csv("binned_dewpoint.csv")
rh = load_csv("binned_rh.csv")

fig = plt.figure(figsize=SLIDE)
ax1 = fig.add_axes([0.07, 0.24, 0.55, 0.58])
ax2 = fig.add_axes([0.67, 0.24, 0.31, 0.58], sharey=ax1)
panel(ax1, dew, "Dew point at first pitch (°C)")
panel(ax2, rh, "Relative humidity (%)")
ax1.set_ylabel("Change in carry vs reference bin (ft)")
ax1.set_title("Dew point (primary)   ·   0 = 12–14 °C bin", fontsize=12)
ax2.set_title("RH (sensitivity)   ·   0 = 50–60% bin", fontsize=12)
plt.setp(ax2.get_yticklabels(), visible=False)

handles = [
    (Line2D([], [], color=C["orange"], marker="o", mec="white", lw=2), "Raw mean distance (band = 95% CI)"),
    (Line2D([], [], color=C["muted"], ls=(0, (4, 2)), lw=1.6), "What temperature alone predicts"),
    (Line2D([], [], color=C["blue"], marker="o", ls="none", mec="white", ms=7),
     "Adjusted effect, 95% CI (T, P, wind, park, era held fixed)"),
    (Line2D([], [], color=C["aqua"], lw=2.2), "Physics prediction (air density)"),
]
fig.legend([h for h, _ in handles], [l for _, l in handles], loc="lower left", ncol=2,
           bbox_to_anchor=(0.06, 0.035), fontsize=9.5, columnspacing=2.0, handlelength=2.4)

title_block(fig, "Humid days show longer fly balls, mostly because they are hot days",
            "With temperature, wind, park and era held fixed, humidity adds about 1 ft per 10 °C of dew point, "
            "close to the physics line.")
footnote(fig, "Air balls: launch 20–40°, EV ≥ 90 mph, outdoor games 2015–2025 (159,725 balls, 20,744 games). "
              "ERA5 weather at first pitch. CIs clustered by game.", y=0.005)
save(fig, "fig02_distance_vs_humidity")
