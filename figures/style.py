"""Shared styling for every report figure: fonts, colors, slide size, US map base.

Import from a figure script with:
    from style import apply, C, DIVERGING, SEQ_BLUE, us_map_axes, save, load_csv
Colors follow the dataviz reference palette (blue/orange/aqua categorical; blue<->red diverging
with a neutral gray midpoint; one-hue blue sequential).
"""
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "analysis" / "results"
OUT = Path(__file__).resolve().parent / "out"
sys.path.insert(0, str(ROOT / "physics"))   # physics/air.py, physics/trajectory.py

SLIDE = (10, 5.6)    # inches; 16:9-friendly
DPI = 200

C = dict(
    blue="#2a78d6", orange="#eb6834", aqua="#1baf7a", yellow="#eda100", violet="#6250d6",
    red="#e34948",
    ink="#0b0b0b", ink2="#52514e", muted="#898781", grid="#e1e0d9", axis="#c3c2b7",
    surface="#fcfcfb", neutral="#f0efec", land="#f4f3ef", state="#c9c7bf",
)

# Diverging blue <-> red, gray midpoint (below average = blue, above = red).
DIVERGING = LinearSegmentedColormap.from_list(
    "hh_div", ["#104281", "#3987e5", "#9ec5f4", C["neutral"], "#f2a9a8", "#e34948", "#9c1f1f"])
# Sequential one-hue blue, light -> dark.
SEQ_BLUE = LinearSegmentedColormap.from_list(
    "hh_seq", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])

# Parks with a roof (open-roof games only are in the map tables; roof-closed games are excluded).
RETRACTABLE = {15: "AZ", 14: "TOR", 32: "MIL", 2392: "HOU", 4169: "MIA", 5325: "TEX"}
# Fixed dome: no outdoor games at all, so it is absent from the tables. Drawn as an 'x' for context.
DOMES = {"Tropicana Field (TB, dome)": (27.768, -82.653)}
# One-off / temporary home parks with < 100 outdoor games (shown small; noisy).
TEMPORARY = {2536, 2756}   # TD Ballpark (Dunedin), Sahlen Field (Buffalo)


def apply():
    """Global rcParams: system sans, recessive hairline axes, no top/right spines."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 11, "axes.labelcolor": C["ink2"], "axes.edgecolor": C["axis"],
        "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": C["grid"], "grid.linewidth": 0.6, "axes.axisbelow": True,
        "xtick.color": C["muted"], "ytick.color": C["muted"], "xtick.labelcolor": C["ink2"],
        "ytick.labelcolor": C["ink2"], "xtick.labelsize": 10, "ytick.labelsize": 10,
        "legend.frameon": False, "legend.fontsize": 10,
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "text.color": C["ink"], "lines.linewidth": 2,
    })


def load_csv(name):
    return pd.read_csv(RESULTS / name)


def title_block(fig, title, subtitle=None, y=0.975):
    """Slide-style headline + one-line subtitle, left aligned."""
    fig.text(0.015, y, title, fontsize=16, fontweight="bold", color=C["ink"], va="top")
    if subtitle:
        fig.text(0.015, y - 0.058, subtitle, fontsize=11, color=C["ink2"], va="top")


def footnote(fig, text, y=0.012):
    fig.text(0.015, y, text, fontsize=8.5, color=C["muted"], va="bottom")


def us_map_axes(fig, rect_or_spec, bbox=(-123.0, -70.0, 25.0, 48.0), pad=0.03):
    """Lower-48 Lambert Conformal axes with land, state lines and coastlines (Natural Earth 50m).

    bbox = (lon_min, lon_max, lat_min, lat_max) that must be fully visible (default: every MLB park).
    The extent is set in projected coordinates so no corner of the lower 48 gets clipped by the cone.
    """
    import numpy as np
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    proj = ccrs.LambertConformal(central_longitude=-96, central_latitude=39,
                                 standard_parallels=(33, 45))
    if isinstance(rect_or_spec, (list, tuple)):
        ax = fig.add_axes(rect_or_spec, projection=proj)
    else:
        ax = fig.add_subplot(rect_or_spec, projection=proj)
    lon, lat = np.meshgrid(np.linspace(bbox[0], bbox[1], 30), np.linspace(bbox[2], bbox[3], 30))
    xy = proj.transform_points(ccrs.PlateCarree(), lon.ravel(), lat.ravel())
    x0, x1, y0, y1 = xy[:, 0].min(), xy[:, 0].max(), xy[:, 1].min(), xy[:, 1].max()
    px, py = pad * (x1 - x0), pad * (y1 - y0)
    ax.set_extent((x0 - px, x1 + px, y0 - py, y1 + py), crs=proj)
    ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor=C["land"], edgecolor="none", zorder=0)
    ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor="white", edgecolor="none", zorder=0)
    ax.add_feature(cfeature.STATES.with_scale("50m"), edgecolor=C["state"], linewidth=0.4, zorder=1)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"), edgecolor=C["axis"], linewidth=0.6, zorder=1)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), edgecolor=C["axis"], linewidth=0.5, zorder=1)
    ax.spines["geo"].set_visible(False)
    ax.grid(False)
    return ax


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{name}.png"
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")
    return path
