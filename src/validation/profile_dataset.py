
from pathlib import Path
import hashlib
import json

import pandas as pd


# Xác định thư mục gốc dự án
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


def calculate_sha256(file_path: Path) -> str:
    """Tính SHA256 theo từng khối dữ liệu."""
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file dữ liệu: {DATA_FILE}"
        )

    print("=" * 65)
    print("VIETJOBS DATA PROFILING")
    print("=" * 65)

    print(f"\nFile: {DATA_FILE}")
    print(f"Dung lượng: {DATA_FILE.stat().st_size:,} bytes")
    print(f"SHA256: {calculate_sha256(DATA_FILE)}")

    # Đọc dữ liệu gốc để khảo sát, không ghi đè file CSV
    df = pd.read_csv(
        DATA_FILE,
        encoding="utf-8-sig",
        low_memory=False,
    )

    print("\n1. KÍCH THƯỚC DATASET")
    print(f"Số bản ghi: {len(df):,}")
    print(f"Số cột: {len(df.columns):,}")

    print("\n2. DANH SÁCH CỘT")
    for column in df.columns:
        print(f"- {column}")

    # Tổng hợp schema và chất lượng dữ liệu
    schema = pd.DataFrame({
        "column_name": df.columns,
        "data_type": [
            str(dtype) for dtype in df.dtypes
        ],
        "missing_count": df.isna().sum().values,
        "missing_percent": (
            df.isna().mean().values * 100
        ).round(2),
        "distinct_count": [
            df[column].nunique(dropna=True)
            for column in df.columns
        ],
    })

    print("\n3. KIỂU DỮ LIỆU VÀ GIÁ TRỊ THIẾU")
    print(
        schema.sort_values(
            "missing_percent",
            ascending=False,
        ).to_string(index=False)
    )

    print("\n4. KIỂM TRA BẢN GHI TRÙNG")
    duplicate_count = int(df.duplicated().sum())
    print(f"Số dòng trùng hoàn toàn: {duplicate_count:,}")

    print("\n5. THỐNG KÊ CÁC CỘT QUAN TRỌNG")

    candidate_columns = [
        "category",
        "location",
        "job_title",
        "experience_required",
        "contract_type",
        "salary",
        "salary_min",
        "salary_max",
        "salary_avg",
    ]

    for column in candidate_columns:
        if column in df.columns:
            print(f"\n--- {column} ---")
            print(
                df[column]
                .value_counts(dropna=False)
                .head(10)
                .to_string()
            )

    # Xuất báo cáo profiling
    schema.to_csv(
        REPORT_DIR / "vietjobs_schema_profile.csv",
        index=False,
        encoding="utf-8-sig",
    )

    summary = {
        "file_name": DATA_FILE.name,
        "file_size_bytes": DATA_FILE.stat().st_size,
        "sha256": calculate_sha256(DATA_FILE),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "exact_duplicate_rows": duplicate_count,
        "columns": df.columns.tolist(),
    }

    with (
        REPORT_DIR / "vietjobs_profile_summary.json"
    ).open("w", encoding="utf-8") as file:
        json.dump(
            summary,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n6. ĐÃ XUẤT BÁO CÁO")
    print(
        REPORT_DIR / "vietjobs_schema_profile.csv"
    )
    print(
        REPORT_DIR / "vietjobs_profile_summary.json"
    )


if __name__ == "__main__":
    main()
