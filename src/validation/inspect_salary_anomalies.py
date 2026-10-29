from pathlib import Path
import pandas as pd
root = Path(__file__).resolve().parents[2]
source = root / "data" / "raw" / "external" / "VietJobs.csv"
df = pd.read_csv(source, low_memory=False)
cols = [
"job_title", "location", "category",
"salary", "salary_min", "salary_max", "salary_avg"
]
print("=== 1. HAI DONG CO SALARY_MIN > SALARY_MAX ===")
invalid = df["salary_min"] > df["salary_max"]
print(df.loc[invalid, cols].to_string(index=True))
print("\n=== 2. LUONG MIN/MAX BANG 0 NHUNG KHONG GHI THOA THUAN ===")
zero_range = (df["salary_min"] == 0) & (df["salary_max"] == 0)
agreed = df["salary_avg"].astype(str).str.strip().str.lower().isin(
["thoả thuận", "thỏa thuận"]
)
other_zero = zero_range & ~agreed
print("So dong:", int(other_zero.sum()))
print(df.loc[other_zero, cols].head(20).to_string(index=True))
print("\n=== 3. GIA TRI UNK CUA NGOAI NGU ===")
language_unk = df["languages_required"].astype(str).str.strip().str.upper() == "UNK"
print("So dong UNK:", int(language_unk.sum()))
print(df.loc[language_unk, ["job_title", "category", "languages_required"]]
.head(15).to_string(index=True))