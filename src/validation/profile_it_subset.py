
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "external"
    / "VietJobs.csv"
)

REPORT_DIR = PROJECT_ROOT / "data" / "processed"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

IT_CATEGORY = "công_nghệ_thông_tin_kỹ_thuật_số"


def main():
    df = pd.read_csv(
        DATA_FILE,
        encoding="utf-8-sig",
        low_memory=False,
    )

    # Lọc đúng nhóm IT theo category quan sát được
    it_df = df.loc[
        df["category"].eq(IT_CATEGORY)
    ].copy()

    print("=" * 65)
    print("IT JOB SUBSET PROFILING")
    print("=" * 65)

    print(f"\nTổng số tin trong dataset: {len(df):,}")
    print(f"Số tin thuộc nhóm IT: {len(it_df):,}")

    if it_df.empty:
        print("Không tìm thấy category IT. Kiểm tra lại giá trị category.")
        print("\nCác category hiện có:")
        print(df["category"].value_counts().to_string())
        return

    print("\n1. GIÁ TRỊ THIẾU TRONG NHÓM IT")

    for column in [
        "technical_skills",
        "soft_skills",
        "languages_required",
        "experience_required",
        "qualifications",
        "salary",
        "salary_min",
        "salary_max",
        "salary_avg",
    ]:
        if column in it_df.columns:
            missing = int(it_df[column].isna().sum())
            percentage = it_df[column].isna().mean() * 100

            print(
                f"{column}: {missing:,}/{len(it_df):,} "
                f"({percentage:.2f}%)"
            )

    print("\n2. CHỨC DANH PHỔ BIẾN")

    print(
        it_df["job_title"]
        .value_counts()
        .head(20)
        .to_string()
    )

    print("\n3. KINH NGHIỆM YÊU CẦU")

    print(
        it_df["experience_required"]
        .value_counts(dropna=False)
        .head(20)
        .to_string()
    )

    print("\n4. KỸ NĂNG KỸ THUẬT - MỘT SỐ GIÁ TRỊ MẪU")

    available_skills = it_df.loc[
        it_df["technical_skills"].notna(),
        "technical_skills",
    ]

    print(
        f"Số tin có technical_skills: "
        f"{len(available_skills):,}"
    )

    for index, value in enumerate(available_skills.head(10), start=1):
        print(f"\n--- Mẫu {index} ---")
        print(str(value)[:1200])

    print("\n5. KIỂM TRA PHÂN BỐ LƯƠNG")

    for column in ["salary", "salary_min", "salary_max", "salary_avg"]:
        if column in it_df.columns:
            print(f"\n--- {column} ---")
            print(
                it_df[column]
                .value_counts(dropna=False)
                .head(15)
                .to_string()
            )

    print("\n6. KIỂM TRA DÒNG TRÙNG TRONG NHÓM IT")

    print(
        "Số dòng trùng hoàn toàn:",
        int(it_df.duplicated().sum()),
    )

    # Chỉ lưu báo cáo thống kê, không xuất lại toàn bộ tin tuyển dụng
    summary = pd.DataFrame([
        {
            "metric": "total_dataset_rows",
            "value": len(df),
        },
        {
            "metric": "it_job_rows",
            "value": len(it_df),
        },
        {
            "metric": "it_rows_with_technical_skills",
            "value": int(it_df["technical_skills"].notna().sum()),
        },
        {
            "metric": "it_exact_duplicate_rows",
            "value": int(it_df.duplicated().sum()),
        },
    ])

    summary.to_csv(
        REPORT_DIR / "it_subset_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("\nĐã lưu báo cáo:")
    print(REPORT_DIR / "it_subset_summary.csv")


if __name__ == "__main__":
    main()
