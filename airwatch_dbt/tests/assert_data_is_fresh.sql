-- Warns (does not fail) when the newest reading is older than the allowed age.
{{ config(severity='warn') }}
select max(ts_utc) as newest_reading
from {{ ref('stg_pm25_hourly') }}
having max(ts_utc) < now() - interval '{{ var("max_data_age_hours") }} hours'
