-- One row per sensor-hour, with station details, IST time and anomaly flags attached.
select
    h.location_id,
    h.sensor_id,
    h.ts                              as ts_utc,
    h.ts at time zone 'Asia/Kolkata'  as ts_ist,
    h.value                           as pm25,
    s.name                            as station_name,
    s.city,
    s.agency,
    coalesce(a.is_anomaly, false)     as is_anomaly,
    coalesce(a.stuck, false)          as is_stuck
from {{ source('airwatch_pipeline', 'pm25_hourly') }} h
join {{ source('airwatch_pipeline', 'stations') }} s
  on s.location_id = h.location_id
left join {{ source('airwatch_pipeline', 'pm25_anomalies') }} a
  on  a.location_id = h.location_id
  and a.sensor_id   = h.sensor_id
  and a.ts          = h.ts
where h.value is not null
