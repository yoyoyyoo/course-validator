import streamlit as st
import pandas as pd
import re

# Page config MUST be the first Streamlit command
st.set_page_config(page_title="Course Validator", layout="centered")

# Then other imports (if any additional ones are needed)
# Then function definitions
def find_section(section_titles, possible_names):
    """Find first matching section header from possible names"""
    for name in possible_names:
        matches = section_titles.str.contains(name, case=False, regex=False, na=False)
        if matches.any():
            return matches.idxmax()
    return None

# Then your main app code
st.title("📘 Course Completion Validator")

