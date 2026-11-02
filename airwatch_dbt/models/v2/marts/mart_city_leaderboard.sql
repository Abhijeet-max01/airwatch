-- Which city had the worst air recently, and how many days broke the national standard?
with latest as (
    select max(reading_date) as max_date from {{ ref('mart_city_daily') }}
)
select
    d.city,
    round(avg(d.avg_pm25)::numeric, 1) as avg_pm25,
    count(*)                           as days_tracked,
    count(*) filter (where d.above_national_standard) as days_above_standard,
    round(100.0 * count(*) filter (where d.above_national_standard) / count(*), 1) as pct_days_above_standard,
    rank() over (order by avg(d.avg_pm25) desc) as pollution_rank
from {{ ref('mart_city_daily') }} d
cross join latest l
where d.is_complete_day
  and d.reading_date > l.max_date - {{ var('leaderboard_days') }}
group by d.city
