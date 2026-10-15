"""Simple 2D batted-ball model: how far does a typical home-run ball carry vs humidity?

Model (point mass, no wind, no spin decay):
    m dv/dt = -1/2 rho C_d A |v| v  +  1/2 rho C_L A |v|^2 n_perp  -  m g y_hat
where n_perp is the unit vector perpendicular to v (pointing "up" for backspin).
C_d = 0.35 and C_L = 0.20 are representative constants (Nathan's trajectory
calculator uses C_d ~ 0.35; C_L ~ 0.2 corresponds to ~2000 rpm backspin on a
~100 mph fly ball). Both are tunable below. Run:  python physics/trajectory.py
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[1]
try:  # prefer the project's shared density function if the other agent wrote it
    sys.path.insert(0, str(ROOT / "src"))
    from air import air_density, pressure_at_altitude  # noqa: E402
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from air import air_density, pressure_at_altitude  # noqa: E402

# --- constants -------------------------------------------------------------
G = 9.81                       # m/s^2
M = 0.145                      # kg, regulation ball (5-5.25 oz)
CIRC = 9.125 * 0.0254          # m, circumference 9.125 in
AREA = np.pi * (CIRC / (2 * np.pi)) ** 2   # cross-section, ~0.00426 m^2
CD, CL = 0.35, 0.20            # drag / lift coefficients (tunable)
MPH, FT = 0.44704, 0.3048
EV_MPH, LA_DEG, H0_FT = 103.0, 28.0, 3.0   # typical HR launch (Nathan)
P_SEA = 101325.0


def vacuum_range(v0, theta, h0):
    """No-drag kinematics: x(t)=v0 cos t, y(t)=h0+v0 sin t - g t^2/2; solve y=0."""
    vx, vy = v0 * np.cos(theta), v0 * np.sin(theta)
    t_land = (vy + np.sqrt(vy ** 2 + 2 * G * h0)) / G
    return vx * t_land


def carry(rho, ev_mph=EV_MPH, la_deg=LA_DEG, h0_ft=H0_FT, cd=CD, cl=CL):
    """Horizontal distance [ft] where the ball returns to ground level."""
    k_d = 0.5 * rho * cd * AREA / M
    k_l = 0.5 * rho * cl * AREA / M

    def rhs(_, s):
        _, _, vx, vy = s
        v = np.hypot(vx, vy)
        ax = -k_d * v * vx - k_l * v * vy
        ay = -k_d * v * vy + k_l * v * vx - G
        return [vx, vy, ax, ay]

    def ground(_, s):
        return s[1]
    ground.terminal, ground.direction = True, -1

    th = np.radians(la_deg)
    v0 = ev_mph * MPH
    s0 = [0.0, h0_ft * FT, v0 * np.cos(th), v0 * np.sin(th)]
    sol = solve_ivp(rhs, (0, 15), s0, events=ground, rtol=1e-9, atol=1e-9)
    return sol.y_events[0][0][0] / FT


def main():
    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)
    th = np.radians(LA_DEG)
    print(f"Launch: {EV_MPH} mph, {LA_DEG} deg, {H0_FT} ft.  C_d={CD}, C_L={CL}, "
          f"A={AREA*1e4:.1f} cm^2, m={M} kg")
    print(f"Vacuum (no-drag) range: {vacuum_range(EV_MPH*MPH, th, H0_FT*FT)/FT:.0f} ft\n")

    # 1) distance vs RH at fixed T, sea-level P
    rhs_pct = np.arange(0, 101, 10)
    temps = (60, 75, 90)
    table = {t: [carry(air_density(t, r / 100, P_SEA)) for r in rhs_pct] for t in temps}
    print("Carry distance (ft) vs relative humidity, sea level")
    print("  RH %  " + "".join(f"{t:>4} F   " for t in temps))
    for i, r in enumerate(rhs_pct):
        print(f"  {r:>4}  " + "".join(f"{table[t][i]:7.1f}  " for t in temps))
    for t in temps:
        print(f"  0->100% RH at {t} F: {table[t][-1]-table[t][0]:+.2f} ft "
              f"(density {100*(air_density(t,1)/air_density(t,0)-1):+.2f}%)")

    # 2) sensitivity: ft per 1% change in air density (around 75 F, 50% RH)
    rho_ref = air_density(75, 0.5, P_SEA)
    d_ref = carry(rho_ref)
    slope = (carry(rho_ref * 1.01) - carry(rho_ref * 0.99)) / 2
    print(f"\nReference: rho={rho_ref:.4f} kg/m^3 -> {d_ref:.1f} ft")
    print(f"Sensitivity: {slope:+.2f} ft per +1% air density "
          f"({100*slope/d_ref:+.2f}% distance per +1% density)")

    # 3) checks against published rules of thumb (Nathan)
    checks = [
        ("RH 25%->75% at 75 F", carry(air_density(75, .75)) - carry(air_density(75, .25)),
         "+0.9 ft (Nathan 2016)"),
        ("75 F -> 85 F at 50% RH", carry(air_density(85, .5)) - d_ref,
         "+3.3 to +4.5 ft"),
        ("Sea level -> 1000 ft (305 m)",
         carry(air_density(75, .5, pressure_at_altitude(304.8))) - d_ref, "+5.9 ft"),
        ("Sea level -> Denver (1600 m)",
         carry(air_density(75, .5, pressure_at_altitude(1600))) - d_ref,
         "+5% to +7% (Nathan; Statcast: +29 ft)"),
    ]
    print("\nRule-of-thumb checks (model vs literature)")
    for name, dd, lit in checks:
        print(f"  {name:<30} {dd:+6.1f} ft ({100*dd/d_ref:+.1f}%)   lit: {lit}")

    # figure
    rh_fine = np.linspace(0, 100, 21)
    colors = {60: "#2a78d6", 75: "#1baf7a", 90: "#eb6834"}
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=200)
    for t in temps:
        d = [carry(air_density(t, r / 100, P_SEA)) for r in rh_fine]
        ax.plot(rh_fine, d, color=colors[t], lw=2.2)
        ax.annotate(f"{t}°F  ({d[-1]-d[0]:+.1f} ft from 0→100% RH)", (100, d[-1]),
                    xytext=(6, 0), textcoords="offset points", va="center",
                    color="#0b0b0b", fontsize=10)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Relative humidity (%)")
    ax.set_ylabel("Carry distance (ft)")
    fig.text(0.07, 0.95, "Humidity barely moves a home-run ball; temperature does",
             fontsize=13, fontweight="bold", color="#0b0b0b")
    fig.text(0.07, 0.905, f"Model: {EV_MPH:.0f} mph exit velocity, {LA_DEG:.0f}° launch, "
             "sea level, C_d = 0.35, C_L = 0.20", fontsize=9, color="#52514e")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_color("#b5b4ae")
    ax.spines["bottom"].set_color("#b5b4ae")
    ax.tick_params(colors="#52514e")
    ax.grid(axis="y", color="#e6e5e0", lw=0.8)
    fig.subplots_adjust(left=0.1, right=0.68, top=0.85)
    fig.savefig(out / "distance_vs_rh.png", facecolor="white")
    print(f"\nSaved {out / 'distance_vs_rh.png'}")


if __name__ == "__main__":
    main()
