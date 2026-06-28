select *
from {{ ref('mart_city_pollution_trends') }}
where max_pm25 > 500 and likely_sensor_error = false