"""Join Statcast batted balls, StatsAPI games and ERA5 first-pitch weather.

Usage:
    python src/build_dataset.py

Writes:
    data/processed/batted_balls.parquet  one row per ball in play
    data/processed/games.parquet         one row per game (weather + HR aggregates)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from physics.air import air_density, sat_vapor_pressure  # noqa: E402

RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"

FIXED_DOMES = {12: "Tropicana Field", 2397: "Tokyo Dome", 5150: "Gocheok Sky Dome"}
RETRACTABLE = {15: "Chase Field", 14: "Rogers Centre", 32: "Miller/American Family Field",
               2392: "Minute Maid/Daikin Park", 4169: "Marlins/loanDepot park",
               5325: "Globe Life Field", 680: "Safeco/T-Mobile Park (open-sided)"}


def load_games():
    g = pd.read_parquet(RAW / "games.parquet")
    w = pd.read_parquet(RAW / "game_weather.parquet")
    g = g.merge(w, on="game_pk", how="left")

    # StatsAPI wind string, e.g. "6 mph, In From CF"
    wind = g["wind_reported"].str.extract(r"(\d+)\s*mph,?\s*(.*)")
    g["wind_mph_reported"] = pd.to_numeric(wind[0], errors="coerce")
    g["wind_dir_reported"] = wind[1].str.strip().replace("", np.nan)

    # Physics: ERA5 is deg C, %, hPa
    t_k = g["temperature_2m"] + 273.15
    g["vapor_pressure_hpa"] = g["relative_humidity_2m"] / 100 * sat_vapor_pressure(t_k) / 100
    g["air_density"] = air_density(g["temperature_2m"] * 9 / 5 + 32,
                                   g["relative_humidity_2m"] / 100,
                                   g["surface_pressure"] * 100)

    cond = g["condition"].fillna("")
    g["is_dome_venue"] = g["venue_id"].isin(FIXED_DOMES)
    g["has_retractable_roof"] = g["venue_id"].isin(RETRACTABLE)
    g["roof_closed"] = cond.isin(["Dome", "Roof Closed"]) | g["is_dome_venue"]
    g["is_raining"] = cond.str.contains("Rain|Drizzle") | (g["precipitation"] > 0.1)
    g["year"] = g["season"]
    g["month"] = pd.to_datetime(g["official_date"]).dt.month
    return g


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    games = load_games()
    bb = pd.concat([pd.read_parquet(p) for p in sorted(RAW.glob("statcast_*.parquet"))],
                   ignore_index=True)
    for c in ["launch_speed", "launch_angle", "hit_distance_sc", "hc_x", "hc_y"]:
        bb[c] = pd.to_numeric(bb[c], errors="coerce").astype("float64")
    bb["is_hr"] = bb["events"].eq("home_run")
    bb["is_fly_ball"] = bb["bb_type"].eq("fly_ball")

    agg = bb.groupby("game_pk").agg(
        n_batted_balls=("is_hr", "size"), n_hr=("is_hr", "sum"),
        n_fly_balls=("is_fly_ball", "sum"),
        mean_hr_distance=("hit_distance_sc", lambda s: s[bb.loc[s.index, "is_hr"]].mean()),
    ).reset_index()
    games = games.merge(agg, on="game_pk", how="left")
    games["has_statcast"] = games["n_batted_balls"].notna()
    for c in ["n_batted_balls", "n_hr", "n_fly_balls"]:
        games[c] = games[c].astype("Int64")
    games.to_parquet(OUT / "games.parquet", index=False)

    game_cols = [c for c in games.columns
                 if c not in {"n_batted_balls", "n_hr", "n_fly_balls", "mean_hr_distance", "has_statcast"}]
    out = bb.merge(games[game_cols], on="game_pk", how="left")
    out.to_parquet(OUT / "batted_balls.parquet", index=False)

    print(f"games: {len(games):,} ({(~games.has_statcast).sum()} without Statcast rows)")
    print(f"batted balls: {len(out):,} ({out['venue_id'].isna().sum()} not matched to a game)")
    t = out.groupby("year").agg(batted_balls=("is_hr", "size"), hr=("is_hr", "sum"),
                                hr_dist_missing_pct=("hit_distance_sc",
                                                     lambda s: 100 * s[out.loc[s.index, "is_hr"]].isna().mean()))
    gy = games.groupby("year").agg(games=("game_pk", "size"),
                                   weather_pct=("temperature_2m", lambda s: 100 * s.notna().mean()),
                                   indoor_pct=("roof_closed", lambda s: 100 * s.mean()))
    print(gy.join(t).round(1).to_string())


if __name__ == "__main__":
    main()
