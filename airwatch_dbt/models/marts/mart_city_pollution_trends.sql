select
    city,
    reading_date,
    avg_pm25,
    max_pm25,
    num_readings,
    case
        when max_pm25 > 500 then true
        else false
    end as likely_sensor_error
from {{ ref('int_daily_city_pm25') }}
order by city, reading_date