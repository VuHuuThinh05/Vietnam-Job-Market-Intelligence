
with source as (

    select * 
    from public.raw_vietjobs

),

cleaned as (

    select
        trim(job_title) as job_title,
        nullif(trim(location), '') as location,
        nullif(trim(country), '') as country,

        nullif(trim(qualifications), '') as qualifications,
        nullif(trim(technical_skills), '') as technical_skills,
        nullif(trim(soft_skills), '') as soft_skills,
        nullif(trim(languages_required), '') as languages_required,

        nullif(trim(experience_required), '') as experience_required,
        nullif(trim(salary), '') as salary,
        nullif(trim(contract_type), '') as contract_type,
        nullif(trim(working_hours), '') as working_hours,

        nullif(trim(benefits), '') as benefits,
        nullif(trim(description), '') as description,
        nullif(trim(requirements_text), '') as requirements_text,

        trim(category) as category,

        salary_min,
        salary_max,
        salary_avg,


        case
            when salary_min > 0 and salary_max < salary_min
                then 'invalid_range'
            when salary_min = 0 and salary_max = 0
                and salary_avg = 'Thoả thuận'
                then 'negotiable'
            when salary_min = 0 and salary_max = 0
                then 'unavailable'
            else 'provided'
        end as salary_status


    from source

)

select * from cleaned
