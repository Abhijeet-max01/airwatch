with pollution as (
    select
        city,
        reading_date,
        avg_pm25,
        likely_sensor_error
    from {{ ref('mart_city_pollution_trends') }}
    where likely_sensor_error = false
),

weather as (
    select
        city,
        date(recorded_at) as reading_date,
        round(avg(temperature)::numeric, 2) as avg_temp,
        round(avg(humidity)::numeric, 2) as avg_humidity,
        round(avg(wind_speed)::numeric, 2) as avg_wind_speed
    from {{ source('airwatch_raw', 'raw_weather') }}
    group by city, date(recorded_at)
)

select
    p.city,
    p.reading_date,
    p.avg_pm25,
    w.avg_temp,
    w.avg_humidity,
    w.avg_wind_speed,
    case
        when w.avg_humidity > 70 and p.avg_pm25 > 50 then 'High humidity + High pollution'
        when w.avg_wind_speed > 5 and p.avg_pm25 < 40 then 'High wind + Low pollution'
        else 'Normal conditions'
    end as weather_pollution_pattern
from pollution p
inner join weather w
    on p.city = w.city
    and p.reading_date = w.reading_date
order by p.city, p.reading_date