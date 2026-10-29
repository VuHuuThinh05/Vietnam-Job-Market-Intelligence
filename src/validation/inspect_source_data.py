
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "raw" / "external" / "VietJobs.csv"
OUTPUT = ROOT / "data" / "processed"

df = pd.read_csv(SOURCE, low_memory=False)

print("=" * 70)
print("1. TONG QUAN DU LIEU")
print("=" * 70)
print(f"So dong: {len(df):,}")
print(f"So cot: {len(df.columns)}")
print(f"Dung luong file: {SOURCE.stat().st_size / (1024**2):.2f} MB")

print("\n2. DANH SACH COT VA KIEU DU LIEU")
print(df.dtypes.to_string())

print("\n3. GIA TRI THIEU")
missing = pd.DataFrame({
    "missing_count": df.isna().sum(),
    "missing_pct": (df.isna().mean() * 100).round(2),
})
print(missing.sort_values("missing_pct", ascending=False).to_string())

print("\n4. BAN GHI TRUNG LAP")
print(f"So dong trung lap toan bo cot: {df.duplicated().sum():,}")

print("\n5. SO LUONG TIN THEO NHOM NGANH")
if "category" in df.columns:
    print(df["category"].fillna("(NULL)").value_counts().to_string())

print("\n6. KIEM TRA CAC COT LUONG")
salary_cols = [
    c for c in ["salary", "salary_min", "salary_max", "salary_avg"]
    if c in df.columns
]
if salary_cols:
    print(df[salary_cols].head(10).to_string(index=False))
    for col in salary_cols:
        print(f"\n{col}:")
        print(df[col].value_counts(dropna=False).head(10).to_string())

print("\n7. KIEM TRA CAC COT KY NANG VA NGOAI NGU")
for col in ["technical_skills", "soft_skills", "languages_required"]:
    if col in df.columns:
        print(f"\n{col}:")
        print(df[col].fillna("(NULL)").astype(str).value_counts().head(12).to_string())

print("\n8. LUU BAO CAO")
OUTPUT.mkdir(parents=True, exist_ok=True)

missing.to_csv(
    OUTPUT / "source_missing_values.csv",
    encoding="utf-8-sig"
)

summary = {
    "row_count": int(len(df)),
    "column_count": int(len(df.columns)),
    "duplicate_rows": int(df.duplicated().sum()),
    "columns": list(df.columns),
    "file_size_mb": round(SOURCE.stat().st_size / (1024**2), 2),
}

with open(
    OUTPUT / "source_data_summary.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print("Da luu source_missing_values.csv")
print("Da luu source_data_summary.json")
