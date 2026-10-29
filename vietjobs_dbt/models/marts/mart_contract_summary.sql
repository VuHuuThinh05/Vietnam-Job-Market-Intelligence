
select
    category,
    contract_type,
    count(*) as total_jobs,

    count(*) filter (
        where salary_status = 'negotiable'
    ) as negotiable_jobs,

    count(*) filter (
        where salary_status = 'provided'
    ) as jobs_with_salary

from {{ ref('stg_vietjobs') }}
group by
    category,
    contract_type
