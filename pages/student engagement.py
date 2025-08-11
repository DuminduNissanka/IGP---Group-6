import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os

# Import get_dataset_by_selection from utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from my_utils import get_dataset_by_selection


# Page Setup
st.set_page_config(page_title="Student Engagement", layout="wide")
st.title("📘 Student Engagement")

# Get Dataset Selection from Session State

dataset_choice = st.session_state.get("selected_dataset")

if not dataset_choice:
    st.warning("Please select a dataset from the Home page.")
    st.stop()

st.sidebar.markdown(f"**📁 Selected Dataset:** {dataset_choice}")


#Load Dataset from utils
df, sheet_names = get_dataset_by_selection(dataset_choice)

if df is None or df.empty:
    st.error("❌ Failed to load the selected dataset.")
    st.stop()


# Week Selector (Top of Page)
week_options = ["All Weeks"] + sheet_names
week_selection = st.selectbox("📅 Select Week", options=week_options, index=0)

if week_selection != "All Weeks":
    df = df[df["Week"] == week_selection]


# Column Setup

gender_col = "Q10 How do you describe yourself? - Selected Choice"
country_col = "Q12 List of Countries"
day_columns = [
    "Student Activity by Day in hours Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday"
]
resource_columns = ["Learning_Materials_Time", "Module_Info_Time", "Reading_List_Time"]
initial_access_cols = [col for col in df.columns if col.startswith("Initial_Week_")]

# Filters (Top of Page)

st.markdown("### 🔍 Filter Data")
f1, f2 = st.columns(2)

with f1:
    gender_filter = st.selectbox("🚻 Gender", ["All"] + sorted(df[gender_col].dropna().unique()))
with f2:
    country_filter = st.selectbox("🌍 Country", ["All"] + sorted(df[country_col].dropna().unique()))

if gender_filter != "All":
    df = df[df[gender_col] == gender_filter]
if country_filter != "All":
    df = df[df[country_col] == country_filter]

#Engagement KPIs

st.markdown("### 📌 Engagement Stats")
avg_daily = df[day_columns].mean().mean()
total_learning_time = df["Learning_Materials_Time"].sum()
total_reading_time = df["Reading_List_Time"].sum()

a1, a2, a3 = st.columns(3)
a1.metric("🕒 Avg Daily Activity (hrs)", f"{avg_daily:.2f}")
a2.metric("📘 Total Learning Time", f"{total_learning_time:.1f} hrs")
a3.metric("📖 Reading Time", f"{total_reading_time:.1f} hrs")

# Activity by Day (Line Chart)

st.markdown("### 📊 Student Activity by Day")
avg_by_day = df[day_columns].mean().reset_index()
avg_by_day.columns = ["Day", "Avg Hours"]
fig_day = px.line(avg_by_day, x="Day", y="Avg Hours", markers=True)
st.plotly_chart(fig_day, use_container_width=True)


# Time Spent on Resources (Bar Chart)

st.markdown("### 🧠 Time Spent on Content Types")
resource_df = df[resource_columns].mean().reset_index()
resource_df.columns = ["Content Type", "Avg Hours"]
fig_resource = px.bar(resource_df, x="Content Type", y="Avg Hours", text_auto=True)
st.plotly_chart(fig_resource, use_container_width=True)


# Early Access to Study Materials

st.markdown("### ⏩ Accessing Next Week's Materials Early")
if initial_access_cols:
    access_df = df[initial_access_cols].notna().sum().reset_index()
    access_df.columns = ["Week", "Access Count"]
    access_df["Week"] = access_df["Week"].str.extract(r"(\d+)").astype(int)
    access_df = access_df.sort_values("Week")
    fig_early = px.area(access_df, x="Week", y="Access Count")
    st.plotly_chart(fig_early, use_container_width=True)
else:
    st.info("No early access data available.")
