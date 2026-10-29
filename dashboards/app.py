import ast
import json
import re
import unicodedata
from collections import Counter

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from db import get_connection

PAGE_SIZE = 10
ALL_CATEGORIES = "Tất cả ngành nghề"
ALL_LOCATIONS = "Tất cả địa điểm"
OTHER_LOCATION = "Khác / chưa xác định"
UNKNOWN = "Chưa xác định"

st.set_page_config(
    page_title="Vietnam Tech Hiring Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# LIGHT MODERN ENTERPRISE UI STYLING (Tương phản cao, sắc nét, dễ đọc)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background-color: #f1f5f9;
        color: #0f172a;
    }
    
    .block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1650px; }
    
    /* Hero Banner Light Theme */
    .hero-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0284c7 100%);
        border-radius: 16px;
        padding: 1.8rem 2.2rem;
        margin-bottom: 1.5rem;
        color: #ffffff;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.3rem;
        letter-spacing: -0.02em;
    }
    .hero-subtitle { color: #cbd5e1; font-size: 0.98rem; margin: 0; font-weight: 500; }
    .hero-badge {
        background: rgba(255, 255, 255, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #38bdf8;
        padding: 8px 18px;
        border-radius: 30px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    
    /* KPI Metric Cards Light Modern */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.05);
        transition: all 0.2s ease-in-out;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(15, 23, 42, 0.08);
        border-color: #0284c7;
    }
    .kpi-label { color: #64748b; font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .kpi-value { color: #0f172a; font-size: 1.85rem; font-weight: 800; margin: 6px 0 2px 0; }
    .kpi-subtext { font-size: 0.8rem; color: #0284c7; font-weight: 600; }
    
    /* Sidebar Styling Light/Dark Contrast */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] * { color: #0f172a !important; }
    
    /* Streamlit Tabs Custom */
    div[data-testid="stTabs"] button {
        font-size: 0.92rem;
        font-weight: 700;
        color: #475569 !important;
        padding: 10px 22px;
        border-radius: 8px;
        background-color: #e2e8f0;
        margin-right: 6px;
        transition: all 0.2s;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #ffffff !important;
        background-color: #0284c7 !important;
        box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3);
    }
    
    .insight-box {
        background: #f0f9ff;
        border-left: 5px solid #0284c7;
        border-radius: 0 10px 10px 0;
        padding: 14px 18px;
        margin: 15px 0;
        font-size: 0.92rem;
        color: #0f172a;
    }
    .insight-title { color: #0369a1; font-weight: 800; margin-bottom: 4px; font-size: 0.95rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

CHART_TEMPLATE = "plotly_white"
COLOR_PALETTE = ["#0284c7", "#4f46e5", "#059669", "#7c3aed", "#d97706", "#ec4899", "#2563eb", "#0891b2"]

def polish_chart(fig, height=390, showlegend=None):
    fig.update_layout(
        template=CHART_TEMPLATE,
        height=height,
        margin=dict(l=15, r=15, t=45, b=15),
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#334155", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title_font=dict(size=15, color="#0f172a", family="Plus Jakarta Sans"),
        hoverlabel=dict(bgcolor="#0f172a", font_color="#ffffff", font_family="Plus Jakarta Sans"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11)),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#e2e8f0", zeroline=False)
    if showlegend is not None:
        fig.update_layout(showlegend=showlegend)
    return fig

# -----------------------------------------------------------------------------
# Chuẩn hóa địa điểm
# -----------------------------------------------------------------------------
def normalize_location_text(value):
    text = unicodedata.normalize("NFD", str(value).casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("đ", "d")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()

PROVINCE_NAMES = (
    "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang", "Bắc Kạn", "Bạc Liêu",
    "Bắc Ninh", "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước",
    "Bình Thuận", "Cà Mau", "Cần Thơ", "Cao Bằng", "Đà Nẵng", "Đắk Lắk",
    "Đắk Nông", "Điện Biên", "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Giang",
    "Hà Nam", "Hà Nội", "Hà Tĩnh", "Hải Dương", "Hải Phòng", "Hậu Giang",
    "Hòa Bình", "Hưng Yên", "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu",
    "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định", "Nghệ An",
    "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên", "Quảng Bình",
    "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sóc Trăng",
    "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên", "Thanh Hóa",
    "Thừa Thiên Huế", "Tiền Giang", "Hồ Chí Minh", "Trà Vinh", "Tuyên Quang",
    "Vĩnh Long", "Vĩnh Phúc", "Yên Bái",
)
PROVINCE_ALIASES = {normalize_location_text(name): name for name in PROVINCE_NAMES}
PROVINCE_ALIASES.update({
    normalize_location_text(alias): province
    for alias, province in (
        ("TP Hà Nội", "Hà Nội"), ("Thành phố Hà Nội", "Hà Nội"),
        ("TP Đà Nẵng", "Đà Nẵng"), ("TP Hải Phòng", "Hải Phòng"),
        ("TP Cần Thơ", "Cần Thơ"), ("TP Hồ Chí Minh", "Hồ Chí Minh"),
        ("Thành phố Hồ Chí Minh", "Hồ Chí Minh"), ("TPHCM", "Hồ Chí Minh"),
        ("TP HCM", "Hồ Chí Minh"), ("HCM", "Hồ Chí Minh"),
        ("Sài Gòn", "Hồ Chí Minh"), ("Huế", "Thừa Thiên Huế"),
    )
})
AREA_ALIASES = {
    normalize_location_text(alias): province
    for province, aliases in {
        "Hà Nội": ("Hà Đông", "Bắc Từ Liêm", "Nam Từ Liêm", "Cầu Giấy", "Đông Anh", "Gia Lâm", "Long Biên", "Thanh Xuân", "Đống Đa", "Ba Đình", "Hai Bà Trưng", "Hoàng Mai"),
        "Hồ Chí Minh": ("Thủ Đức", "TP Thủ Đức", "Quận 1", "Quận 2", "Quận 3", "Quận 4", "Quận 5", "Quận 6", "Quận 7", "Quận 8", "Quận 9", "Quận 10", "Quận 11", "Quận 12", "Bình Thạnh", "Tân Bình", "Gò Vấp", "Phú Nhuận"),
        "Đà Nẵng": ("Hải Châu", "Thanh Khê", "Sơn Trà", "Cẩm Lệ", "Ngũ Hành Sơn"),
        "Bình Dương": ("Dĩ An", "Bến Cát", "Thuận An", "Thủ Dầu Một"),
        "Đồng Nai": ("Biên Hòa", "Long Khánh"),
    }.items() for alias in aliases
}

def infer_province(location):
    if location is None or pd.isna(location) or not str(location).strip():
        return OTHER_LOCATION
    parts = str(location).split(",")
    for part in reversed(parts):
        normalized = normalize_location_text(part)
        if normalized in PROVINCE_ALIASES:
            return PROVINCE_ALIASES[normalized]
        if normalized in AREA_ALIASES:
            return AREA_ALIASES[normalized]
    text = normalize_location_text(location)
    international_markers = ("germany", "japan", "tokyo", "singapore", "usa", "korea", "china", "remote worldwide")
    if any(marker in text for marker in international_markers):
        return "Nước ngoài / quốc tế"
    return OTHER_LOCATION

@st.cache_data(ttl=300, show_spinner="Đang truy vấn dữ liệu từ Postgres/dbt...")
def load_market_data():
    query = """
        SELECT category, location, salary, salary_min, salary_max, salary_avg,
               salary_status, contract_type, experience_required, qualifications,
               technical_skills, soft_skills, languages_required, working_hours, benefits
        FROM analytics.stg_vietjobs
    """
    with get_connection() as conn:
        df = pd.read_sql(query, conn)
    if df.empty:
        return df
    for col in ("salary_min", "salary_max", "salary_avg"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["category"] = df["category"].fillna(UNKNOWN).replace("", UNKNOWN)
    df["location_province"] = df["location"].apply(infer_province)
    df["salary_status"] = df["salary_status"].fillna(UNKNOWN).astype(str)
    return df

def display_value(value):
    if value is None or pd.isna(value):
        return "Chưa có dữ liệu"
    text = str(value).strip()
    if not text or text.casefold() in {"nan", "none", "null", "n/a", "na", "[]", "{}"}:
        return "Chưa có dữ liệu"
    return text

def parse_items(value):
    text = display_value(value)
    if text == "Chưa có dữ liệu":
        return []
    for parser in (json.loads, ast.literal_eval):
        try:
            parsed = parser(text)
            if isinstance(parsed, dict):
                parsed = list(parsed.keys())
            if isinstance(parsed, (list, tuple, set)):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
    parts = re.split(r"[,;|•\n]+", text)
    cleaned = [re.sub(r"^[\[\]{}'\"\s]+|[\[\]{}'\"\s]+$", "", x).strip() for x in parts]
    return [x for x in cleaned if x and x.casefold() not in {"null", "none", "nan"}]

def add_insight_card(title, obs, rec):
    st.markdown(
        f"""
        <div class="insight-box">
            <div class="insight-title">💡 Insights & Actionable Takeaways — {title}</div>
            <div style="margin-bottom: 4px;"><b>Quan sát:</b> {obs}</div>
            <div style="color: #475569;"><b>Khuyến nghị:</b> {rec}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------------------------------------------------------
# MAIN APP LAYOUT
# -----------------------------------------------------------------------------
df_raw = load_market_data()

# Hero Banner
st.markdown(
    """
    <div class="hero-container">
        <div>
            <div class="hero-title">Vietnam Tech Hiring Intelligence</div>
            <p class="hero-subtitle">Analytics Cockpit & Signal Pipeline — Phân tích thị trường tuyển dụng Công nghệ & Dữ liệu</p>
        </div>
        <div class="hero-badge">dbt + Postgres Engine</div>
    </div>
    """,
    unsafe_allow_html=True
)

if df_raw.empty:
    st.error("Chưa có dữ liệu trong bảng analytics.stg_vietjobs. Vui lòng kiểm tra lại Pipeline!")
    st.stop()

# -----------------------------------------------------------------------------
# SIDEBAR CONTROLS
# -----------------------------------------------------------------------------
st.sidebar.markdown("<h2 style='font-size:1.15rem; font-weight:800; color:#0f172a;'>🎛️ BỘ LỌC TOÀN CỤC</h2>", unsafe_allow_html=True)

categories = [ALL_CATEGORIES] + sorted([c for c in df_raw["category"].unique() if c != UNKNOWN])
selected_cat = st.sidebar.selectbox("Ngành nghề", categories)

provinces = [ALL_LOCATIONS] + sorted([p for p in df_raw["location_province"].unique() if p not in (OTHER_LOCATION, "Nước ngoài / quốc tế")])
selected_loc = st.sidebar.selectbox("Tỉnh / Thành phố", provinces)

# Apply global filters
df = df_raw.copy()
if selected_cat != ALL_CATEGORIES:
    df = df[df["category"] == selected_cat]
if selected_loc != ALL_LOCATIONS:
    df = df[df["location_province"] == selected_loc]

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='font-size:0.85rem; font-weight:800; color:#64748b;'>SUMMARY METRICS</h3>", unsafe_allow_html=True)
st.sidebar.markdown(f"**Tổng số tin lọc:** `{len(df):,}` / `{len(df_raw):,}`")
salary_valid_df = df[df["salary_status"].eq("provided") & df["salary_min"].notna() & df["salary_max"].notna() & (df["salary_min"] > 0)]
st.sidebar.markdown(f"**Mẫu lương hợp lệ:** `{len(salary_valid_df):,}`")

# -----------------------------------------------------------------------------
# TABS SYSTEM
# -----------------------------------------------------------------------------
tab_overview, tab_salary, tab_employment, tab_skills, tab_quality, tab_search = st.tabs([
    "📊 TỔNG QUAN", "💰 PHÂN TÍCH LƯƠNG", "🧾 HÌNH THỨC & YÊU CẦU", "🧠 KỸ NĂNG NỔI BẬT", "🧪 DATA QUALITY", "🔎 TRA CỨU VIỆC LÀM"
])

# =============================================================================
# TAB 1: TỔNG QUAN
# =============================================================================
with tab_overview:
    m1, m2, m3, m4, m5 = st.columns(5)
    total_jobs = len(df)
    valid_sal_count = len(salary_valid_df)
    negotiable_count = (df["salary_status"] == "negotiable").sum()
    cat_count = df["category"].nunique()
    loc_count = df["location_province"].nunique()

    m1.markdown(f'<div class="kpi-card"><div class="kpi-label">Tổng Tin Tuyển Dụng</div><div class="kpi-value">{total_jobs:,}</div><div class="kpi-subtext">Active Listings</div></div>', unsafe_allow_html=True)
    m2.markdown(f'<div class="kpi-card"><div class="kpi-label">Mẫu Lương Rõ Ràng</div><div class="kpi-value">{valid_sal_count:,}</div><div class="kpi-subtext">{valid_sal_count/max(total_jobs,1):.1%} Tổng số tin</div></div>', unsafe_allow_html=True)
    m3.markdown(f'<div class="kpi-card"><div class="kpi-label">Lương Thỏa Thuận</div><div class="kpi-value">{negotiable_count:,}</div><div class="kpi-subtext">{negotiable_count/max(total_jobs,1):.1%} Tổng số tin</div></div>', unsafe_allow_html=True)
    m4.markdown(f'<div class="kpi-card"><div class="kpi-label">Số Ngành Nghề</div><div class="kpi-value">{cat_count}</div><div class="kpi-subtext">Categories</div></div>', unsafe_allow_html=True)
    m5.markdown(f'<div class="kpi-card"><div class="kpi-label">Tỉnh / Thành</div><div class="kpi-value">{loc_count}</div><div class="kpi-subtext">Regions</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    r1_col1, r1_col2 = st.columns(2)

    with r1_col1:
        st.markdown("### 📈 1. Top Ngành Nghề Cần Tuyển Dụng Nhiều Nhất")
        top_cats = df["category"].value_counts().head(8).reset_index()
        top_cats.columns = ["Ngành nghề", "Số tin"]
        fig1 = px.bar(
            top_cats, x="Số tin", y="Ngành nghề", orientation="h",
            color="Số tin", color_continuous_scale="blues", text="Số tin"
        )
        fig1.update_traces(textposition="outside", cliponaxis=False)
        fig1.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(polish_chart(fig1, 380), use_container_width=True)

    with r1_col2:
        st.markdown("### 🍩 2. Cơ Cấu Minh Bạch Mức Lương")
        sal_status = df["salary_status"].value_counts().reset_index()
        sal_status.columns = ["Trạng thái", "Số lượng"]
        status_map = {"provided": "Minh bạch lương", "negotiable": "Thỏa thuận", "unavailable": "Không đề cập", "invalid_range": "Sai khoảng"}
        sal_status["Trạng thái"] = sal_status["Trạng thái"].map(lambda x: status_map.get(x, x))
        
        fig2 = px.pie(
            sal_status, names="Trạng thái", values="Số lượng", hole=0.55,
            color_discrete_sequence=COLOR_PALETTE
        )
        fig2.update_traces(textinfo="percent+label")
        st.plotly_chart(polish_chart(fig2, 380), use_container_width=True)

    r2_col1, r2_col2 = st.columns(2)

    with r2_col1:
        st.markdown("### 🗺️ 3. Phân Bố Nhu Cầu Tuyển Dụng Theo Tỉnh/Thành")
        geo_df = df[~df["location_province"].isin([OTHER_LOCATION, "Nước ngoài / quốc tế"])]["location_province"].value_counts().head(8).reset_index()
        geo_df.columns = ["Tỉnh/Thành", "Số lượng tin"]
        fig3 = px.bar(
            geo_df, x="Tỉnh/Thành", y="Số lượng tin", color="Số lượng tin",
            color_continuous_scale="teal", text="Số lượng tin"
        )
        fig3.update_traces(textposition="outside")
        fig3.update_layout(coloraxis_showscale=False)
        st.plotly_chart(polish_chart(fig3, 380), use_container_width=True)

    with r2_col2:
        st.markdown("### 🔻 4. Phễu Chuyển Đổi Chất Lượng Tin Tuyển Dụng (Data Funnel)")
        funnel_data = pd.DataFrame({
            "Giai đoạn": ["1. Tổng số tin", "2. Có ngành nghề", "3. Có địa điểm rõ ràng", "4. Cung cấp khoảng lương"],
            "Số lượng": [total_jobs, df[df["category"] != UNKNOWN].shape[0], df[~df["location_province"].isin([OTHER_LOCATION])].shape[0], valid_sal_count]
        })
        fig4 = px.funnel(funnel_data, x="Số lượng", y="Giai đoạn", color_discrete_sequence=["#0284c7"])
        st.plotly_chart(polish_chart(fig4, 380), use_container_width=True)

    add_insight_card("Cơ cấu & Khả năng khai thác dữ liệu", f"Tỷ lệ tin có mức lương minh bạch chiếm {valid_sal_count/max(total_jobs,1):.1%}. Phễu dữ liệu cho thấy sự hao hụt thông tin chủ yếu ở trường lương.", "Tập trung chuẩn hóa các tin ở trạng thái 'Thỏa thuận' bằng cách phân tích NLP văn bản mô tả công việc.")

# =============================================================================
# TAB 2: PHÂN TÍCH LƯƠNG
# =============================================================================
with tab_salary:
    if salary_valid_df.empty:
        st.warning("Không đủ dữ liệu lương hợp lệ để hiển thị phân tích.")
    else:
        salary_valid_df["midpoint"] = (salary_valid_df["salary_min"] + salary_valid_df["salary_max"]) / 2
        
        s1, s2, s3, s4 = st.columns(4)
        s1.markdown(f'<div class="kpi-card"><div class="kpi-label">Lương Trung Vị (Median)</div><div class="kpi-value">{salary_valid_df["midpoint"].median():.1f}M</div><div class="kpi-subtext">VNĐ / tháng</div></div>', unsafe_allow_html=True)
        s2.markdown(f'<div class="kpi-card"><div class="kpi-label">Phân vị 25% (P25)</div><div class="kpi-value">{salary_valid_df["midpoint"].quantile(0.25):.1f}M</div><div class="kpi-subtext">Khung lương cơ bản</div></div>', unsafe_allow_html=True)
        s3.markdown(f'<div class="kpi-card"><div class="kpi-label">Phân vị 75% (P75)</div><div class="kpi-value">{salary_valid_df["midpoint"].quantile(0.75):.1f}M</div><div class="kpi-subtext">Khung lương cao cấp</div></div>', unsafe_allow_html=True)
        s4.markdown(f'<div class="kpi-card"><div class="kpi-label">Mức Lương Đỉnh (P95)</div><div class="kpi-value">{salary_valid_df["midpoint"].quantile(0.95):.1f}M</div><div class="kpi-subtext">Chuyên gia / Management</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### 📦 1. Biểu Đồ Hộp Mức Lương Theo Ngành (BoxPlot)")
            cat_sal = salary_valid_df.groupby("category").filter(lambda x: len(x) >= 5)
            fig_sal1 = px.box(
                cat_sal, y="category", x="midpoint", color="category",
                color_discrete_sequence=COLOR_PALETTE, points=False
            )
            fig_sal1.update_layout(showlegend=False, xaxis_title="Điểm giữa khoảng lương (Triệu VNĐ)")
            st.plotly_chart(polish_chart(fig_sal1, 400), use_container_width=True)

        with c2:
            st.markdown("### 🌐 2. Bản Đồ Cơ Hội: Số Lượng vs Lương Trung Vị")
            opp_df = salary_valid_df.groupby("category").agg(
                so_tin=("midpoint", "count"),
                luong_trung_vi=("midpoint", "median")
            ).reset_index()
            fig_sal2 = px.scatter(
                opp_df, x="so_tin", y="luong_trung_vi", size="so_tin", color="category",
                hover_name="category", size_max=38, color_discrete_sequence=COLOR_PALETTE
            )
            fig_sal2.update_layout(xaxis_title="Số lượng tin có lương", yaxis_title="Lương trung vị (Triệu VNĐ)")
            st.plotly_chart(polish_chart(fig_sal2, 400), use_container_width=True)

        c3, c4 = st.columns(2)

        with c3:
            st.markdown("### 📊 3. Phân Bố Tần Suất Mức Lương (Histogram)")
            hist_df = salary_valid_df[salary_valid_df["midpoint"] <= salary_valid_df["midpoint"].quantile(0.98)]
            fig_sal3 = px.histogram(
                hist_df, x="midpoint", nbins=25,
                color_discrete_sequence=["#0284c7"], title="Mật độ phân bố mức lương"
            )
            fig_sal3.update_layout(xaxis_title="Khoảng lương (Triệu VNĐ)", yaxis_title="Số lượng tin")
            st.plotly_chart(polish_chart(fig_sal3, 380), use_container_width=True)

        with c4:
            st.markdown("### 🏛️ 4. So Sánh Các Phân Vị Lương (P25 - Median - P75)")
            quantiles_df = salary_valid_df.groupby("category")["midpoint"].agg(
                P25=lambda x: x.quantile(0.25),
                Median="median",
                P75=lambda x: x.quantile(0.75)
            ).reset_index().head(6)
            fig_sal4 = px.bar(
                quantiles_df, x="category", y=["P25", "Median", "P75"],
                barmode="group", color_discrete_sequence=["#94a3b8", "#0284c7", "#4f46e5"]
            )
            fig_sal4.update_layout(xaxis_title=None, yaxis_title="Triệu VNĐ")
            st.plotly_chart(polish_chart(fig_sal4, 380), use_container_width=True)

# =============================================================================
# TAB 3: HÌNH THỨC & YÊU CẦU
# =============================================================================
with tab_employment:
    col_e1, col_e2 = st.columns(2)
    
    with col_e1:
        st.markdown("### 📑 1. Cơ Cấu Loại Hợp Đồng Tuyển Dụng")
        contract_df = df["contract_type"].map(display_value).value_counts().reset_index()
        contract_df.columns = ["Loại hợp đồng", "Số lượng"]
        fig_emp1 = px.pie(
            contract_df, names="Loại hợp đồng", values="Số lượng", hole=0.5,
            color_discrete_sequence=COLOR_PALETTE
        )
        st.plotly_chart(polish_chart(fig_emp1, 380), use_container_width=True)

    with col_e2:
        st.markdown("### ⏳ 2. Mức Độ Yêu Cầu Kinh Nghiệm")
        exp_df = df["experience_required"].map(display_value).value_counts().head(8).reset_index()
        exp_df.columns = ["Kinh nghiệm", "Số lượng"]
        fig_emp2 = px.bar(
            exp_df, x="Số lượng", y="Kinh nghiệm", orientation="h",
            color="Số lượng", color_continuous_scale="purples", text="Số lượng"
        )
        fig_emp2.update_traces(textposition="outside")
        fig_emp2.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(polish_chart(fig_emp2, 380), use_container_width=True)

    col_e3, col_e4 = st.columns(2)

    with col_e3:
        st.markdown("### 🎓 3. Yêu Cầu Trình Độ / Bằng Cấp")
        qual_df = df["qualifications"].map(display_value).value_counts().head(6).reset_index()
        qual_df.columns = ["Bằng cấp", "Số lượng"]
        fig_emp3 = px.bar(
            qual_df, x="Bằng cấp", y="Số lượng", color="Số lượng",
            color_continuous_scale="greens", text="Số lượng"  # Đã sửa 'emerald' -> 'greens'
        )
        fig_emp3.update_traces(textposition="outside")
        fig_emp3.update_layout(coloraxis_showscale=False)
        st.plotly_chart(polish_chart(fig_emp3, 380), use_container_width=True)

    with col_e4:
        st.markdown("### 🌐 4. Yêu Cầu Ngoại Ngữ Trong Tin Tuyển Dụng")
        lang_df = df["languages_required"].map(display_value).value_counts().head(6).reset_index()
        lang_df.columns = ["Ngoại ngữ", "Số lượng"]
        fig_emp4 = px.pie(
            lang_df, names="Ngoại ngữ", values="Số lượng",
            color_discrete_sequence=COLOR_PALETTE
        )
        st.plotly_chart(polish_chart(fig_emp4, 380), use_container_width=True)

# =============================================================================
# TAB 4: KỸ NĂNG NỔI BẬT
# =============================================================================
with tab_skills:
    col_sk1, col_sk2 = st.columns(2)

    with col_sk1:
        st.markdown("### 💻 1. Top Kỹ Năng Chuyên Môn (Technical Skills)")
        tech_counter = Counter()
        for v in df["technical_skills"]:
            for item in parse_items(v):
                cleaned = item.strip().lower()
                if cleaned and len(cleaned) <= 50:
                    tech_counter[cleaned] += 1
        
        tech_df = pd.DataFrame(tech_counter.most_common(10), columns=["Kỹ năng", "Tần suất"])
        fig_sk1 = px.bar(
            tech_df, x="Tần suất", y="Kỹ năng", orientation="h",
            color="Tần suất", color_continuous_scale="blues", text="Tần suất"
        )
        fig_sk1.update_traces(textposition="outside")
        fig_sk1.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(polish_chart(fig_sk1, 390), use_container_width=True)

    with col_sk2:
        st.markdown("### 🤝 2. Top Kỹ Năng Mềm (Soft Skills)")
        soft_counter = Counter()
        for v in df["soft_skills"]:
            for item in parse_items(v):
                cleaned = item.strip().lower()
                if cleaned and len(cleaned) <= 50:
                    soft_counter[cleaned] += 1
        
        soft_df = pd.DataFrame(soft_counter.most_common(10), columns=["Kỹ năng", "Tần suất"])
        fig_sk2 = px.bar(
            soft_df, x="Tần suất", y="Kỹ năng", orientation="h",
            color="Tần suất", color_continuous_scale="purples", text="Tần suất"
        )
        fig_sk2.update_traces(textposition="outside")
        fig_sk2.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(polish_chart(fig_sk2, 390), use_container_width=True)

    col_sk3, col_sk4 = st.columns(2)

    with col_sk3:
        st.markdown("### 🎯 3. Biểu Đồ Treemap Tương Quan Kỹ Năng Tech")
        if not tech_df.empty:
            fig_sk3 = px.treemap(
                tech_df, path=["Kỹ năng"], values="Tần suất",
                color="Tần suất", color_continuous_scale="viridis"
            )
            st.plotly_chart(polish_chart(fig_sk3, 380), use_container_width=True)

    with col_sk4:
        st.markdown("### 🕸️ 4. Radar Chart: So Sánh Mức Độ Phổ Biến Kỹ Năng Mềm")
        if not soft_df.empty:
            fig_sk4 = go.Figure(data=go.Scatterpolar(
                r=soft_df["Tần suất"].tolist(),
                theta=soft_df["Kỹ năng"].tolist(),
                fill='toself',
                line_color='#7c3aed'
            ))
            st.plotly_chart(polish_chart(fig_sk4, 380), use_container_width=True)

# =============================================================================
# TAB 5: DATA QUALITY
# =============================================================================
with tab_quality:
    st.markdown("### 🧪 Kiểm Soát Chất Lượng & Thiếu Dữ Liệu")
    
    col_dq1, col_dq2 = st.columns(2)

    with col_dq1:
        st.markdown("### 📊 1. Tỷ Lệ Thiếu Dữ Liệu Theo Trường (Missing Rate)")
        fields = ["category", "location", "salary", "salary_min", "salary_max", "technical_skills", "soft_skills", "experience_required"]
        missing_data = []
        for f in fields:
            null_cnt = df[f].isna().sum()
            missing_data.append({"Trường dữ liệu": f, "Tỷ lệ khuyết (%)": round(null_cnt / len(df) * 100, 2)})
        
        dq_df = pd.DataFrame(missing_data).sort_values("Tỷ lệ khuyết (%)", ascending=False)
        fig_dq1 = px.bar(
            dq_df, x="Trường dữ liệu", y="Tỷ lệ khuyết (%)", color="Tỷ lệ khuyết (%)",
            color_continuous_scale="reds", text="Tỷ lệ khuyết (%)"
        )
        fig_dq1.update_traces(texttemplate="%{text}%", textposition="outside")
        fig_dq1.update_layout(coloraxis_showscale=False)
        st.plotly_chart(polish_chart(fig_dq1, 380), use_container_width=True)

    with col_dq2:
        st.markdown("### ⚠️ 2. Phân Tích Bản Ghi Lỗi Mức Lương (Salary Anomalies)")
        bad_salary = df[df["salary_min"].notna() & df["salary_max"].notna() & (df["salary_min"] > df["salary_max"])].shape[0]
        zero_salary = df[(df["salary_min"] == 0) & (df["salary_max"] == 0)].shape[0]
        valid_sal = valid_sal_count
        
        anomaly_df = pd.DataFrame({
            "Loại bản ghi": ["Lương hợp lệ", "Min/Max bằng 0", "Min > Max (Bất thường)"],
            "Số lượng": [valid_sal, zero_salary, bad_salary]
        })
        fig_dq2 = px.pie(
            anomaly_df, names="Loại bản ghi", values="Số lượng",
            color_discrete_sequence=["#059669", "#d97706", "#dc2626"]
        )
        st.plotly_chart(polish_chart(fig_dq2, 380), use_container_width=True)

# =============================================================================
# TAB 6: TRA CỨU VIỆC LÀM
# =============================================================================
with tab_search:
    st.markdown("### 🔎 Tra Cứu & Lọc Chi Tiết Tin Tuyển Dụng")
    kw = st.text_input("Nhập từ khóa tìm kiếm (Ví dụ: Python, Data Engineer, React...)", "")
    
    filtered_search = df.copy()
    if kw:
        filtered_search = filtered_search[
            filtered_search["category"].str.contains(kw, case=False, na=False) |
            filtered_search["technical_skills"].str.contains(kw, case=False, na=False) |
            filtered_search["location"].str.contains(kw, case=False, na=False)
        ]
    
    st.markdown(f"Tìm thấy **{len(filtered_search):,}** kết quả phù hợp.")
    st.dataframe(
        filtered_search[["category", "location", "salary", "experience_required", "technical_skills"]].head(50),
        use_container_width=True
    )