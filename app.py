import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Course Validator", layout="centered")
st.title("📘 Course Completion Validator")

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

        # Clean course data
        course_df.columns = [col.strip() for col in course_df.columns]
        course_df["Course Code"] = course_df["Course Code"].str.strip().str.upper()

        # Flexible section detection
        section_titles = student_df.iloc[:, 0].astype(str)
        
        def find_section(possible_names):
            """Find first matching section header from possible names"""
            for name in possible_names:
                matches = section_titles.str.contains(name, case=False, na=False)
                if matches.any():
                    return matches.idxmax()
            return None

        # Locate all sections with flexible naming
        sections = {
            'core_start': find_section(["Common core", "Common Core Requirements"]),
            'core_end': find_section(["Program core", "Technical core", "Core Requirements"]),
            'progcore_end': find_section(["Subtotal program core", "Total Program Core"]),
            'comp_start': find_section(["Complementary studies", "General Education"]),
            'comp_end': find_section(["Subtotal complementary", "Complementary Studies Total"]),
            'tech_start': find_section(["List A:", "Technical Electives A"]),
            'tech_end': find_section(["List B:", "Technical Electives B"])
        }

        # Validate all sections were found
        missing_sections = [name for name, idx in sections.items() if idx is None]
        if missing_sections:
            st.error(f"❌ Missing sections: {missing_sections}")
            st.write("First 15 rows for reference:")
            st.dataframe(student_df.head(15))
            st.stop()

        # Extract course sections
        # 1. Core Courses
        core = student_df.iloc[sections['core_end']+1:sections['progcore_end']].copy()
        if not core.empty:
            core.columns = student_df.iloc[sections['core_start']+1]
            core = core[core["Flag"] == 0]
            core["Course Code"] = core.iloc[:, 0].astype(str).str.extract(r"([A-Z]{4}\s?\d{3})")[0].str.strip()
            core = core.dropna(subset=["Course Code"])
            core = pd.merge(core, course_df, on="Course Code", how="inner")
            
            st.subheader("📋 Incomplete Core Courses")
            if core.empty:
                st.success("✅ All core courses completed.")
            else:
                st.dataframe(core[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions", "Term"]])

        # 2. Complementary Studies
        comp = student_df.iloc[sections['comp_start']+2:sections['comp_end'], [0, 1]].copy()
        comp.columns = ["Course", "Flag"]
        comp["Flag"] = pd.to_numeric(comp["Flag"], errors="coerce").fillna(0).astype(int)
        comp_taken = comp[comp["Flag"] == 1]

        st.subheader("🧾 Complementary Studies Summary")
        st.markdown(f"✅ Completed: **{len(comp_taken)}**")
        st.markdown(f"❗ Still Required: **{max(0, 3 - len(comp_taken))}**")
        if not comp_taken.empty:
            st.markdown("**Courses Taken:**")
            for course in comp_taken["Course"]:
                st.markdown(f"- {course}")

        # 3. Technical Electives
        tech = student_df.iloc[sections['tech_start']+1:sections['tech_end'], [0, 1]].copy()
        tech.columns = ["Course", "Flag"]
        tech["Flag"] = pd.to_numeric(tech["Flag"], errors="coerce").fillna(0).astype(int)
        tech_taken = tech[tech["Flag"] == 1].copy()
        tech_taken["Course Code"] = tech_taken["Course"].astype(str).str.extract(r"([A-Z]{4}\s?\d{3})")[0].str.strip()
        tech_taken = tech_taken.dropna(subset=["Course Code"])
        tech_taken["Level"] = tech_taken["Course Code"].str.extract(r"(\d{3})").astype(float)

        total_taken = len(tech_taken)
        taken_400 = (tech_taken["Level"] >= 400).sum()
        missing_400 = max(0, 5 - taken_400)

        st.subheader("🛠 Technical Electives Summary")
        st.markdown(f"✅ Taken: **{total_taken}**")
        st.markdown(f"✅ 400-level or above: **{taken_400}**")
        if total_taken < 5:
            st.warning(f"❗ You still need **{5 - total_taken}** more technical electives.")
        if missing_400 > 0:
            st.warning(f"❗ Missing 400-level: **{missing_400}**")
        if not tech_taken.empty:
            st.markdown("**Courses Taken:**")
            for course in tech_taken["Course"]:
                st.markdown(f"- {course}")

    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        st.write("Debug info - last 5 rows processed:")
        if 'core' in locals():
            st
