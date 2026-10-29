from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "raw" / "external" / "VietJobs.csv"

df = pd.read_csv(SOURCE, low_memory=False)

def classify(value):
    if pd.isna(value):
        return "NULL_THAT"
    s = str(value).strip()
    if s == "":
        return "CHUOI_RONG"
    if s == "0":
        return "GIA_TRI_0"
    if s.upper() == "UNK":
        return "UNK"
    if s == "[]":
        return "DANH_SACH_RONG"
    return "CO_NOI_DUNG"

print("=" * 70)
print("1. CAC GIA TRI DAC BIET TRONG CAC COT")
print("=" * 70)

columns = [
    "languages_required",
    "technical_skills",
    "soft_skills",
    "qualifications",
    "working_hours",
    "salary",
    "salary_avg",
]

for col in columns:
    if col not in df.columns:
        continue

    status = df[col].map(classify)
    print(f"\n--- {col} ---")
    print(status.value_counts(dropna=False).to_string())

    special = df.loc[
        status.isin([
            "NULL_THAT", "CHUOI_RONG", "GIA_TRI_0",
            "UNK", "DANH_SACH_RONG"
        ]),
        col
    ]
    print("Gia tri goc dac biet:")
    print(special.value_counts(dropna=False).head(15).to_string())

print("\n" + "=" * 70)
print("2. DOI CHIEU TRANG THAI LUONG")
print("=" * 70)

salary_cols = ["salary", "salary_min", "salary_max", "salary_avg"]
salary_cols = [c for c in salary_cols if c in df.columns]

agreed = df["salary_avg"].astype(str).str.strip().str.lower().isin(
    ["thoả thuận", "thỏa thuận"]
)

print("So tin luong thoa thuan:", int(agreed.sum()))
print("So tin luong thoa thuan co min/max khac 0:",
      int((agreed & ((df["salary_min"] != 0) |
                     (df["salary_max"] != 0))).sum()))

zero_range = (df["salary_min"] == 0) & (df["salary_max"] == 0)
print("So tin co salary_min = salary_max = 0:", int(zero_range.sum()))
print("So tin co min > max:", int((df["salary_min"] > df["salary_max"]).sum()))

print("\nMot so mau luong thoa thuan:")
print(df.loc[agreed, salary_cols].head(8).to_string(index=False))

print("\n" + "=" * 70)
print("3. KIEM TRA BAN GHI TRUNG")
print("=" * 70)

duplicates = df[df.duplicated(keep=False)]
print("So dong thuoc cac nhom bi trung:", len(duplicates))
print("So dong trung lap bo sung neu giu ban dau:",
      int(df.duplicated().sum()))

print("\n5 mau dong trung de doi chieu:")
print(duplicates.head(5).to_string(index=False))

print("\nHoan tat kiem tra. File CSV goc khong bi thay doi.")
