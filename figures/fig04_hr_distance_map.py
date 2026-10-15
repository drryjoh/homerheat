"""Fig 04 (Q4): average home-run distance by park, and extra carry beyond launch conditions.

Left: mean Statcast distance of home runs at each park (outdoor games 2015-2025). This mixes altitude, climate
and fence geometry (a short porch produces short HRs).
Right: mean_resid_partial, the average air ball's distance beyond what its exit velocity, launch angle and
spray predict, net of game-day temperature and wind (ft). This isolates the air and park: altitude, typical
climate and park-specific carry. It is NOT a humidity map.
Dot size = games; hollow ring = retractable-roof park (open-roof games only).
Data: analysis/results/map_by_park.csv.
Run:  .venv/bin/python figures/fig04_hr_distance_map.py
"""
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, TwoSlopeNorm
import cartopy.crs as ccrs

from style import (apply, C, SLIDE, DIVERGING, SEQ_BLUE, RETRACTABLE, title_block, footnote, save,
                   load_csv, us_map_axes)

apply()
pk = load_csv("map_by_park.csv").sort_values("n_games", ascending=False)
PC = ccrs.PlateCarree()
roof = pk["venue_id"].isin(RETRACTABLE)


def size(n):
    return 12 + 0.11 * n


def draw(ax, col, cmap, norm):
    o, r = pk[~roof], pk[roof]
    ax.scatter(o["lon"], o["lat"], s=size(o["n_games"]), c=o[col], cmap=cmap, norm=norm,
               edgecolors="white", linewidths=0.7, transform=PC, zorder=3)
    ax.scatter(r["lon"], r["lat"], s=size(r["n_games"]), facecolors="white",
               edgecolors=cmap(norm(r[col])), linewidths=2, transform=PC, zorder=4)


def label(ax, vid, text, dx, dy):
    row = pk[pk["venue_id"] == vid].iloc[0]
    ax.annotate(text, (row["lon"], row["lat"]), xycoords=PC._as_mpl_transform(ax), xytext=(dx, dy),
                textcoords="offset points", fontsize=8.5, color=C["ink"], ha="center", va="center",
                arrowprops=dict(arrowstyle="-", color=C["muted"], lw=0.6, shrinkA=0, shrinkB=4), zorder=6)


fig = plt.figure(figsize=SLIDE)
ax1 = us_map_axes(fig, [0.01, 0.22, 0.485, 0.66])
ax2 = us_map_axes(fig, [0.505, 0.22, 0.485, 0.66])

n1 = Normalize(390, 415)
draw(ax1, "mean_hr_distance", SEQ_BLUE, n1)
ax1.set_title("Mean home-run distance (ft)", fontsize=12)
for vid, dx, dy in [(19, 0, 22), (7, 0, -20), (15, -10, -22), (2602, 18, -20), (3313, 18, -16), (2395, -10, -22)]:
    v = pk.loc[pk["venue_id"] == vid].iloc[0]
    label(ax1, vid, f"{v['home_team']} {v['mean_hr_distance']:.0f}", dx, dy)

n2 = TwoSlopeNorm(vcenter=0, vmin=-8, vmax=8)
draw(ax2, "mean_resid_partial", DIVERGING, n2)
ax2.set_title("Extra carry beyond launch, temp & wind (ft)", fontsize=12)
for vid, dx, dy in [(19, 0, 22), (7, 0, -20), (15, -10, -22), (2395, -10, -22), (680, 34, -6), (32, 0, 22)]:
    v = pk.loc[pk["venue_id"] == vid].iloc[0]
    label(ax2, vid, f"{v['home_team']} {v['mean_resid_partial']:+.1f}".replace("-", "−"), dx, dy)

for ax, cmap, norm, ticks, fmt, cap in [
        (ax1, SEQ_BLUE, n1, [390, 395, 400, 405, 410, 415], "{:.0f}",
         "Raw: mixes altitude, climate and fence depth (short porch → short HRs)"),
        (ax2, DIVERGING, n2, [-8, -4, 0, 4, 8], "{:+.0f}",
         "Adjusted: carry beyond EV/LA/spray, net of game-day temp and wind")]:
    ax.apply_aspect()
    pos = ax.get_position()
    cax = fig.add_axes([pos.x0 + 0.06, pos.y0 - 0.045, pos.width - 0.12, 0.02])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal",
                      extend="both")
    cb.set_ticks(ticks)
    cb.set_ticklabels([fmt.format(t).replace("-", "−") for t in ticks])
    cb.outline.set_visible(False)
    cb.ax.tick_params(labelsize=9, length=0)
    fig.text(pos.x0 + pos.width / 2, pos.y0 - 0.105, cap, ha="center", va="top", fontsize=9, color=C["ink2"])

title_block(fig, "Coors Field is the one place the air clearly changes home-run distance",
            "Denver's thin air adds ~20 ft, exactly what air density predicts (+20.3 ft). "
            "Elsewhere park-to-park carry varies by only a few feet.")
footnote(fig, "Outdoor games 2015–2025; rings = retractable roofs (open-roof games only); dot size = games.\nRight: air balls "
              "(LA 20–40°, EV ≥ 90 mph), includes altitude, park and climate; not a humidity map.", y=0.01)
save(fig, "fig04_hr_distance_map")
