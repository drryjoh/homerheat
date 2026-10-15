"""Shared data prep for the humidity / home-run analysis.

    from analysis.prep import load_outdoor
    bb = load_outdoor()               # outdoor batted balls at real home parks
    air = air_balls(bb)               # LA 20-40 deg, EV >= 90 mph, distance present
    g = load_games(outdoor=True)      # one row per game, same filters

All weather is ERA5 at the hour nearest scheduled first pitch (see notes/data.md).
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
RESULTS = ROOT / "analysis" / "results"

# Neutral / one-off sites (notes/baseball.md section 3): London, Mexico City, Monterrey, Tokyo, Seoul,
# San Juan, Field of Dreams, Rickwood, Williamsport, Fort Bragg, Omaha, Bristol.
SPECIAL_VENUES = {5381, 5340, 2701, 2397, 5150, 2535, 5445, 3949, 2735, 5010, 5365, 6130}

# Fence / dimension changes: venue_id -> first season of each new configuration.
# MIA second move-in was "the 2020 offseason"; too few open-roof MIA games to date it, we use 2021.
PARK_CHANGES = {
    2: [2022, 2025],      # BAL Camden LF wall back (2022), partly in (2025)
    14: [2023],           # TOR Rogers Centre alleys in, walls up
    2394: [2023],         # DET Comerica CF in
    2395: [2020],         # SF Oracle CF/Triples Alley in
    3289: [2023],         # NYM Citi RF in
    4169: [2016, 2021],   # MIA fences in twice
}
COORS = 19


def spray_angle(hc_x, hc_y):
    """Spray angle in degrees from Statcast hit coordinates; 0 = CF, + = toward RF (1B side)."""
    return np.degrees(np.arctan2(hc_x - 125.42, 198.27 - hc_y))


def wind_components(speed, from_deg, azimuth_deg):
    """Project ERA5 10 m wind onto the park axis.

    from_deg is where the wind comes FROM; azimuth_deg is the home plate -> CF bearing.
    Returns (out_to_cf, toward_rf): out_to_cf > 0 = blowing out. Verified with StatsAPI
    'Out To CF'/'In From CF' strings and Wrigley HR/FB (12.5% -> 28% from bottom to top wind quintile).
    """
    rel = np.deg2rad(np.asarray(from_deg, float) - np.asarray(azimuth_deg, float))
    out = -speed * np.cos(rel)
    # Wind blows toward from+180; component along bearing az+90 (toward RF side).
    rf = -speed * np.sin(rel)
    return out, rf


def park_period(venue_id, year):
    """'venue_id' or 'venue_id:YYYY' label for each park configuration."""
    out = venue_id.astype(str).to_numpy(dtype=object)
    for vid, years in PARK_CHANGES.items():
        m = (venue_id == vid).to_numpy()
        start = np.full(m.sum(), "base", dtype=object)
        y = year.to_numpy()[m]
        for yr in years:
            start[y >= yr] = str(yr)
        out[m] = [f"{vid}:{s}" for s in start]
    return pd.Series(out, index=venue_id.index)


def add_game_features(df):
    """Columns that only depend on the game row (works for games or batted balls)."""
    df = df.copy()
    df["park_period"] = park_period(df["venue_id"], df["year"])
    df["wind_out"], df["wind_rf"] = wind_components(
        df["wind_speed_10m"], df["wind_direction_10m"], df["azimuth_deg"])
    df["tracking"] = np.where(df["year"] >= 2020, "hawkeye", "trackman")
    df["humidor_all"] = df["year"] >= 2022
    df["season_month"] = df["year"].astype(str) + "-" + df["month"].astype(int).astype(str).str.zfill(2)
    cond = df["condition"].fillna("")
    df["rain_statsapi"] = cond.str.contains("Rain|Drizzle", case=False)
    df["rain_era5"] = df["precipitation"] > 0.1
    # Density split into dry part and the vapour part (Delta rho / rho ~ -0.378 e/P).
    df["vapor_density_pct"] = -0.378 * df["vapor_pressure_hpa"] / df["surface_pressure"] * 100
    return df


def _filter(df, outdoor=True):
    keep = ~df["venue_id"].isin(SPECIAL_VENUES) & df["azimuth_deg"].notna()
    if outdoor is True:
        keep &= ~df["roof_closed"]
    elif outdoor == "closed":
        keep &= df["roof_closed"]
    return df[keep]


def add_terciles(df, games):
    """Dew-point terciles (cut points from outdoor game-level dew point)."""
    cuts = games["dew_point_2m"].quantile([1 / 3, 2 / 3]).to_numpy()
    df = df.copy()
    df["humid_tercile"] = pd.cut(df["dew_point_2m"], [-np.inf, *cuts, np.inf],
                                 labels=["dry", "mid", "humid"])
    return df, cuts


def load_games(outdoor=True):
    """Game-level table. outdoor=True: roof open/open-air; 'closed': roof-closed only; False: all."""
    raw = pd.read_parquet(PROC / "games.parquet")
    g = add_game_features(_filter(raw, outdoor))
    g, _ = add_terciles(g, _filter(raw, True))
    return g


def load_outdoor(outdoor=True):
    """Batted balls with all features. outdoor as in load_games()."""
    bb = pd.read_parquet(PROC / "batted_balls.parquet")
    bb = add_game_features(_filter(bb, outdoor))
    bb["spray"] = spray_angle(bb["hc_x"], bb["hc_y"])
    # Pull-side angle: + = pulled (LF for RHB, RF for LHB).
    bb["pull"] = np.where(bb["stand"] == "L", bb["spray"], -bb["spray"])
    bb, _ = add_terciles(bb, _filter(pd.read_parquet(PROC / "games.parquet"), True))
    return bb


def air_balls(bb):
    """Primary analysis sample: LA 20-40 deg, EV >= 90 mph, distance and spray observed."""
    m = (bb["launch_angle"].between(20, 40) & (bb["launch_speed"] >= 90)
         & bb["hit_distance_sc"].notna() & bb["spray"].notna())
    a = bb[m].copy()
    a["pull"] = a["pull"].clip(-50, 50)
    return a


if __name__ == "__main__":
    bb = load_outdoor()
    a = air_balls(bb)
    print(f"outdoor BIP {len(bb):,}  games {bb.game_pk.nunique():,}  air balls {len(a):,}  "
          f"HR among air balls {a.is_hr.sum():,} / all HR {bb.is_hr.sum():,}")
    print(a.groupby("park_period").size().sort_index().to_string())


def _hourly(vid, season):
    import json
    path = ROOT / "data" / "raw" / "weather" / f"{vid}_{season}.json"
    if not path.exists():
        return None
    h = pd.DataFrame(json.loads(path.read_text())["hourly"])
    h["t"] = pd.to_datetime(h.pop("time"))
    rad = np.deg2rad(h["wind_direction_10m"])
    h["u"], h["v"] = -h["wind_speed_10m"] * np.sin(rad), -h["wind_speed_10m"] * np.cos(rad)
    return h


def ball_time_weather(df):
    """ERA5 linearly interpolated to each ball's estimated time:
    scheduled first pitch + (inning - 1) x minutes-per-inning (20 before 2023, 17.5 from the 2023 pitch clock).
    Returns df with *_ball columns (temperature, dew point, RH, pressure, wind_out, wind_rf, vapor pressure)."""
    mpi = np.where(df["year"] >= 2023, 17.5, 20.0)
    t = (df["game_datetime_utc"].dt.tz_localize(None)
         + pd.to_timedelta((df["inning"].astype(float).fillna(5) - 1) * mpi + 10, unit="min"))
    cols = ["temperature_2m", "dew_point_2m", "relative_humidity_2m", "surface_pressure", "u", "v"]
    out = pd.DataFrame(index=df.index, columns=[c + "_ball" for c in cols], dtype=float)
    for (vid, season), idx in df.groupby(["venue_id", "season"]).groups.items():
        h = _hourly(vid, season)
        if h is None:
            continue
        x = (h["t"] - pd.Timestamp("1970-01-01")).dt.total_seconds().to_numpy()
        xi = (t.loc[idx] - pd.Timestamp("1970-01-01")).dt.total_seconds().to_numpy()
        for c in cols:
            out.loc[idx, c + "_ball"] = np.interp(xi, x, h[c].to_numpy(float))
    az = np.deg2rad(df["azimuth_deg"])
    out["wind_out_ball"] = out["u_ball"] * np.sin(az) + out["v_ball"] * np.cos(az)
    out["wind_rf_ball"] = out["u_ball"] * np.cos(az) - out["v_ball"] * np.sin(az)
    td = out["dew_point_2m_ball"]
    out["vapor_pressure_hpa_ball"] = 6.112 * np.exp(17.67 * td / (td + 243.5))
    return df.join(out.drop(columns=["u_ball", "v_ball"]))
