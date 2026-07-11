select
    city,
    reading_date,
    avg_pm25,
    case
        when avg_pm25 <= 30 then 'Good'
        when avg_pm25 <= 60 then 'Satisfactory'
        when avg_pm25 <= 90 then 'Moderate'
        when avg_pm25 <= 120 then 'Poor'
        when avg_pm25 <= 250 then 'Very Poor'
        else 'Severe'
    end as aqi_category,
    likely_sensor_error
from {{ ref('mart_city_pollution_trends') }}
order by city, reading_date