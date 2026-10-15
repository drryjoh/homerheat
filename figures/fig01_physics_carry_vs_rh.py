"""Fig 01: physics expectation. Predicted carry of a typical home-run ball vs relative humidity.

Shows: carry (ft) of a 103 mph / 28 deg launch at sea level for 60, 75 and 90 F, RH 0-100%,
from the drag+lift point-mass model in physics/trajectory.py (moist-air density from physics/air.py).
Data: none (pure physics; computed on the fly, ~2 s).
Run:  .venv/bin/python figures/fig01_physics_carry_vs_rh.py
"""
import numpy as np
import matplotlib.pyplot as plt

from style import apply, C, SLIDE, title_block, footnote, save
from air import air_density                      # physics/air.py
from trajectory import carry, P_SEA              # physics/trajectory.py

apply()
rh = np.linspace(0, 100, 21)
temps = [(90, C["orange"]), (75, C["aqua"]), (60, C["blue"])]

fig = plt.figure(figsize=SLIDE)
ax = fig.add_axes([0.08, 0.13, 0.66, 0.70])
for t, col in temps:
    d = np.array([carry(air_density(t, r / 100, P_SEA)) for r in rh])
    ax.plot(rh, d, color=col, lw=2.2)
    ax.plot([0, 100], [d[0], d[-1]], "o", color=col, ms=6, mec="white", mew=1.5, clip_on=False)
    ax.annotate(f"{t}°F   {d[-1] - d[0]:+.1f} ft\nfrom 0→100% RH", (100, d[-1]), xytext=(10, 0),
                textcoords="offset points", va="center", fontsize=10.5, color=C["ink"])

ax.set_xlim(0, 100)
ax.set_ylim(409, 424)
ax.set_xlabel("Relative humidity (%)")
ax.set_ylabel("Predicted carry (ft)")
ax.set_xticks(range(0, 101, 20))

# Bracket showing how much bigger the temperature effect is.
d60 = carry(air_density(60, 0.5, P_SEA))
d90 = carry(air_density(90, 0.5, P_SEA))
ax.annotate("", xy=(50, d90), xytext=(50, d60),
            arrowprops=dict(arrowstyle="<->", color=C["ink2"], lw=1.2, shrinkA=2, shrinkB=2))
ax.text(51.5, 413.6, f"60→90°F at 50% RH: {d90 - d60:+.1f} ft", fontsize=10.5,
        color=C["ink"], va="center")

title_block(fig, "Physics: humid air adds only 1–3 ft to a home run",
            "Water vapor (18 g/mol) is lighter than dry air (29 g/mol), so humid air is slightly thinner. "
            "Temperature matters far more.")
footnote(fig, "Model: 2-D point mass, 103 mph exit velocity, 28° launch, Cd 0.35, CL 0.20, sea level, "
              "no wind (physics/trajectory.py). Agrees with Nathan (2016) within ~10%.")
save(fig, "fig01_physics_carry_vs_rh")
