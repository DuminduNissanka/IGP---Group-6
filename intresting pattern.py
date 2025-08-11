import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import sys, os

from scipy.stats import linregress

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from my_utils import get_dataset_by_selection


#Page Setup

st.set_page_config(page_title="Interesting Patterns", layout="wide")
st.title("🔍 Interesting Patterns")


# Dataset Selection from Session

dataset_choice = st.session_state.get("selected_dataset")

if not dataset_choice:
    st.warning("Please select a dataset from the Home page.")
    st.stop()

st.sidebar.markdown(f"**📁 Selected Dataset:** {dataset_choice}")


# Load Dataset

df, sheet_names = get_dataset_by_selection(dataset_choice)

if df is None or df.empty:
    st.error("❌ Failed to load the selected dataset.")
    st.stop()


# Student Next-Week Access Trend

st.subheader("📊 1. Student Access in Following Week (Trend)")

student_access = pd.DataFrame()

for i in range(1, 11):  # Week_1 to Week_10
    sheet_name = f"Week_{i}"
    if sheet_name not in sheet_names:
        continue

    weekly_df = df[df["Week"] == sheet_name]

    next_week_col = [col for col in weekly_df.columns if f"{i+1}" in col and 'access' in col.lower()]
    id_col = [col for col in weekly_df.columns if 'student' in col.lower() and 'id' in col.lower()]

    if next_week_col and id_col:
        col_access = next_week_col[0]
        col_id = id_col[0]

        temp = weekly_df[[col_id, col_access]].copy()
        temp.columns = ['Student_ID', f'W{i}_to_W{i+1}']
        temp = temp.groupby('Student_ID').sum()
        student_access = pd.concat([student_access, temp], axis=1)

# Line Chart for Avg Trend 
if not student_access.empty:
    student_access = student_access.fillna(0).sort_index(axis=1).reset_index()
    avg_access_trend = student_access.drop(columns='Student_ID').mean().reset_index()
    avg_access_trend.columns = ['Week_Transition', 'Average_Access']

    fig_trend = px.line(
        avg_access_trend,
        x='Week_Transition',
        y='Average_Access',
        markers=True,
        title='Average Student Access in the Next Week'
    )
    fig_trend.update_layout(xaxis_title='Week Transition', yaxis_title='Average Access Count')
    st.plotly_chart(fig_trend, use_container_width=True)


    # Calculate Total Access Per Student 
    student_access['Total_Next_Week_Access'] = student_access.drop(columns='Student_ID').sum(axis=1)
    student_total = student_access[['Student_ID', 'Total_Next_Week_Access']]

    # Load Marks (Assume Week_1 has marks)
    week_1_df = df[df['Week'] == 'Week_1']
    marks_cols = [col for col in week_1_df.columns if 'mark' in col.lower() or 'score' in col.lower() or 'result' in col.lower()]
    id_col = [col for col in week_1_df.columns if 'student' in col.lower() and 'id' in col.lower()][0]
    marks_df = week_1_df[[id_col] + marks_cols].copy()
    marks_df.columns = ['Student_ID'] + marks_cols

    # Merge and Analyze 
    merged = student_total.merge(marks_df, on='Student_ID', how='left')
    top_5 = merged.sort_values(by='Total_Next_Week_Access', ascending=False).head(5)
    bottom_5 = merged.sort_values(by='Total_Next_Week_Access', ascending=True).head(5)

    # Top 5 Proactive Students 
    st.subheader("🔝 Top 5 Proactive Students")
    fig_top, ax_top = plt.subplots(figsize=(4, 3)) 
    ax_top.bar(top_5['Student_ID'].astype(str), top_5['Total_Next_Week_Access'], color='green')
    ax_top.set_ylabel("Next-Week Access Count")
    ax_top.set_xlabel("Student ID")
    ax_top.set_title("Top 5 Most Proactive Students")
    st.pyplot(fig_top)


    # Bottom 5 Least Proactive Students 
    st.subheader("🔻 Bottom 5 Least Proactive Students")
    fig_bot, ax_bot = plt.subplots()
    ax_bot.bar(bottom_5['Student_ID'].astype(str), bottom_5['Total_Next_Week_Access'], color='red')
    ax_bot.set_ylabel("Next-Week Access Count")
    ax_bot.set_xlabel("Student ID")
    ax_bot.set_title("Bottom 5 Least Proactive Students")
    st.pyplot(fig_bot)

    # Access vs Marks Table 
    st.subheader("📊 Access vs Marks")
    st.dataframe(pd.concat([top_5, bottom_5])[['Student_ID', 'Total_Next_Week_Access'] + marks_cols])

    # Correlation Analysis
    if marks_cols:
        correlation = merged['Total_Next_Week_Access'].corr(merged[marks_cols[0]])
        
else:
    st.info("Next-week access data is not available in the dataset.")


if 'Week_1' in sheet_names:
    df_w1 = df[df['Week'] == 'Week_1'].copy()

    week_cols = [col for col in df_w1.columns if 'Time_accessed_week' in col]
    early_cols = [col for col in week_cols if any(str(w) in col for w in [1, 2, 3])]

    if early_cols and 'Overall Result' in df_w1.columns:
        # Compute engagement metrics
        df_w1['Engagement_Slope'] = df_w1[week_cols].apply(
            lambda row: linregress(range(1, len(week_cols)+1), row)[0], axis=1
        )
        df_w1['Engagement_Variance'] = df_w1[week_cols].std(axis=1)
        df_w1['Early_Engagement_Avg'] = df_w1[early_cols].mean(axis=1)

        # Identify at-risk students
        df_w1['At_Risk'] = (df_w1['Early_Engagement_Avg'] < 2) & (df_w1['Overall Result'] < 40)

        output_df = df_w1[['Student_ID', 'Early_Engagement_Avg', 'Overall Result', 'At_Risk']].dropna()

        # Histogram of Early Engagement
        fig_hist = px.histogram(
            output_df,
            x='Early_Engagement_Avg',
            nbins=20,
            color='At_Risk',
            barmode='overlay',
            color_discrete_map={True: 'red', False: 'green'},
            title='Early Engagement Distribution (Weeks 1–3)'
        )
        st.plotly_chart(fig_hist, use_container_width=True)

     
        st.warning("Required columns for this analysis are missing.")
else:
    st.warning("Week_1 data not available in the dataset.")






# Early Engagement vs Performance (Binned View)

st.subheader("🚨 2. Early Engagement vs Performance")

if 'Week_1' in sheet_names:
    df_w1 = df[df['Week'] == 'Week_1'].copy()

    week_cols = [col for col in df_w1.columns if 'Time_accessed_week' in col]
    early_cols = [col for col in week_cols if any(str(w) in col for w in [1, 2, 3])]

    if early_cols and 'Overall Result' in df_w1.columns:
        df_w1['Early_Engagement_Avg'] = df_w1[early_cols].mean(axis=1)
        df_w1['At_Risk'] = (df_w1['Early_Engagement_Avg'] < 2) & (df_w1['Overall Result'] < 40)

        # Bin early engagement into ranges
        bins = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 5]
        labels = ['0–0.5', '0.5–1', '1–1.5', '1.5–2', '2–2.5', '2.5–3', '3–3.5', '3.5+']
        df_w1['Engagement_Bin'] = pd.cut(df_w1['Early_Engagement_Avg'], bins=bins, labels=labels, right=False)

        # Group and aggregate
        grouped = df_w1.groupby('Engagement_Bin').agg(
            Avg_Result=('Overall Result', 'mean'),
            At_Risk_Count=('At_Risk', 'sum'),
            Total=('At_Risk', 'count')
        ).reset_index()

        grouped['At_Risk_Percent'] = (grouped['At_Risk_Count'] / grouped['Total']) * 100

        # Plot bar chart: Avg Result per engagement bin
        fig_bar = px.bar(
            grouped,
            x='Engagement_Bin',
            y='Avg_Result',
            text='Avg_Result',
            title='📊 Average Result by Early Engagement Level',
            labels={'Engagement_Bin': 'Early Engagement (Weeks 1–3)', 'Avg_Result': 'Average Result (%)'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)


    else:
        st.warning("Required columns for this analysis are missing.")
else:
    st.warning("Week_1 data not available in the dataset.")


# Total Engagement vs Final Result (Performance Band View)

st.subheader("🧭 3. Total Engagement vs Final Result")

# Filter Week_1 data from already-loaded DataFrame
df_w1 = df[df["Week"] == "Week_1"].copy()

# Get columns like 'Time_accessed_week1', etc.
week_cols = [col for col in df_w1.columns if 'Time_accessed_week' in col]

if 'Overall Result' in df_w1.columns and week_cols:
    # Sum total engagement time across week columns
    df_w1['Total_Access_Time'] = df_w1[week_cols].sum(axis=1)

    # Categorize performance bands
    def categorize(score):
        if score >= 70:
            return 'Distinction'
        elif score >= 60:
            return 'Merit'
        elif score >= 50:
            return 'Pass'
        else:
            return 'Fail'

    df_w1['Performance_Band'] = df_w1['Overall Result'].apply(categorize)

    if 'Student_ID' in df_w1.columns:
        df_w1['Student_ID'] = df_w1['Student_ID'].astype(str)
    else:
        df_w1['Student_ID'] = df_w1.index.astype(str) 

    # catterplot using Plotly
    fig_perf = px.scatter(
        df_w1,
        x='Total_Access_Time',
        y='Overall Result',
        color='Performance_Band',
        hover_name='Student_ID',
        title='Total Engagement Time vs Overall Performance',
        labels={
            'Total_Access_Time': 'Total Engagement Time (All Weeks)',
            'Overall Result': 'Final Result (%)',
            'Performance_Band': 'Performance Category'
        },
        color_discrete_map={
            'Distinction': 'blue',
            'Merit': 'green',
            'Pass': 'orange',
            'Fail': 'red'
        },
    )

    fig_perf.update_traces(marker=dict(size=10, line=dict(width=0.5, color='DarkSlateGrey')))
    fig_perf.update_layout(title_x=0.5)

    st.plotly_chart(fig_perf, use_container_width=True)

else:
    st.warning("Missing necessary columns for this analysis.")



st.subheader("🕒 5. Login Frequency by 2-Hour Time Windows")

try:
    # Use the dataset already loaded via get_dataset_by_selection
    df_time = df.copy()

    # Identify timestamp columns
    time_cols = [col for col in df_time.columns if "initial" in col.lower()]

    if not time_cols:
        st.warning("⚠️ No timestamp columns found with 'initial' in the column name.")
    else:
        # Convert to datetime
        for col in time_cols:
            df_time[col] = pd.to_datetime(df_time[col], errors='coerce')

        # Reshape to long format for plotting
        long_df = df_time.melt(value_vars=time_cols, var_name='Resource', value_name='AccessTime')
        long_df.dropna(subset=['AccessTime'], inplace=True)

        # Create 2-hour time windows
        long_df['Hour'] = long_df['AccessTime'].dt.hour
        long_df['2-Hour Window'] = long_df['Hour'].apply(
            lambda x: f"{x - x % 2:02d}:00 - {x - x % 2 + 1:02d}:59"
        )

        # Set ordering
        bins_order = [f"{h:02d}:00 - {h+1:02d}:59" for h in range(0, 24, 2)]
        long_df["2-Hour Window"] = pd.Categorical(long_df["2-Hour Window"], categories=bins_order, ordered=True)

        # Count logins per window
        window_counts = long_df['2-Hour Window'].value_counts().sort_index()

        # Plot
        import plotly.graph_objects as go
        fig_time = go.Figure(go.Bar(
            x=window_counts.index,
            y=window_counts.values,
            marker_color='steelblue'
        ))

        fig_time.update_layout(
            title="Login Frequency by 2-Hour Time Windows",
            xaxis_title="Time Window",
            yaxis_title="Number of Logins",
            xaxis_tickangle=-45,
            template="simple_white",
            title_x=0.5
        )

        st.plotly_chart(fig_time, use_container_width=True)

       
except Exception as e:
    st.error(f"❌ Failed to generate time-based login chart: {e}")



