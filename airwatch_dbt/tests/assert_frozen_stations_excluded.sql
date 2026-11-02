-- Fails if any unusable (frozen / gappy) station leaks into the clean data.
select c.location_id
from {{ ref('int_station_hourly_clean') }} c
join {{ ref('int_station_quality') }} q on q.location_id = c.location_id
where not q.is_usable
