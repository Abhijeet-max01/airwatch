-- Scores every station. A station is usable only if it is not frozen and has few gaps.
with per_station as (
    select
        location_id,
        station_name,
        city,
        agency,
        count(*)                                        as readings,
        count(distinct ts_utc)                          as hours_present,
        min(ts_utc)                                     as first_reading,
        max(ts_utc)                                     as last_reading,
        avg(case when is_stuck   then 1.0 else 0.0 end) as stuck_share,
        avg(case when is_anomaly then 1.0 else 0.0 end) as anomaly_share
    from {{ ref('stg_pm25_hourly') }}
    group by 1, 2, 3, 4
),
scored as (
    select
        *,
        hours_present / greatest(extract(epoch from (last_reading - first_reading)) / 3600 + 1, 1) as coverage
    from per_station
)
select
    location_id,
    station_name,
    city,
    agency,
    readings,
    first_reading,
    last_reading,
    round(stuck_share::numeric, 3)   as stuck_share,
    round(anomaly_share::numeric, 3) as anomaly_share,
    round(coverage::numeric, 3)      as coverage,
    (stuck_share <= {{ var('max_frozen_share') }}
        and coverage >= {{ var('min_coverage') }})   as is_usable,
    case
        when stuck_share > {{ var('max_frozen_share') }} then 'frozen sensor'
        when coverage < {{ var('min_coverage') }}        then 'too many gaps'
        else 'ok'
    end as quality_note
from scored
