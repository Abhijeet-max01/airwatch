select city, ts_ist, count(*) as n
from {{ ref('mart_city_hourly') }}
group by 1, 2
having count(*) > 1
