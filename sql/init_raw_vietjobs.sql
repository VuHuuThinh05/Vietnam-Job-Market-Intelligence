-- Initialize a NEW local vietjobs PostgreSQL database before first ingestion.
-- Intentionally mirrors the source CSV's 18 columns; source values are preserved.
CREATE TABLE IF NOT EXISTS public.raw_vietjobs (
    job_title TEXT,
    location TEXT,
    country TEXT,
    qualifications TEXT,
    technical_skills TEXT,
    soft_skills TEXT,
    languages_required TEXT,
    experience_required TEXT,
    salary TEXT,
    contract_type TEXT,
    working_hours TEXT,
    benefits TEXT,
    description TEXT,
    requirements_text TEXT,
    category TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    salary_avg TEXT
);
