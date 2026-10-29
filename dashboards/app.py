"""Compact exploratory dashboard for the historical VietJobs dataset."""
import ast
import json
import re
from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

from db import get_connection

st.set_page_config(page_title="Vietnam Job Market Intelligence", page_icon="📊", layout="wide")
st.title("Vietnam Job Market Intelligence")
st.caption("Historical job-market dataset · Exploratory analysis, not live recruitment data")


@st.cache_data(ttl=300)
def load_data():
    query = """
        SELECT job_title, category, location, salary, salary_min, salary_max,
               salary_status, contract_type, technical_skills, soft_skills,
               experience_required, qualifications, languages_required
        FROM analytics.stg_vietjobs
    """
    with get_connection() as conn:
        return pd.read_sql(query, conn)


def top_skills(values, limit=10):
    """Count each skill once per listing, supporting JSON-like and delimited text."""
    counts = Counter()
    for value in values.dropna():
        raw = str(value).strip()
        if not raw or raw in ("0", "[]", "{}"):
            continue
        try:
            items = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            try:
                items = ast.literal_eval(raw)
            except (ValueError, SyntaxError):
                items = re.split(r"[,;|]+", raw)
        if isinstance(items, dict):
            items = list(items)
        if not isinstance(items, (list, tuple, set)):
            items = [items]
        unique = {
            str(item).strip().strip("'\"").lower()
            for item in items
            if str(item).strip() and len(str(item).strip()) <= 50
        }
        counts.update(s for s in unique if s not in ("0", "null", "nan", "none"))
    return pd.DataFrame(counts.most_common(limit), columns=["Skill", "Listings"])


def bar_counts(series, title, limit=10):
    counts = series.fillna("Unknown").replace("", "Unknown").value_counts().head(limit)
    fig = px.bar(x=counts.values, y=counts.index, orientation="h",
                 labels={"x": "Listings", "y": ""}, title=title)
    fig.update_layout(yaxis={"autorange": "reversed"}, height=420)
    st.plotly_chart(fig, use_container_width=True)


try:
    source = load_data()
except Exception as exc:
    st.error("Cannot read analytics.stg_vietjobs. Check PostgreSQL, dbt and DB_PASSWORD.")
    st.exception(exc)
    st.stop()

if source.empty:
    st.warning("No data found. Run the ingestion and dbt pipeline first.")
    st.stop()

for col in ("salary_min", "salary_max"):
    source[col] = pd.to_numeric(source[col], errors="coerce")
source["category"] = source["category"].fillna("Unknown")
source["location"] = source["location"].fillna("Unknown")

with st.sidebar:
    st.header("Filters")
    category = st.selectbox("Category", ["All"] + sorted(source["category"].unique()))
    scoped = source if category == "All" else source[source["category"] == category]
    location = st.selectbox("Location (source label)", ["All"] + sorted(scoped["location"].unique()))
    if st.button("Refresh data"):
        load_data.clear()
        st.rerun()

data = scoped if location == "All" else scoped[scoped["location"] == location]
data = data.copy()
salary = data[
    data["salary_status"].eq("provided")
    & data["salary_min"].gt(0)
    & data["salary_max"].ge(data["salary_min"])
].copy()
salary["midpoint"] = (salary["salary_min"] + salary["salary_max"]) / 2

k1, k2, k3, k4 = st.columns(4)
k1.metric("Listings", f"{len(data):,}")
k2.metric("Categories", data["category"].nunique())
k3.metric("Valid salary ranges", f"{len(salary):,}")
k4.metric("Negotiable salary", f"{data['salary_status'].eq('negotiable').sum():,}")

overview, salary_tab, skills_tab, quality = st.tabs(
    ["Overview", "Salary", "Skills & contracts", "Data quality"]
)

with overview:
    a, b = st.columns(2)
    with a:
        bar_counts(data["category"], "Top categories")
    with b:
        bar_counts(data["location"], "Top source location labels")
    status = data["salary_status"].fillna("unknown").value_counts().rename_axis("status").reset_index(name="jobs")
    st.plotly_chart(px.pie(status, names="status", values="jobs",
                           title="Salary availability", hole=0.45), use_container_width=True)

with salary_tab:
    st.caption("Midpoint = (salary_min + salary_max) / 2, using source units. "
               "Only positive, non-inverted salary ranges are included.")
    if salary.empty:
        st.info("No valid salary ranges for these filters.")
    else:
        st.metric("Median salary midpoint (source units)", f"{salary['midpoint'].median():,.1f}")
        top_categories = salary["category"].value_counts().head(8).index
        fig = px.box(salary[salary["category"].isin(top_categories)],
                     x="category", y="midpoint", title="Salary midpoint by category")
        st.plotly_chart(fig, use_container_width=True)

with skills_tab:
    a, b = st.columns(2)
    with a:
        bar_counts(data["contract_type"], "Contract types")
    with b:
        skills = top_skills(data["technical_skills"])
        if skills.empty:
            st.info("No technical skills in the selected records.")
        else:
            fig = px.bar(skills, x="Listings", y="Skill", orientation="h",
                         title="Most frequently mentioned technical skills")
            fig.update_layout(yaxis={"autorange": "reversed"}, height=420)
            st.plotly_chart(fig, use_container_width=True)

with quality:
    cols = ["location", "qualifications", "technical_skills", "soft_skills",
            "languages_required", "experience_required"]
    missing = pd.Series({
        col: (data[col].isna() | data[col].astype(str).str.strip().isin(["", "0", "[]"])).mean() * 100
        if len(data) else 0
        for col in cols
    }).sort_values(ascending=False)
    fig = px.bar(x=missing.values, y=missing.index, orientation="h",
                 labels={"x": "Missing or empty (%)", "y": ""},
                 title="Potentially empty requirement fields")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("For some source fields, empty or 0 means 'not required' rather than a data error.")
    invalid_mask = data["salary_min"].gt(data["salary_max"]).fillna(False)
    st.metric("Invalid salary ranges (min > max)", f"{invalid_mask.sum():,}")
    st.dataframe(data.loc[invalid_mask, ["job_title", "category", "location",
                                       "salary_min", "salary_max"]], use_container_width=True)

with st.expander("Search source records"):
    keyword = st.text_input("Job title or technical skill")
    matches = data
    if keyword:
        matches = data[
            data["job_title"].fillna("").str.contains(keyword, case=False, regex=False)
            | data["technical_skills"].fillna("").str.contains(keyword, case=False, regex=False)
        ]
    st.caption(f"{len(matches):,} matching records; showing up to 100")
    st.dataframe(matches[["job_title", "category", "location", "salary",
                          "contract_type", "technical_skills"]].head(100),
                 use_container_width=True)
