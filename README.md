# Vietnam Job Market Intelligence

**An end-to-end data pipeline for recruitment market analysis using PostgreSQL, dbt, Docker, and Streamlit.**

## Overview

Vietnam Job Market Intelligence is a data engineering portfolio project that transforms Vietnamese recruitment data into structured datasets for market analysis.

The project focuses on building a reproducible local analytics workflow: loading source data into PostgreSQL, transforming it with dbt, validating analytical models, and presenting insights through interactive dashboards.

The dataset covers multiple occupational categories rather than only the technology sector.

## Business Objectives

The project aims to help users explore:

- The distribution of recruitment listings across occupational categories.
- Geographic distribution of job opportunities.
- Salary information and salary availability.
- Contract types and employment characteristics.
- Skills and qualification requirements.
- Data quality limitations that may affect interpretation.

The dataset does not provide a verified posting date for every record. Therefore, the project does not treat the dataset as a reliable time series of recruitment demand.

## Architecture

```text
VietJobs CSV
     |
     v
Python Ingestion
(src/ingestion/load_vietjobs.py)
     |
     v
PostgreSQL
(raw_vietjobs)
     |
     v
dbt Transformations
     |
     +--> stg_vietjobs
     |
     +--> mart_category_summary
     |
     +--> mart_contract_summary
                  |
                  v
          Analytics Layer
             /       \
            v         v
       Streamlit   Metabase
       Dashboard   Exploration
```

### Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Source data | VietJobs CSV | Recruitment records |
| Database | PostgreSQL 16 | Raw data storage and SQL queries |
| Local infrastructure | Docker Compose | Running PostgreSQL and Metabase |
| Transformation | dbt Core and dbt-postgres | SQL-based data transformation |
| Dashboard | Streamlit | Interactive data exploration |
| Visualization | Plotly | Interactive charts |
| BI exploration | Metabase | Querying and visualizing analytical models |
| Validation | dbt tests and Python scripts | Data quality checks and profiling |

## Dataset

The source dataset contains **48,092 records and 18 columns**, covering **16 occupational categories**.

Source: [VietJobs dataset on Hugging Face](https://huggingface.co/datasets/dinhieufam/VietJobs)

The source repository and research paper are available here:

- [VietJobs GitHub repository](https://github.com/VinNLP/VietJobs)
- [VietJobs research paper](https://aclanthology.org/2026.lrec-1.501/)

The dataset includes job titles, locations, occupational categories, salary fields, employment characteristics, qualifications, skills, and job descriptions.

### Data Quality Considerations

Salary and requirement fields need careful interpretation:

- Negotiable salary records should not be interpreted as zero-paid jobs.
- Missing values and explicit empty requirement values may have different meanings.
- Salary ranges with a maximum below the minimum require validation.
- Duplicate records may affect counts if they are not handled consistently.
- The source data should be preserved separately from transformed analytical models.

These considerations are documented as part of the project's data profiling and validation work.

## Data Pipeline

### 1. Raw Data Layer and Ingestion

The source CSV is loaded into PostgreSQL using src/ingestion/load_vietjobs.py.

The ingestion script validates the source file structure, checks the row count and salary-bound data types, loads the CSV into a temporary staging table, and verifies the final row count.

The script refuses to load into a non-empty target table unless --replace is explicitly provided. Database changes are performed within a transaction so that failures roll back the current load.

Set the DB_PASSWORD environment variable before running the script.

$env:DB_PASSWORD = "your_local_database_password"

# Load only when the target table is empty
python .\src\ingestion\load_vietjobs.py

# Replace existing raw data with the validated CSV
python .\src\ingestion\load_vietjobs.py --replace

The source CSV is excluded from version control and must be obtained separately from the VietJobs dataset.

### 2. Staging Layer

`analytics.stg_vietjobs` standardizes text fields and derives a salary status used by downstream analytical models.

The current salary status categories include:

- `negotiable`
- `unavailable`
- `provided`
- `invalid_range`

These classifications are intended to distinguish salary availability from invalid salary ranges.

### 3. Analytical Marts

**`analytics.mart_category_summary`**

Aggregates recruitment records by occupational category, including job counts, location counts, salary availability, and salary midpoint statistics where the salary range is valid.

**`analytics.mart_contract_summary`**

Aggregates recruitment records by occupational category and contract type.

### 4. Data Validation

The dbt project currently contains tests for required fields and key uniqueness in selected models. The current test suite has passed seven tests in the local development environment.

Additional Python scripts are available under `src/validation/` for source profiling, special-value inspection, salary anomaly inspection, and exploratory skills analysis.

## Repository Structure

```text
.
├── dashboards/
│   ├── app.py
│   └── db.py
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   └── source_audit.md
src/
├── ingestion/
│   └── load_vietjobs.py
└── validation/
    ├── inspect_it_skills.py
    ├── inspect_salary_anomalies.py
    ├── inspect_source_data.py
    ├── inspect_special_values.py
    ├── profile_dataset.py
    └── profile_it_subset.py
├── vietjobs_dbt/
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/
│       └── marts/
├── .env.example
├── .gitignore
├── docker-compose.yml
└── requirements.txt
```

Local data files, environment secrets, dbt profiles, and generated artifacts are excluded from version control.

## Local Setup

### Prerequisites

- Git
- Python 3.11
- Docker Desktop with Docker Compose
- The VietJobs CSV dataset

### 1. Clone the repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Vietnam-Job-Market-Intelligence
```

Replace the placeholder URL with your actual GitHub repository URL after publishing the project.

### 2. Configure environment variables

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set a local PostgreSQL password. Do not commit `.env`.

For a new database, the password in `.env` must match the password used when initializing PostgreSQL. Changing `POSTGRES_PASSWORD` does not automatically change the password in an existing database volume.

### 3. Prepare the source dataset

Place the source CSV at:

```text
data/raw/external/VietJobs.csv
```

The dataset is excluded from Git because of its size. Obtain it from the source dataset page linked above.

### 4. Start PostgreSQL and Metabase

```powershell
docker compose config --quiet
docker compose up -d
docker compose ps
```

Wait until PostgreSQL is healthy before continuing.

### 5. Install Python dependencies

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Configure dbt

Create a local `profiles.yml` in the repository root. This file is intentionally excluded from Git.

Configure the `vietjobs_dbt` profile with the PostgreSQL connection details from your local environment. Set the host to `localhost`, port to `5432`, database and user to the values in `.env`, and schema to `analytics`.

Ensure that the password matches the database's actual password.

Validate the configuration:

```powershell
dbt debug --project-dir .\vietjobs_dbt --profiles-dir .
```

### 7. Load and transform the data

The raw CSV must be loaded into `public.raw_vietjobs` before running the dbt models.

Once the raw table is available, run:

```powershell
dbt run --project-dir .\vietjobs_dbt --profiles-dir .
dbt test --project-dir .\vietjobs_dbt --profiles-dir .
```

### 8. Launch the Streamlit dashboard

From the repository root, with the virtual environment activated:

```powershell
streamlit run .\dashboards\app.py
```

The dashboard connects to PostgreSQL using the `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` environment variables, with local defaults defined in `dashboards/db.py`.

### 9. Open Metabase

Visit [http://localhost:3000](http://localhost:3000) and complete the initial setup if needed. Configure the database connection to use the PostgreSQL instance and the `analytics` schema.

## Current Project Status

The following components have been verified in the local development environment:

- PostgreSQL and Metabase containers run through Docker Compose.
- The raw PostgreSQL table contains 48,092 records across 16 categories.
- Three dbt business models are configured: one staging model and two marts.
- The dbt connection check passes.
- Seven dbt tests passed after restructuring the model directories.
- The Streamlit dashboard and database connection module are present.
- A Python ingestion script is available at `src/ingestion/load_vietjobs.py`.
- The script successfully loaded 48,092 records into `public.raw_vietjobs`.
- The raw table contains 16 occupational categories.
- Three dbt models and seven dbt tests have been verified in the local development environment.
- PostgreSQL and Metabase run through Docker Compose.
- The Streamlit dashboard is available for interactive exploration.

Scheduled orchestration has not yet been established as a verified project component.

## Limitations and Future Improvements

Potential next steps include:

- Building a reproducible ingestion script with explicit validation and error handling.
- Expanding automated data quality tests.
- Adding an orchestration workflow after the pipeline steps are independently reproducible.
- Documenting transformation logic and field-level business definitions.
- Adding dashboard screenshots and representative analytical findings.
- Improving deployment configuration and secret management.

## License and Data Attribution

Review the source dataset's license and terms before redistributing the data. This repository is intended to document the pipeline implementation and analytical workflow; the source dataset is not included by default.
