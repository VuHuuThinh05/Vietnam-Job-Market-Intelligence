# System Architecture, Pipeline Flow and Logical ERD

The implemented project is a **local batch analytics pipeline** based on a historical VietJobs CSV. Airflow uses `schedule=None` (manual execution, not scheduled ingestion).

## 1. System architecture

```mermaid
flowchart LR
  CSV["VietJobs CSV<br/>historical source"] --> ING["Python ingestion<br/>psycopg"]
  AIR["Apache Airflow<br/>manual DAG"] -.controls.-> ING
  AIR -.controls.-> DBT["dbt Core<br/>run and test"]
  ING --> RAW[("PostgreSQL 16<br/>public.raw_vietjobs")]
  RAW --> DBT
  DBT --> STG[("analytics.stg_vietjobs<br/>view")]
  STG --> CAT[("mart_category_summary<br/>view")]
  STG --> CON[("mart_contract_summary<br/>view")]
  STG --> STREAM["Streamlit + Plotly<br/>dashboard"]
  CAT --> META["Metabase<br/>optional BI exploration"]
  CON --> META
```

The database and Metabase run under `docker-compose.yml`. Airflow runs under `airflow-docker-compose.yml`, reaching the host-published PostgreSQL port with `host.docker.internal` on Windows Docker Desktop. Streamlit runs from the host Python environment.

## 2. Processing/data flow

```mermaid
flowchart TD
  START["Manual Airflow trigger: vietjobs_pipeline"] --> INGEST["ingest_vietjobs<br/>load_vietjobs.py --replace"]
  INGEST --> VALIDATE["Validate source header, record width and row count"]
  VALIDATE --> STAGE["COPY into a temporary PostgreSQL table"]
  STAGE --> CHECK{"Row counts and integer bounds valid?"}
  CHECK -- No --> ROLLBACK["Fail and roll back transaction"]
  CHECK -- Yes --> REPLACE["Replace public.raw_vietjobs inside transaction"]
  REPLACE --> VERIFY["Verify target count and commit"]
  VERIFY --> RUN["dbt_run<br/>staging + 2 marts"]
  RUN --> TEST["dbt_test<br/>not_null + unique"]
  TEST --> OK{"All checks pass?"}
  OK -- Yes --> READY["Analytical views available"]
  OK -- No --> LOGS["Inspect Airflow/dbt logs"]
```

The ingestion transaction can roll back its own failed load, but a downstream dbt failure **does not undo** an already committed raw load. The raw table must exist before the first ingestion; see `sql/init_raw_vietjobs.sql`.

## 3. Logical ERD / analytical lineage

The application is not a normalized transactional system. There is one **raw physical table**, a staging **dbt view**, and two aggregate **dbt views**. Relations below express derivation and grouping only—not declared foreign keys or enforced relationships.

```mermaid
erDiagram
  RAW_VIETJOBS {
    text job_title
    text location
    text country
    text qualifications
    text technical_skills
    text soft_skills
    text languages_required
    text experience_required
    text salary
    text contract_type
    text working_hours
    text benefits
    text description
    text requirements_text
    text category
    int salary_min
    int salary_max
    text salary_avg
  }
  STG_VIETJOBS {
    text job_title
    text location
    text category
    int salary_min
    int salary_max
    text salary_avg
    text salary_status
  }
  MART_CATEGORY_SUMMARY {
    text category
    bigint total_jobs
    bigint total_locations
    bigint negotiable_jobs
    bigint jobs_with_salary
    bigint salary_unavailable_jobs
    bigint invalid_salary_jobs
    numeric avg_salary_midpoint_million
  }
  MART_CONTRACT_SUMMARY {
    text category
    text contract_type
    bigint total_jobs
    bigint negotiable_jobs
    bigint jobs_with_salary
  }
  RAW_VIETJOBS ||--|| STG_VIETJOBS : "transformed row-wise"
  STG_VIETJOBS }o--|| MART_CATEGORY_SUMMARY : "aggregated by category"
  STG_VIETJOBS }o--|| MART_CONTRACT_SUMMARY : "aggregated by category and contract type"
```

The staging view retains all 18 source columns and adds `salary_status`; only selected fields are shown in the ERD for readability. Grouped mart keys are analytical groupings, not SQL foreign keys.
