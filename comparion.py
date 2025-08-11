import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# Page Setup
st.set_page_config(page_title="Dataset Comparison", layout="wide")
st.title("📊 Comparison: Group vs Individual Assignment Behavior")

# File Paths 
path1 = Path("C:/Users/DuminduS/Desktop/UWE/IGP/Project/Code/DatasetforStreamlit/cleaned_Newdata01.xlsx")  # Group
path2 = Path("C:/Users/DuminduS/Desktop/UWE/IGP/Project/Code/DatasetforStreamlit/cleaned_new2_revised_2.xlsx")  # Individual

try:
    # Load all sheets and tag by week
    xls1 = pd.ExcelFile(path1)
    xls2 = pd.ExcelFile(path2)

    df1_all = pd.concat([xls1.parse(sheet).assign(Week=sheet) for sheet in xls1.sheet_names], ignore_index=True)
    df2_all = pd.concat([xls2.parse(sheet).assign(Week=sheet) for sheet in xls2.sheet_names], ignore_index=True)

    df1_all.columns = df1_all.columns.str.strip()
    df2_all.columns = df2_all.columns.str.strip()

except Exception as e:
    st.error(f"❌ Failed to load or parse Excel files: {e}")
    st.stop()

# Filter for common students
students_group = set(df1_all['Student_ID'].unique())
students_indiv = set(df2_all['Student_ID'].unique())
common_students = students_group.intersection(students_indiv)

df1_common = df1_all[df1_all['Student_ID'].isin(common_students)].copy()
df2_common = df2_all[df2_all['Student_ID'].isin(common_students)].copy()

# Compute Scores 
df1_scores = df1_common.groupby('Student_ID')["Overall Result"].mean().rename("Group_Assignment_Score")
df2_scores = df2_common.groupby('Student_ID')["Overall Result"].mean().rename("Individual_Assignment_Score")

# Compute Logins
login_cols_group = [col for col in df1_common.columns if 'Times Accessed' in col]
login_cols_indiv = [col for col in df2_common.columns if 'Times Accessed' in col]

df1_login = df1_common.groupby('Student_ID')[login_cols_group].apply(lambda x: (x > 0).sum().sum()).rename("Group_Logins")
df2_login = df2_common.groupby('Student_ID')[login_cols_indiv].apply(lambda x: (x > 0).sum().sum()).rename("Individual_Logins")

# Merge All 
final_df = pd.concat([df1_scores, df2_scores, df1_login, df2_login], axis=1).dropna()

# Plot Mean Logins Comparison
st.subheader("🔄 Average Logins: Group vs Individual")

login_means = final_df[["Group_Logins", "Individual_Logins"]].mean().reset_index()
login_means.columns = ['Assignment Type', 'Mean Logins']

fig, ax = plt.subplots(figsize=(7, 5))
sns.barplot(data=login_means, x='Assignment Type', y='Mean Logins', ax=ax)
ax.set_title("Average Logins by Assignment Type")
plt.tight_layout()
st.pyplot(fig)

# Optional: Preview Table
st.subheader("📋 Student-Level Comparison (Top 10)")
st.dataframe(final_df.head(10))
