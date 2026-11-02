-- City-level PM2.5 per hour (IST), averaged across trusted stations.
select
    city,
    ts_ist,
    round(avg(pm25)::numeric, 1) as avg_pm25,
    count(*)                     as stations_reporting
from {{ ref('int_station_hourly_clean') }}
group by 1, 2
