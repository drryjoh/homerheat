"""ERA5 hourly weather at first pitch for every game (Open-Meteo archive, no key).

Usage:
    python src/fetch_weather.py

Reads data/raw/games.parquet. Makes one request per venue per season, caching each
JSON response in data/raw/weather/{venue_id}_{season}.json, then picks the hour
nearest first pitch. Writes data/raw/game_weather.parquet (one row per game_pk).
"""
import json
import time
from pathlib import Path

import pandas as pd
import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
CACHE = RAW / "weather"
URL = "https://archive-api.open-meteo.com/v1/archive"
HOURLY = ["temperature_2m", "relative_humidity_2m", "dew_point_2m", "surface_pressure",
          "pressure_msl", "precipitation", "rain", "wind_speed_10m", "wind_direction_10m"]


def fetch(venue_id, season, lat, lon, elev_m, start, end):
    path = CACHE / f"{venue_id}_{season}.json"
    if path.exists():
        return json.loads(path.read_text())
    params = {"latitude": lat, "longitude": lon, "elevation": elev_m,
              "start_date": start, "end_date": end, "hourly": ",".join(HOURLY),
              "models": "era5", "timezone": "GMT", "wind_speed_unit": "ms"}
    for attempt in range(8):
        r = requests.get(URL, params=params, timeout=120)
        if r.status_code == 429:  # rate limited: back off (minutely/hourly limits)
            wait = 60 * (attempt + 1)
            print(f"  429, waiting {wait}s")
            time.sleep(wait)
            continue
        r.raise_for_status()
        path.write_text(r.text)
        time.sleep(1.0)  # be polite
        return r.json()
    raise RuntimeError(f"gave up on {venue_id} {season}")


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    games = pd.read_parquet(RAW / "games.parquet")
    games["hour_utc"] = games["game_datetime_utc"].dt.round("h").dt.tz_localize(None)
    out = []
    groups = games.groupby(["venue_id", "season"])
    for i, ((vid, season), g) in enumerate(groups, 1):
        start = g["hour_utc"].min().strftime("%Y-%m-%d")
        end = g["hour_utc"].max().strftime("%Y-%m-%d")
        d = fetch(vid, season, g["lat"].iloc[0], g["lon"].iloc[0],
                  round(g["elevation_ft"].iloc[0] * 0.3048), start, end)
        h = pd.DataFrame(d["hourly"])
        h["hour_utc"] = pd.to_datetime(h.pop("time"))
        h["era5_grid_lat"], h["era5_grid_lon"] = d["latitude"], d["longitude"]
        out.append(g[["game_pk", "hour_utc"]].merge(h, on="hour_utc", how="left"))
        if i % 25 == 0:
            print(f"{i}/{groups.ngroups} venue-seasons")
    df = pd.concat(out, ignore_index=True).rename(columns={"hour_utc": "weather_hour_utc"})
    df.to_parquet(RAW / "game_weather.parquet", index=False)
    print(f"saved {len(df)} games, {df['temperature_2m'].isna().sum()} missing temperature")


if __name__ == "__main__":
    main()
