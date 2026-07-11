select
    city,
    round(avg(avg_pm25)::numeric, 2) as overall_avg_pm25,
    round(max(max_pm25)::numeric, 2) as overall_max_pm25,
    count(*) as days_tracked,
    rank() over (order by avg(avg_pm25) desc) as pollution_rank
from {{ ref('int_daily_city_pm25') }}
where city not in (
    select distinct city
    from {{ ref('mart_city_pollution_trends') }}
    where likely_sensor_error = true
)
group by city
order by pollution_rank