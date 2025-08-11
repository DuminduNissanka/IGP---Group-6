import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import sys, os

# ✅ Add utils path BEFORE importing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from my_utils import get_dataset_by_selection

# -------------------------
# ✅ Page Setup
# -------------------------
st.set_page_config(page_title="Summary Dashboard", layout="wide")
st.title("🎓 Educational Dashboard – Summary View")

# -------------------------
# 📦 Get Dataset Selection from Session State
# -------------------------
dataset_choice = st.session_state.get("selected_dataset")

if not dataset_choice:
    st.warning("Please select a dataset from the Home page.")
    st.stop()

st.sidebar.markdown(f"**📁 Selected Dataset:** {dataset_choice}")

# -------------------------
# 📁 Load Dataset from utils
# -------------------------
full_df, sheet_names = get_dataset_by_selection(dataset_choice)  # ✅ Keep unfiltered original
df = full_df.copy()  # ✅ Working copy

if df is None or df.empty:
    st.error("❌ Failed to load the selected dataset.")
    st.stop()

st.success(f"📊 Currently using: **{dataset_choice}**")

# -------------------------
# Column Mapping
# -------------------------
gender_col = "Q10 How do you describe yourself? - Selected Choice"
country_col = "Q12 List of Countries"
degree_col = "Q16 What is your first degree subject area?"
age_col = "Q14 What is your year of birth (Just the year, e.g. 1995) ?"
score_cols = ["CW2", "CW3", "CW4", "CC1 [FA] (100)"]
student_id_col = "StudentID"  # 🔁 Replace with your actual student ID column if needed

# -------------------------
# 🗂 Week Selector
# -------------------------
week_options = ["All Weeks"] + sheet_names
week_selection = st.selectbox("📅 Select Week", options=week_options, index=0)

if week_selection != "All Weeks":
    df = df[df["Week"] == week_selection]

# -------------------------
# 🧽 Clean Data
# -------------------------
for col in [gender_col, country_col, degree_col, age_col]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

current_year = datetime.datetime.now().year
df["Age"] = pd.to_numeric(df[age_col], errors='coerce')
df["Age"] = current_year - df["Age"]
df = df[df["Age"].between(18, 100)]

# -------------------------
# 🔍 Filters (Gender, Country)
# -------------------------
st.markdown("### 🔎 Filter Data")
f1, f2 = st.columns(2)

with f1:
    gender_filter = st.selectbox("🧑 Gender", options=["All"] + sorted(df[gender_col].dropna().unique()))
with f2:
    country_filter = st.selectbox("🌍 Country", options=["All"] + sorted(df[country_col].dropna().unique()))

if gender_filter != "All":
    df = df[df[gender_col] == gender_filter]
if country_filter != "All":
    df = df[df[country_col] == country_filter]

# -------------------------
# 📌 Summary KPIs
# -------------------------
st.markdown("### 📌 Key Statistics")
k1, k2, k3, k4 = st.columns(4)

with k1:
    if week_selection == "All Weeks":
        # Use Week_1 from full_df
        week1_df = full_df[full_df["Week"] == "Week_1"]

        # Clean and process Week 1 data
        for col in [gender_col, country_col, degree_col, age_col]:
            if col in week1_df.columns:
                week1_df[col] = week1_df[col].astype(str).str.strip()

        # ✅ Age filtering
        current_year = datetime.datetime.now().year
        week1_df["Age"] = pd.to_numeric(week1_df[age_col], errors='coerce')
        week1_df["Age"] = current_year - week1_df["Age"]
        week1_df = week1_df[week1_df["Age"].between(18, 100)]

        # Apply filters
        if gender_filter != "All":
            week1_df = week1_df[week1_df[gender_col] == gender_filter]
        if country_filter != "All":
            week1_df = week1_df[week1_df[country_col] == country_filter]

        # Unique student count
        if student_id_col in week1_df.columns:
            total_students = week1_df[student_id_col].nunique()
        else:
            total_students = len(week1_df)
    else:
        if student_id_col in df.columns:
            total_students = df[student_id_col].nunique()
        else:
            total_students = len(df)

    st.metric("👥 Total Students", total_students)



with k2:
    avg_scores = df[score_cols].mean(numeric_only=True) if all(col in df.columns for col in score_cols) else pd.Series()
    st.metric("📊 Avg Marks", f"{avg_scores.mean():.2f}" if not avg_scores.empty else "N/A")

with k3:
    login_cols = [col for col in df.columns if "Time_accessed" in col or "Initial_" in col]

    if login_cols:
        login_df = df[login_cols].copy()
        for col in login_cols:
            if pd.api.types.is_datetime64_any_dtype(login_df[col]):
                login_df[col] = (login_df[col] - login_df[col].min()).dt.total_seconds()
            else:
                login_df[col] = pd.to_numeric(login_df[col], errors='coerce')

        avg_login_time = login_df.sum(axis=1).mean()
        st.metric("🕒 Avg Login Time", f"{avg_login_time:.1f} min")
    else:
        st.metric("🕒 Avg Login Time", "N/A")

with k4:
    avg_age = df["Age"].mean()
    st.metric("🧑‍🦳 Avg Age", f"{avg_age:.1f}")

# -------------------------
# 📊 Charts
# -------------------------
st.markdown("### 📊 Distribution Overview")

c1, c2 = st.columns(2)
with c1:
    st.markdown("#### 🎓 Top 5 Degree Subjects")
    if degree_col in df.columns:
        top_degrees = df[degree_col].value_counts().nlargest(5)
        fig_degrees = px.pie(values=top_degrees.values, names=top_degrees.index, hole=0.5)
        st.plotly_chart(fig_degrees, use_container_width=True)
    else:
        st.warning("Degree subject data not available.")

with c2:
    st.markdown("#### 🚻 Gender Distribution")
    if gender_col in df.columns:
        gender_counts = df[gender_col].value_counts()
        fig_gender = px.pie(values=gender_counts.values, names=gender_counts.index, hole=0.5)
        st.plotly_chart(fig_gender, use_container_width=True)
    else:
        st.warning("Gender data not available.")

c3, c4 = st.columns(2)
with c3:
    st.markdown("#### 🌍 Top 5 Countries")
    if country_col in df.columns:
        top_countries = df[country_col].value_counts().nlargest(5)
        fig_country = px.pie(values=top_countries.values, names=top_countries.index, hole=0.5)
        st.plotly_chart(fig_country, use_container_width=True)
    else:
        st.warning("Country data not available.")

with c4:
    st.markdown("#### 👶 Age Distribution")
    if "Age" in df.columns:
        fig_age = px.histogram(df, x="Age", nbins=10, title="Age Histogram")
        fig_age.update_layout(xaxis_title="Age", yaxis_title="Count", bargap=0.1)
        st.plotly_chart(fig_age, use_container_width=True)
    else:
        st.warning("Age data not available.")

