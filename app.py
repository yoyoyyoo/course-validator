import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Course Validator", layout="centered")
st.title("📘 Course Completion Validator")

# file upload
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
student_file = st.file_uploader("Upload Student Progress (EE_2025 or CE)", type=["xlsx"])

if course_file and student_file:
    try:
        course_df = pd.read_excel(course_file)
        student_sheets = pd.read_excel(student_file, sheet_name=None)

        # ✅ ElecEng or CompEng sheet
        possible_sheets = ["ElecEng", "CompEng"]
        sheet_name = next((s for s in possible_sheets if s in student_sheets), None)

        if not sheet_name:
            st.error("❌ Could not find a valid sheet. Expecting 'ElecEng' or 'CompEng'.")
            st.stop()

        student_df = student_sheets[sheet_name]

        # course info
        course_df.columns = [col.strip() for col in course_df.columns]
        course_df["Course Code"] = course_df["Course Code"].str.strip().str.upper()

        # section locate
        section_titles = student_df.iloc[:, 0].astype(str)
        core_start = section_titles[section_titles.str.contains("Common core", case=False)].index[0]
        core_end = section_titles[section_titles.str.contains("Program core", case=False)].index[0]
        progcore_end = section_titles[section_titles.str.contains("Subtotal program core", case=False)].index[0]
        comp_start = section_titles[section_titles.str.contains("Complementary studies", case=False)].index[0]
        comp_end = section_titles[section_titles.str.contains("Subtotal complementary", case=False)].index[0]
        tech_start = section_titles[section_titles.str.contains("List A:", case=False)].index[0]
        tech_end = section_titles[section_titles.str.contains("List B:", case=False)].index[0]

        # 🟦 complementary
        core = student_df.iloc[core_end + 1:progcore_end].copy()
        core.columns = student_df.iloc[core_start + 1]
        core = core[core["Flag"] == 0]
        core["Course Code"] = core.iloc[:, 0].astype(str).str.extract(r"([A-Z]{4}\s?\d{3})")[0].str.strip()
        core = core.dropna(subset=["Course Code"])
        core = pd.merge(core, course_df, on="Course Code", how="inner")  
        st.subheader("📋 Incomplete Core Courses")
        if core.empty:
            st.success("✅ All core courses completed.")
        else:
            st.dataframe(core[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions", "Term"]])

        # 🧾 Complementary Studies
        comp = student_df.iloc[comp_start + 2:comp_end, [0, 1]].copy()
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

        # 🛠 Technical Electives
        tech = student_df.iloc[tech_start + 1:tech_end, [0, 1]].copy()
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
        st.error(f"❌ Error: {str(e)}")
