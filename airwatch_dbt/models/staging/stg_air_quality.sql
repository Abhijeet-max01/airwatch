select
    city,
    location_id,
    value as pm25_value,
    recorded_at,
    inserted_at
from {{ source('airwatch_raw', 'raw_air_quality') }}