select
    city,
    date(recorded_at) as reading_date,
    avg(pm25_value) as avg_pm25,
    max(pm25_value) as max_pm25,
    count(*) as num_readings
from {{ ref('stg_air_quality') }}
group by city, date(recorded_at)