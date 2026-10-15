"""Download Statcast balls in play per regular season.

Usage:
    python src/fetch_statcast.py --years 2015-2025
    python src/fetch_statcast.py --years 2019 2023
    python src/fetch_statcast.py --start 2024-04-01 --end 2024-04-03   # quick test

Writes data/raw/statcast_{year}.parquet (skips years already saved).
"""
import argparse
from pathlib import Path

import pandas as pd
from pybaseball import cache, statcast

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

COLS = ["game_pk", "game_date", "home_team", "away_team", "batter", "pitcher",
        "stand", "p_throws", "events", "bb_type", "launch_speed", "launch_angle",
        "hit_distance_sc", "hc_x", "hc_y", "inning"]


def parse_years(tokens):
    years = []
    for t in tokens:
        if "-" in t:
            a, b = map(int, t.split("-"))
            years += range(a, b + 1)
        else:
            years.append(int(t))
    return years


def balls_in_play(start, end):
    df = statcast(start_dt=start, end_dt=end, parallel=True)
    df = df[(df["type"] == "X") & (df["game_type"] == "R")]
    out = df[COLS].copy()
    out["game_date"] = pd.to_datetime(out["game_date"])
    return out.sort_values(["game_date", "game_pk"]).reset_index(drop=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--years", nargs="+", default=["2015-2025"])
    p.add_argument("--start")
    p.add_argument("--end")
    args = p.parse_args()
    cache.enable()
    RAW.mkdir(parents=True, exist_ok=True)

    if args.start:
        df = balls_in_play(args.start, args.end or args.start)
        print(df.head(), "\n", len(df), "balls in play;", (df.events == "home_run").sum(), "HR")
        return

    for year in parse_years(args.years):
        path = RAW / f"statcast_{year}.parquet"
        if path.exists():
            print(f"{year}: already saved, skipping")
            continue
        # Mar 1 - Nov 30 covers every regular season (incl. Seoul/Tokyo openers); game_type filters.
        df = balls_in_play(f"{year}-03-01", f"{year}-11-30")
        df.to_parquet(path, index=False)
        print(f"{year}: {len(df):,} balls in play, {(df.events == 'home_run').sum():,} HR -> {path}")


if __name__ == "__main__":
    main()
