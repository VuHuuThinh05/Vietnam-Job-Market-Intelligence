# VietJobs dbt Models

This directory contains the dbt project for transforming the raw VietJobs data in PostgreSQL.

## Models

- `staging/stg_vietjobs.sql`: standardizes source fields and derives salary status.
- `marts/mart_category_summary.sql`: summarizes recruitment data by occupational category.
- `marts/mart_contract_summary.sql`: summarizes recruitment data by category and contract type.

## Run

From the repository root, with the virtual environment activated and PostgreSQL running:

```powershell
dbt debug --project-dir .\vietjobs_dbt --profiles-dir .
dbt run --project-dir .\vietjobs_dbt --profiles-dir .
dbt test --project-dir .\vietjobs_dbt --profiles-dir .
```

The local `profiles.yml` contains connection settings and must not be committed.
