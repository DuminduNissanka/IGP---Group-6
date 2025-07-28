import streamlit as st # type: ignore
import pandas as pd # type: ignore
import plotly.express as px # type: ignore
import plotly.graph_objects as go # type: ignore

# -------------------------
# ✅ Page Setup
# -------------------------
st.set_page_config(page_title="Learning Analytics Dashboard", layout="wide")

st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

st.markdown("""
    <style>
    .title-test {
        font-weight: 600;
        font-size: 28px;
        padding: 14px 24px;
        margin-top: 2rem;
        margin-bottom: 2rem;
        background-color: #0066cc;
        color: white;
        border-radius: 10px;
        width: 70%;
        text-align: center;
        margin-left: auto;
        margin-right: auto;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    }
    </style>
    <div class="title-test">🎓 Educational Dashboard</div>
""", unsafe_allow_html=True)

# -------------------------
# 📦 Load Excel sheets
# -------------------------
@st.cache_data
def load_excel_sheets(file_path):
    xls = pd.ExcelFile(file_path)
    sheets = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}
    return sheets, xls.sheet_names

file_path = "C:/Users/DuminduS/Desktop/UWE/IGP/Project/data sets/week1to11_dataset.xlsx"
sheets_dict, week_list = load_excel_sheets(file_path)

# -------------------------
# 🧭 Week & Filter Section
# -------------------------
st.markdown("### 📊 Filter Data")

col1, col2, col3 = st.columns([1, 1.5, 1.5])

with col1:
    selected_week = st.selectbox(
        "Week",
        week_list,
        index=week_list.index(st.session_state.get("selected_week", week_list[0]))
    )

# Reset filters if week changes
if selected_week != st.session_state.get("selected_week"):
    st.session_state.selected_genders = []
    st.session_state.selected_countries = []
    st.session_state.selected_week = selected_week

# Load selected week's data
df = sheets_dict[selected_week]

# Define column names
gender_col = "Q10 How do you describe yourself? - Selected Choice"
country_col = "Q12 List of Countries"
degree_col = "Q16 What is your first degree subject area?"

# Clean text columns
for col in [gender_col, country_col, degree_col]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

# Get filter options
gender_options = sorted(df[gender_col].dropna().unique()) if gender_col in df.columns else []
country_options = sorted(df[country_col].dropna().unique()) if country_col in df.columns else []

with col2:
    selected_genders = st.multiselect(
        "Gender(s):",
        options=gender_options,
        default=st.session_state.get("selected_genders", []),
        key=f"gender_{selected_week}"
    )

with col3:
    selected_countries = st.multiselect(
        "Country(ies):",
        options=country_options,
        default=st.session_state.get("selected_countries", []),
        key=f"country_{selected_week}"
    )

# Save selections
st.session_state.selected_genders = selected_genders
st.session_state.selected_countries = selected_countries

# Filter dataset
filtered_df = df.copy()
if selected_genders:
    filtered_df = filtered_df[filtered_df[gender_col].isin(selected_genders)]
if selected_countries:
    filtered_df = filtered_df[filtered_df[country_col].isin(selected_countries)]

# Handle no data case
if filtered_df.empty:
    st.warning("⚠️ No data available for the selected filters. Try selecting other options.")
    st.stop()

# -------------------------
# 📍 Country Breakdown + Week Info
# -------------------------
st.markdown(f"### 📍 Country Breakdown: {', '.join(selected_countries) if selected_countries else 'All Countries'}")
st.markdown("---")

# ✅ Dynamically display week date and student count
week_number = ''.join(filter(str.isdigit, selected_week))  # Extract week number from string
date_column = f"Date_range_week{week_number}"

if date_column in df.columns:
    week_date = df[date_column].dropna().astype(str).unique()
    date_text = week_date[0] if len(week_date) == 1 else ", ".join(week_date)
    st.markdown(f"🗓️ **Week Date:** {date_text}")
else:
    st.markdown("🗓️ **Week Date:** _Date column not found_")

st.markdown(f"👥 **Number of Students This Week:** {df.shape[0]}")

# -------------------------
# 🎓 Pie & Bar Chart
# -------------------------
col1, col2 = st.columns(2)

with col1:
    if degree_col in filtered_df.columns:
        subject_counts = (
            filtered_df[degree_col]
            .dropna()
            .value_counts()
            .reset_index(name="Count")
            .rename(columns={"index": degree_col})
        )
        fig_subject = px.pie(
            subject_counts,
            names=degree_col,
            values='Count',
            title="🎓 First Degree Subjects",
            hole=0.4
        )
        st.plotly_chart(fig_subject, use_container_width=True)
    else:
        st.warning("First degree subject column not found.")

with col2:
    if "CW4" in filtered_df.columns and gender_col in filtered_df.columns:
        chart_data = filtered_df.groupby(gender_col).agg(
            CW4_avg=('CW4', 'mean'),
            CW4_std=('CW4', 'std'),
            Count=('CW4', 'count')
        ).reset_index()

        chart_data["Label"] = chart_data[gender_col] + " (n=" + chart_data["Count"].astype(str) + ")"
        chart_data["sem"] = chart_data["CW4_std"] / chart_data["Count"]**0.5

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=chart_data["Label"],
            y=chart_data["CW4_avg"],
            error_y=dict(type='data', array=chart_data["sem"]),
            text=chart_data["CW4_avg"].round(2),
            textposition='outside',
            marker_color='skyblue'
        ))
        fig_bar.update_layout(
            title="📈 Average CW4 Score by Gender (with Sample Size and Error Bars)",
            yaxis_title="Average CW4 Score",
            xaxis_title="Gender (Sample Size)",
            height=500
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        small_groups = chart_data[chart_data["Count"] <= 3][gender_col].tolist()
        if small_groups:
            st.warning(f"⚠️ Groups with low sample size: {', '.join(small_groups)}. Averages may not be statistically reliable.")
    else:
        st.warning("CW4 or Gender column not found.")

# -------------------------
# 📌 Summary + Engagement
# -------------------------
st.markdown("### 📌 Summary Statistics")
col3, col4 = st.columns(2)
col3.metric("Total Students", filtered_df.shape[0])
col4.metric("Average CW4 Score", round(filtered_df["CW4"].mean(), 2) if "CW4" in filtered_df.columns else "N/A")

st.markdown("### ⏱️ Average Engagement Metrics")
engagement_cols = {
    "Student Time in Course (minutes)": "Avg course & student time &logins Student Time in Course",
    "Avg Time Per User (minutes)": "Avg_Time_Per_User",
    "Total Logins": "Total_Logins",
    "Learning Materials Time (hours)": "Learning_Materials_Time",
    "Reading List Time (hours)": "Reading_List_Time"
}

for label, col in engagement_cols.items():
    if col in filtered_df.columns:
        try:
            avg_val = round(pd.to_numeric(filtered_df[col], errors='coerce').mean(), 2)
            st.metric(label=label, value=avg_val)
        except Exception as e:
            st.warning(f"Could not calculate metric for {label}: {e}")
    else:
        st.warning(f"Column '{col}' not found in data.")





