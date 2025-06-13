import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Course Validator", layout="centered")
st.title("📘 Course Completion Validator")

def find_section(section_titles, possible_names):
    """Find first matching section header from possible names"""
    for name in possible_names:
        matches = section_titles.str.contains(name, case=False, regex=False, na=False)
        if matches.any():
            return matches.idxmax()
    return None

# File upload
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
student_file = st.file_uploader("Upload Student Progress (EE or CE)", type=["xlsx"])

if course_file and student_file:
    try:
        # Load data
        course_df = pd.read_excel(course_file)
        student_sheets = pd.read_excel(student_file, sheet_name=None)

        # Flexible sheet detection
        possible_sheets = ["eleceng", "compeng", "ee", "ce", "electrical", "computer"]
        sheet_name = next(
            (name for name in student_sheets.keys() 
             if name.strip().lower() in possible_sheets),
            None
        )

        if not sheet_name:
            st.error(f"❌ Expected sheets matching: {possible_sheets}. Found: {list(student_sheets.keys())}")
            st.stop()

        student_df = student_sheets[sheet_name]
        section_titles = student_df.iloc[:, 0].astype(str)

        # Debug: Show sheet structure
        with st.expander("🔍 Debug: Show Sheet Structure"):
            st.write("First 10 rows:", student_df.head(10))
            st.write("Last 10 rows:", student_df.tail(10))
            st.write("Unique values in first column:", student_df.iloc[:, 0].unique())

        # Locate all sections with flexible naming
        sections = {
            'core_start': find_section(section_titles, ["Common core", "Common Core Requirements"]),
            'core_end': find_section(section_titles, ["Program core", "Technical core", "Core Requirements"]),
            'progcore_end': find_section(section_titles, ["Subtotal program core", "Total Program Core"]),
            'comp_start': find_section(section_titles, ["Complementary studies", "General Education"]),
            'comp_end': find_section(section_titles, ["Subtotal complementary", "Complementary Studies Total"]),
            'tech_start': find_section(section_titles, ["List A:", "Technical Electives A", "Group A"]),
            'tech_end': find_section(section_titles, ["List B:", "Technical Electives B", "Group B"])
        }

        # Validate all sections were found
        missing_sections = [name for name, idx in sections.items() if idx is None]
        if missing_sections:
            st.error(f"❌ Missing sections: {missing_sections}")
            st.write("Please check if your file contains these headers:")
            st.write("- Common core / Program core or Technical core")
            st.write("- Complementary studies")
            st.write("- List A: / List B: or similar technical electives headers")
            st.stop()

        # Debug: Show found sections
        with st.expander("🔍 Debug: Detected Sections"):
            for name, idx in sections.items():
                st.write(f"{name}: Row {idx} - '{student_df.iloc[idx, 0]}'")

        # Rest of your processing code...
        # [Include all your existing course processing logic here]

    except Exception as e:
        st.error("❌ An unexpected error occurred")
        st.write("Please check your file structure and try again.")
        st.write("Debug info has been recorded.")
        st.stop()
