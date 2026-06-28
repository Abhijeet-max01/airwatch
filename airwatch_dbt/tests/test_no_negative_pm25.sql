select *
from {{ ref('stg_air_quality') }}
where pm25_value < 0