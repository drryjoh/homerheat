"""One row per completed MLB regular-season game from the StatsAPI schedule.

Usage:
    python src/fetch_games.py --years 2015-2025

Writes data/raw/games.parquet with game_pk, UTC first-pitch time, venue
(id, name, lat/lon, elevation) and the reported weather (condition, temp, wind).
Games whose schedule entry has no weather fall back to the live feed.
"""
import argparse
import time
from pathlib import Path

import pandas as pd
import requests

from fetch_statcast import parse_years

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
API = "https://statsapi.mlb.com/api"
# StatsAPI venue coordinates are missing or wrong for some (mostly neutral-site) parks.
# venue_id: (lat, lon, elevation_ft), checked against stadium locations on maps.
VENUE_FIX = {
    16: (33.7350, -84.3895, 1050),      # Turner Field, Atlanta (coords missing)
    2397: (35.7056, 139.7519, 100),     # Tokyo Dome
    2535: (18.4167, -66.0728, 70),      # Hiram Bithorn Stadium, San Juan
    2701: (25.7215, -100.3115, 1770),   # Estadio de Beisbol Monterrey
    2735: (41.2420, -77.0475, 520),     # Williamsport Little League Classic park
    3949: (33.5023, -86.8564, 600),     # Rickwood Field, Birmingham
    5010: (35.1400, -79.0060, 290),     # Fort Bragg Field
    5150: (37.4982, 126.8670, 100),     # Gocheok Sky Dome, Seoul
    5340: (19.4040, -99.0850, 7350),    # Estadio Alfredo Harp Helu, Mexico City
    5365: (41.2665, -95.9318, 1000),    # TD Ameritrade Park, Omaha
    5381: (51.5387, -0.0166, 40),       # London Stadium (API gives central London)
    5445: (42.4983, -91.0565, 1000),    # Field of Dreams, Dyersville IA
    6130: (36.5157, -82.2570, 1600),    # Bristol Motor Speedway (API lat is off by 5 deg)
}
SKIP_STATES = {"Postponed", "Cancelled", "Suspended"}  # suspended games reappear as Final on resume date


def get(url, **params):
    for attempt in range(5):
        try:
            r = requests.get(url, params=params, timeout=60)
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed: {url} {params}")


def season_games(year):
    d = get(f"{API}/v1/schedule", sportId=1, season=year, gameType="R",
            hydrate="weather,venue(location),team")
    rows = []
    for day in d["dates"]:
        for g in day["games"]:
            if g["status"]["abstractGameState"] != "Final" or g["status"]["detailedState"] in SKIP_STATES:
                continue
            v, loc = g["venue"], g["venue"].get("location", {})
            coords = loc.get("defaultCoordinates", {})
            w = g.get("weather", {})
            rows.append({
                "game_pk": g["gamePk"],
                "season": year,
                "official_date": g.get("officialDate"),
                "game_datetime_utc": g["gameDate"],
                "day_night": g.get("dayNight"),
                "double_header": g.get("doubleHeader"),
                "game_number": g.get("gameNumber"),
                "status": g["status"]["detailedState"],
                "home_team_abbr": g["teams"]["home"]["team"].get("abbreviation"),
                "away_team_abbr": g["teams"]["away"]["team"].get("abbreviation"),
                "venue_id": v["id"],
                "venue_name": v["name"],
                "venue_city": loc.get("city"),
                "venue_country": loc.get("country"),
                "lat": coords.get("latitude"),
                "lon": coords.get("longitude"),
                "elevation_ft": loc.get("elevation"),
                "azimuth_deg": loc.get("azimuthAngle"),
                "condition": w.get("condition"),
                "temp_f_reported": w.get("temp"),
                "wind_reported": w.get("wind"),
            })
    return pd.DataFrame(rows)


def fill_from_feed(df):
    """Fallback: per-game live feed for games missing weather or venue coordinates."""
    need = df["condition"].isna() | df["lat"].isna()
    print(f"  feed fallback for {need.sum()} games")
    for i in df.index[need]:
        gd = get(f"{API}/v1.1/game/{df.at[i, 'game_pk']}/feed/live")["gameData"]
        w = gd.get("weather", {})
        loc = gd.get("venue", {}).get("location", {})
        c = loc.get("defaultCoordinates", {})
        for col, val in [("condition", w.get("condition")), ("temp_f_reported", w.get("temp")),
                         ("wind_reported", w.get("wind")), ("lat", c.get("latitude")),
                         ("lon", c.get("longitude")), ("elevation_ft", loc.get("elevation"))]:
            if pd.isna(df.at[i, col]) and val is not None:
                df.at[i, col] = val
        time.sleep(0.2)
    return df


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--years", nargs="+", default=["2015-2025"])
    args = p.parse_args()
    frames = []
    for year in parse_years(args.years):
        g = season_games(year)
        print(f"{year}: {len(g)} games, {g['condition'].isna().sum()} missing weather, "
              f"{g['lat'].isna().sum()} missing coords")
        frames.append(fill_from_feed(g))
    df = pd.concat(frames, ignore_index=True)
    # A game can be listed twice (e.g. resumed); keep its earliest Final entry = real first pitch.
    df = df.sort_values("game_datetime_utc").drop_duplicates("game_pk", keep="first")
    df["game_datetime_utc"] = pd.to_datetime(df["game_datetime_utc"], utc=True)
    df["temp_f_reported"] = pd.to_numeric(df["temp_f_reported"], errors="coerce")
    for c in ["lat", "lon", "elevation_ft", "azimuth_deg"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for vid, (lat, lon, elev) in VENUE_FIX.items():
        df.loc[df.venue_id == vid, ["lat", "lon", "elevation_ft"]] = [lat, lon, elev]
    df = df.reset_index(drop=True)
    df.to_parquet(RAW / "games.parquet", index=False)
    print(f"saved {len(df)} games -> {RAW / 'games.parquet'}")


if __name__ == "__main__":
    main()
