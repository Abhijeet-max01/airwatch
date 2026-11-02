-- Station report card: which sensors we trust and why not.
select
    *,
    row_number() over (partition by city order by is_usable desc, coverage desc) as rank_in_city
from {{ ref('int_station_quality') }}
