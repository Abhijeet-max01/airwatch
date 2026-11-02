-- After anomaly removal, no city-hour should be negative or absurdly high.
select * from {{ ref('mart_city_hourly') }}
where avg_pm25 < 0 or avg_pm25 > 1000
