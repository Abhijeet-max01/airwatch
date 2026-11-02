"""Anomaly detection for hourly PM2.5 readings.

Three detectors, combined:
  1. Hampel filter  - robust z-score vs the station's own rolling median (adapts per station)
  2. Stuck sensor   - same value repeated for many hours in a row
  3. Isolation Forest (ML) - unusual combination of level / jump / volatility;
                             counts only if it is also moderately far from the local median
The old hardcoded rule (value > 500) is kept only as a baseline to compare against.
"""
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

WINDOW = 25            # hours, centred rolling window
MIN_PERIODS = 8
HAMPEL_K = 6.0         # flag if |robust z| > 6
CONSENSUS_Z = 3.0      # Isolation Forest must also see |z| > 3
STUCK_HOURS = 12
IF_CONTAMINATION = 0.003
OLD_RULE = 500


def mad_scale(x):
    med = np.nanmedian(x)
    return 1.4826 * np.nanmedian(np.abs(x - med))


def station_features(g):
    g = g.drop_duplicates("ts").copy()
    g["hr"] = g["ts"].dt.floor("h")
    g = g.drop_duplicates("hr").set_index("hr").sort_index()
    grid = pd.date_range(g.index.min(), g.index.max(), freq="h")
    s = g["value"].astype(float).reindex(grid)

    roll = s.rolling(WINDOW, center=True, min_periods=MIN_PERIODS)
    med = roll.median()
    scale = roll.apply(mad_scale, raw=True)
    scale_f = pd.Series(
        np.maximum.reduce([scale.fillna(0).values, (0.15 * med).fillna(0).values, np.full(len(s), 3.0)]),
        index=s.index,
    )
    z = (s - med) / scale_f

    # stuck = same value for many consecutive readings (computed on real readings, so gaps don't hide it)
    v = g["value"].astype(float)
    run_id = (v != v.shift()).cumsum()
    stuck_real = v.groupby(run_id).transform("size") >= STUCK_HOURS
    stuck = stuck_real.reindex(grid, fill_value=False)

    log_v = np.log1p(s)
    d1 = log_v - log_v.shift(1)
    d24 = log_v - np.log1p(med)
    vol6 = s.rolling(6, min_periods=3).std() / (s.rolling(6, min_periods=3).mean() + 1)

    out = pd.DataFrame(index=g.index)
    for col in ["location_id", "sensor_id", "ts", "value", "name", "city"]:
        out[col] = g[col]
    out["rolling_median"] = med.loc[g.index]
    out["robust_z"] = z.loc[g.index]
    out["stuck"] = stuck.loc[g.index]
    out["f_level"] = log_v.loc[g.index]
    out["f_jump"] = d1.loc[g.index]
    out["f_vs_median"] = d24.loc[g.index]
    out["f_vol"] = vol6.loc[g.index]
    return out


def detect(df):
    parts = [station_features(g) for _, g in df.groupby(["location_id", "sensor_id"])]
    res = pd.concat(parts, ignore_index=True)

    res["rule_gt500"] = res["value"] > OLD_RULE
    res["hampel"] = res["robust_z"].abs() > HAMPEL_K

    feats = ["f_level", "f_jump", "f_vs_median", "f_vol"]
    X = res[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    model = IsolationForest(n_estimators=200, contamination=IF_CONTAMINATION, random_state=42)
    res["iforest"] = model.fit_predict(X) == -1

    res["is_anomaly"] = (
        res["hampel"] | res["stuck"] | (res["iforest"] & (res["robust_z"].abs() > CONSENSUS_Z))
    )
    return res


def summarize(res):
    n = len(res)
    print(f"Readings analysed:             {n}")
    print(f"Old rule (> {OLD_RULE}) flags:        {int(res.rule_gt500.sum())}")
    print(f"Hampel (per-station) flags:    {int(res.hampel.sum())}")
    print(f"Stuck-sensor flags:            {int(res.stuck.sum())}")
    print(f"Isolation Forest flags:        {int(res.iforest.sum())}")
    print(f"FINAL anomalies:               {int(res.is_anomaly.sum())}  ({100*res.is_anomaly.mean():.2f}%)")
    old = res[res.rule_gt500]
    print(f"\nOld-rule flags the new method also caught: {int(old.is_anomaly.sum())} of {len(old)}")
    print(f"New method found that the old rule missed: {int((res.is_anomaly & ~res.rule_gt500).sum())}")
    kept = res[(res.value > 200) & (res.value <= OLD_RULE) & ~res.is_anomaly]
    print(f"Severe-but-real readings (200-500) kept:    {len(kept)}")


def show_top(res, k=12):
    top = res[res.is_anomaly].copy()
    top["abs_z"] = top["robust_z"].abs()
    top = top.sort_values("abs_z", ascending=False).head(k)
    print("\nTop flagged readings:")
    for _, r in top.iterrows():
        why = []
        if r.hampel: why.append("spike")
        if r.stuck: why.append("stuck")
        if r.iforest: why.append("model")
        print(f"  {str(r['name'])[:30]:<30} {str(r.ts)[:16]}  value={r.value:>6.1f}  "
              f"local_median={r.rolling_median:>6.1f}  [{'+'.join(why)}]")


def main():
    import psycopg2
    from psycopg2.extras import execute_values
    from dotenv import load_dotenv
    load_dotenv()
    conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"), connect_timeout=15)
    cur = conn.cursor()
    cur.execute("""select p.location_id, p.sensor_id, p.ts, p.value, s.name, s.city
                   from pm25_hourly p join stations s using (location_id)
                   where p.value is not null order by 1, 2, 3""")
    df = pd.DataFrame(cur.fetchall(), columns=["location_id", "sensor_id", "ts", "value", "name", "city"])
    print(f"Loaded {len(df)} readings from {df.location_id.nunique()} stations\n")

    res = detect(df)
    summarize(res)
    show_top(res)

    cur.execute("""
    create table if not exists pm25_anomalies (
        location_id    integer not null,
        sensor_id      integer not null,
        ts             timestamptz not null,
        value          double precision,
        rolling_median double precision,
        robust_z       double precision,
        rule_gt500     boolean,
        hampel         boolean,
        stuck          boolean,
        iforest        boolean,
        is_anomaly     boolean,
        detected_at    timestamptz default now(),
        primary key (location_id, sensor_id, ts)
    )""")
    cur.execute("truncate pm25_anomalies")
    flagged = res[res.is_anomaly | res.rule_gt500]

    def f(x):
        return None if pd.isna(x) else float(x)

    rows = [
        (int(r.location_id), int(r.sensor_id), r.ts.to_pydatetime(), f(r.value), f(r.rolling_median),
         f(r.robust_z), bool(r.rule_gt500), bool(r.hampel), bool(r.stuck), bool(r.iforest), bool(r.is_anomaly))
        for r in flagged.itertuples()
    ]
    if rows:
        execute_values(cur, """insert into pm25_anomalies
            (location_id, sensor_id, ts, value, rolling_median, robust_z,
             rule_gt500, hampel, stuck, iforest, is_anomaly) values %s""", rows)
    conn.commit()
    conn.close()
    print(f"\nSaved {len(rows)} flagged rows to table pm25_anomalies")


if __name__ == "__main__":
    main()
