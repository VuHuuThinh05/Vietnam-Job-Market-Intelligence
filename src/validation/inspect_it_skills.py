
from pathlib import Path
import ast
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = ROOT / "data" / "raw" / "external" / "VietJobs.csv"
OUTPUT_DIR = ROOT / "data" / "processed"


def parse_skills(value):
    """Chuyển chuỗi biểu diễn list thành danh sách kỹ năng."""
    if pd.isna(value):
        return []

    if isinstance(value, list):
        return value

    text = str(value).strip()

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return parsed
    except (ValueError, SyntaxError):
        pass

    # Không tự tách theo dấu phẩy nếu chưa xác minh định dạng.
    return [text] if text else []


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(
        DATA_FILE,
        encoding="utf-8-sig",
        low_memory=False,
    )

    it_df = df[
        df["category"].eq("công_nghệ_thông_tin_kỹ_thuật_số")
    ].copy()

    it_df["parsed_skills"] = it_df["technical_skills"].apply(
        parse_skills
    )

    print("=" * 65)
    print("IT SKILL INSPECTION")
    print("=" * 65)

    print("\n1. SỐ LƯỢNG KỸ NĂNG TRONG MỖI TIN")

    skill_counts = it_df["parsed_skills"].apply(len)

    print(skill_counts.describe().to_string())

    print("\n2. CÁC KỸ NĂNG XUẤT HIỆN NHIỀU NHẤT")

    exploded = it_df[["job_title", "parsed_skills"]].explode(
        "parsed_skills"
    )

    exploded["parsed_skills"] = (
        exploded["parsed_skills"].astype("string").str.strip()
    )

    exploded = exploded[
        exploded["parsed_skills"].notna()
        & exploded["parsed_skills"].ne("")
    ]

    skill_frequency = (
        exploded["parsed_skills"]
        .value_counts()
        .rename_axis("skill")
        .reset_index(name="job_count")
    )

    print(skill_frequency.head(50).to_string(index=False))

    print("\n3. KIỂM TRA CÁC CHỨC DANH LIÊN QUAN ĐẾN DATA")

    data_pattern = (
        r"data engineer|data analyst|data scientist|"
        r"data platform|big data|etl|database|"
        r"business intelligence|bi developer|"
        r"kỹ sư dữ liệu|phân tích dữ liệu"
    )

    data_jobs = it_df[
        it_df["job_title"].str.contains(
            data_pattern,
            case=False,
            regex=True,
            na=False,
        )
    ]

    print(f"Số tin khớp từ khóa data: {len(data_jobs):,}")

    print(
        data_jobs["job_title"]
        .value_counts()
        .head(50)
        .to_string()
    )

    print("\n4. XUẤT BÁO CÁO")

    skill_frequency.to_csv(
        OUTPUT_DIR / "it_skill_frequency.csv",
        index=False,
        encoding="utf-8-sig",
    )

    data_jobs.drop(columns=["parsed_skills"]).to_csv(
        OUTPUT_DIR / "it_data_related_jobs.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print(OUTPUT_DIR / "it_skill_frequency.csv")
    print(OUTPUT_DIR / "it_data_related_jobs.csv")


if __name__ == "__main__":
    main()
