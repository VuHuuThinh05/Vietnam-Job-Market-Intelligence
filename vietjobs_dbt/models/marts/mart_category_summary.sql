
select
    category,
    count(*) as total_jobs,
    count(distinct location) as total_locations,

    count(*) filter (
        where salary_status = 'negotiable'
    ) as negotiable_jobs,

    count(*) filter (
        where salary_status = 'provided'
    ) as jobs_with_salary,

    count(*) filter (
        where salary_status = 'unavailable'
    ) as salary_unavailable_jobs,

    count(*) filter (
        where salary_status = 'invalid_range'
    ) as invalid_salary_jobs,

    round(
        avg(
            (salary_min + salary_max)::numeric / 2
        ) filter (
            where salary_min > 0
              and salary_max >= salary_min
        ),
        2
    ) as avg_salary_midpoint_million

from {{ ref('stg_vietjobs') }}
group by category
