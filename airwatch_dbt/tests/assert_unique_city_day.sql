select city, reading_date, count(*) as n
from {{ ref('mart_city_daily') }}
group by 1, 2
having count(*) > 1
