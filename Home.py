import streamlit as st
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from my_utils import load_excel

#Sidebar Dataset Selector
st.sidebar.title("📁 Select Dataset")

dataset = st.sidebar.selectbox(
    "Choose Dataset",
    ["", "Group Based Engagement", "Individual Based Engagement"]
)

#Save Selection in Session and Redirect
if dataset and st.session_state.get("selected_dataset") != dataset:
    st.session_state["selected_dataset"] = dataset
    st.session_state["redirected"] = False

if dataset and not st.session_state.get("redirected", False):
    st.session_state["redirected"] = True
   st.switch_page("pages/1_Summary.py")



# Navigation
st.sidebar.markdown("---")

# Main Page Display
st.title("Learning Analytics Dashboard")
st.write("Please select a dataset from the sidebar to begin.")

# Show current dataset info
if "selected_dataset" in st.session_state:
    st.success(f"📊 Current Dataset: **{st.session_state['selected_dataset']}**")
