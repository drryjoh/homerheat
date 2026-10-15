"""Fig 06 (Q3, rain): do home runs still fly in light rain?

Shows, for three definitions of a rainy game, the effect of rain on (left) air-ball carry beyond launch
conditions, in ft, and (right) the EV/LA-adjusted HR count, in %, each with a 95% game-clustered CI.
Both come from the primary models with a rain dummy added, so dew point, temperature, pressure, wind,
park-period and season-month are held fixed. Hollow markers show the raw (unadjusted for weather) residual
gap, rain minus dry. Only games that were played are included; weather is at first pitch.
Data: analysis/results/rain.csv.
Run:  .venv/bin/python figures/fig06_rain.py
"""
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from style import apply, C, SLIDE, title_block, footnote, save, load_csv

apply()
r = load_csv("rain.csv").set_index("flag")
ORDER = [("rain_statsapi", "Reported rain/drizzle\nat first pitch (strict)"),
         ("rain_era5_1mm", "ERA5 precipitation\n> 1 mm/h"),
         ("rain_era5", "ERA5 precipitation\n> 0.1 mm/h (noisy)")]

fig = plt.figure(figsize=SLIDE)
ax1 = fig.add_axes([0.25, 0.2, 0.33, 0.58])
ax2 = fig.add_axes([0.63, 0.2, 0.33, 0.58], sharey=ax1)
n = len(ORDER)
ax1.set_ylim(-0.6, n - 0.4)
for i, (flag, lab) in enumerate(ORDER):
    y = n - 1 - i
    d = r.loc[flag]
    ax1.plot([d["resid_ci_low"], d["resid_ci_high"]], [y, y], color=C["blue"], lw=2.2, solid_capstyle="round")
    ax1.plot(d["resid_ft"], y, "o", color=C["blue"], ms=8, mec="white", mew=1.5, zorder=4)
    raw = d["raw_resid_rain"] - d["raw_resid_dry"]
    ax1.plot(raw, y, "o", mfc="white", mec=C["orange"], mew=1.8, ms=8, zorder=3)
    ax2.plot([d["hr_ci_low"], d["hr_ci_high"]], [y, y], color=C["blue"], lw=2.2, solid_capstyle="round")
    ax2.plot(d["hr_pct"], y, "o", color=C["blue"], ms=8, mec="white", mew=1.5, zorder=4)
    fy = fig.transFigure.inverted().transform(ax1.transData.transform((0, y)))[1]
    fig.text(0.225, fy, lab, ha="right", va="bottom", fontsize=10.5, color=C["ink"], linespacing=1.25)
    fig.text(0.225, fy - 0.012, f"{int(d['n_games_rain']):,} games · {int(d['n_hr_rain']):,} HRs",
             ha="right", va="top", fontsize=9, color=C["ink2"])

for ax in (ax1, ax2):
    ax.axvline(0, color=C["ink2"], lw=1, zorder=1)
    ax.set_ylim(-0.6, n - 0.4)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", left=False, labelleft=False)
    ax.spines["left"].set_visible(False)
ax1.set_xlim(-3.5, 1.5)
ax2.set_xlim(-8, 3)
ax1.set_xlabel("Change in carry (ft)")
ax2.set_xlabel("Change in HR count (%), EV/LA-adjusted")
ax1.set_title("Distance beyond launch conditions", fontsize=12)
ax2.set_title("Home-run rate", fontsize=12)
ax1.annotate("raw gap −2.7 ft:\nrain games are cooler", (r.loc["rain_statsapi", "raw_resid_rain"]
             - r.loc["rain_statsapi", "raw_resid_dry"], n - 1), xytext=(14, 20), textcoords="offset points",
             fontsize=8.5, color=C["ink2"], arrowprops=dict(arrowstyle="-", color=C["muted"], lw=0.6))

leg = [Line2D([], [], color=C["blue"], marker="o", mec="white", ms=8, lw=2.2),
       Line2D([], [], ls="none", marker="o", mfc="white", mec=C["orange"], mew=1.8, ms=8)]
fig.legend(leg, ["Weather-adjusted effect, 95% CI", "Raw residual gap (no weather controls)"],
           loc="lower left", bbox_to_anchor=(0.25, 0.055), ncol=2, fontsize=9.5)

title_block(fig, "Light rain does not suppress home runs once the weather is accounted for",
            "Every 95% CI spans zero. Games with reported rain look ~3 ft shorter raw, only because rainy air is cooler.")
footnote(fig, "Outdoor games 2015–2025 that were played (rainouts excluded); 20,744 games in total. ERA5 has a known "
              "drizzle bias, so the 0.1 mm/h flag fires often.", y=0.008)
save(fig, "fig06_rain")
