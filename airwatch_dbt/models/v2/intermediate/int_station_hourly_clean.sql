-- Trusted readings only: usable stations, anomalies removed. One row per station-hour.
select
    s.location_id,
    s.city,
    s.ts_ist,
    avg(s.pm25) as pm25
from {{ ref('stg_pm25_hourly') }} s
join {{ ref('int_station_quality') }} q
  on q.location_id = s.location_id
where q.is_usable
  and not s.is_anomaly
group by 1, 2, 3
