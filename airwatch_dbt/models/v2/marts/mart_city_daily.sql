-- City-level daily summary with Indian AQI category (bands come from seeds/aqi_breakpoints.csv).
with daily as (
    select
        city,
        ts_ist::date as reading_date,
        avg(avg_pm25) as avg_pm25,
        max(avg_pm25) as peak_hourly_pm25,
        count(*)      as hours_reporting
    from {{ ref('mart_city_hourly') }}
    group by 1, 2
)
select
    d.city,
    d.reading_date,
    round(d.avg_pm25::numeric, 1)         as avg_pm25,
    round(d.peak_hourly_pm25::numeric, 1) as peak_hourly_pm25,
    d.hours_reporting,
    d.hours_reporting >= {{ var('min_hours_per_day') }} as is_complete_day,
    b.category   as aqi_category,
    b.sort_order as aqi_level,
    d.avg_pm25 > {{ var('naaqs_pm25_24h') }} as above_national_standard
from daily d
left join {{ ref('aqi_breakpoints') }} b
  on d.avg_pm25 >= b.pm25_min and d.avg_pm25 < b.pm25_max
