"""Fig 03 (Q3): where home runs are hit most, by month, adjusted for batted-ball (team) quality.

Shows: small-multiple US maps, April-September, one dot per park. Color = adjusted HR rate
(adj_hr_ratio: HRs observed / HRs expected from each air ball's exit velocity, launch angle, spray and
season-month), shown as % above/below that month's league average. Because the expectation comes from how
hard and how high the ball was hit, a strong-hitting home team does not make its park look hot; what remains
is park, climate and weather. Size = games in that park-month. Hollow rings = retractable-roof parks (open-roof
games only). Park-months with < 5 games are dropped. Tropicana Field (fixed dome) has no outdoor games.
Data: analysis/results/map_by_park_month.csv, map_by_month.csv (league HR/FB per month).
Note: the residual / adjusted columns in map_by_month.csv are blank on purpose (season x month fixed effects
make them 0 or 1 by construction), so each panel is relative to its own month.
Run:  .venv/bin/python figures/fig03_hr_rate_map_by_month.py
"""
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.lines import Line2D
import cartopy.crs as ccrs

from style import (apply, C, SLIDE, DIVERGING, RETRACTABLE, DOMES, title_block, footnote, save,
                   load_csv, us_map_axes)

apply()
pm = load_csv("map_by_park_month.csv")
lg = load_csv("map_by_month.csv").set_index("month")
pm = pm[pm["month"].between(4, 9) & (pm["n_games"] >= 5) & pm["adj_hr_ratio"].notna()].copy()
pm["pct"] = 100 * (pm["adj_hr_ratio"] - 1)
norm = TwoSlopeNorm(vcenter=0, vmin=-30, vmax=30)
MONTHS = {4: "April", 5: "May", 6: "June", 7: "July", 8: "August", 9: "September"}
PC = ccrs.PlateCarree()


def size(n):
    return 6 + 0.55 * n          # points^2; ~10 for 5 games, ~90 for 150 games


fig = plt.figure(figsize=SLIDE)
W, H, X0, Y0, DX, DY = 0.318, 0.31, 0.012, 0.16, 0.328, 0.36
for i, (m, name) in enumerate(MONTHS.items()):
    r, c = divmod(i, 3)
    ax = us_map_axes(fig, [X0 + c * DX, Y0 + (1 - r) * DY, W, H])
    d = pm[pm["month"] == m].sort_values("n_games", ascending=False)
    roof = d["venue_id"].isin(RETRACTABLE)
    o = d[~roof]
    ax.scatter(o["lon"], o["lat"], s=size(o["n_games"]), c=o["pct"], cmap=DIVERGING, norm=norm,
               edgecolors="white", linewidths=0.6, transform=PC, zorder=3)
    rr = d[roof]
    ax.scatter(rr["lon"], rr["lat"], s=size(rr["n_games"]), facecolors="white",
               edgecolors=DIVERGING(norm(rr["pct"])), linewidths=1.8, transform=PC, zorder=4)
    for _, (la, lo) in DOMES.items():
        ax.plot(lo, la, marker="x", color=C["muted"], ms=4, mew=1.2, transform=PC, zorder=4)
    ax.text(0.0, 1.02, name, transform=ax.transAxes, fontsize=11.5, fontweight="bold", va="bottom")
    ax.text(1.0, 1.02, f"league HR/FB {100 * lg.loc[m, 'hr_per_fb']:.1f}%  ·  avg {lg.loc[m, 'mean_temp_c']:.0f} °C",
            transform=ax.transAxes, fontsize=8.5, color=C["ink2"], va="bottom", ha="right")

# Colorbar
cax = fig.add_axes([0.06, 0.085, 0.36, 0.022])
sm = plt.cm.ScalarMappable(norm=norm, cmap=DIVERGING)
cb = fig.colorbar(sm, cax=cax, orientation="horizontal", extend="both")
cb.set_ticks([-30, -15, 0, 15, 30])
cb.set_ticklabels(["−30%", "−15%", "league avg", "+15%", "+30%"])
cb.outline.set_visible(False)
cb.ax.tick_params(labelsize=9, length=0)
fig.text(0.06, 0.115, "Adjusted HR rate vs that month's league average (EV/LA/spray-adjusted)",
         fontsize=9.5, color=C["ink2"])

# Size / symbol legend
h = [Line2D([], [], ls="none", marker="o", ms=(size(n)) ** 0.5, mfc=C["axis"], mec="white") for n in (10, 60, 150)]
h += [Line2D([], [], ls="none", marker="o", ms=8, mfc="white", mec=C["ink2"], mew=1.8),
      Line2D([], [], ls="none", marker="x", ms=6, color=C["muted"], mew=1.4)]
fig.legend(h, ["10", "60", "150 games", "retractable roof\n(open-roof games)", "fixed dome\n(excluded)"],
           loc="lower left", bbox_to_anchor=(0.46, 0.055), ncol=5, fontsize=9, handletextpad=0.4,
           columnspacing=1.1)

title_block(fig, "HR hot spots by month, after adjusting for how hard balls were hit",
            "Red = more HRs than the launch conditions predict. Cincinnati, Coors, LA and Milwaukee run hot; "
            "SF, KC and Detroit run cold all season.")
footnote(fig, "Outdoor games 2015–2025, air balls (LA 20–40°, EV ≥ 90 mph). Park-months with < 5 games dropped. "
              "Colors include park dimensions, altitude and climate, not humidity alone.", y=0.008)
save(fig, "fig03_hr_rate_map_by_month")
