-- "When is the air cleanest?" Average PM2.5 by hour of day (IST) over the recent window.
with latest as (
    select max(ts_ist) as max_ts from {{ ref('mart_city_hourly') }}
),
recent as (
    select h.*
    from {{ ref('mart_city_hourly') }} h
    cross join latest l
    where h.ts_ist >= l.max_ts - interval '{{ var("profile_days") }} days'
)
select
    city,
    extract(hour from ts_ist)::int                   as hour_of_day,
    round(avg(avg_pm25)::numeric, 1)                 as avg_pm25,
    count(*)                                         as samples,
    rank() over (partition by city order by avg(avg_pm25)) as cleanest_rank
from recent
group by city, extract(hour from ts_ist)::int
