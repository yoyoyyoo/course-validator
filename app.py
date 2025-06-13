import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="EE Validator", layout="centered")
st.title("📘 Electrical Engineering Course Validator")

# Upload files
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
record_file = st.file_uploader("Upload Student Record (EE_20xx.xlsx)", type=["xlsx"])

def extract_course_code(text):
    """Extract standardized course code like ELEC 270 from string"""
    if pd.isna(text):
        return None
    match = re.match(r"([A-Z]{4})\s?(\d{3})", str(text).strip())
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return None

if course_file and record_file:
    try:
        course_df = pd.read_excel(course_file)
        course_df["Course Code"] = course_df["Course Code"].str.strip().str.upper()

        student_sheets = pd.read_excel(record_file, sheet_name=None)
        if "ElecEng" not in student_sheets:
            st.error("❌ 'ElecEng' sheet not found.")
            st.stop()

        df = student_sheets["ElecEng"]

        # Identify section titles
        section_titles = df.iloc[:, 0].astype(str).str.lower()
        core_start = section_titles[section_titles.str.contains("common core")].index[0] + 1
        core_end = section_titles[section_titles.str.contains("program core")].index[0]
        prog_start = core_end + 1
        prog_end = section_titles[section_titles.str.contains("complementary studies")].index[0]
        comp_start = prog_end + 1
        comp_end = section_titles[section_titles.str.contains("subtotal complementary")].index[0]
        tech_start = section_titles[section_titles.str.contains("list a:")].index[0]
        tech_end = section_titles[section_titles.str.contains("list b:")].index[0]

        # 🟡 Incomplete Core Courses (must exist in test_courses)
        core_df = df.iloc[prog_start:prog_end, [0, 1]].copy()
        core_df.columns = ["Raw", "Flag"]
        core_df["Course Code"] = core_df["Raw"].apply(extract_course_code)
        core_df["Flag"] = pd.to_numeric(core_df["Flag"], errors="coerce").fillna(0).astype(int)
        core_df = core_df[core_df["Flag"] == 0]
        merged_core = pd.merge(core_df, course_df, on="Course Code", how="inner")

        st.subheader("📋 Incomplete Core Courses")
        if merged_core.empty:
            st.success("✅ All core courses completed.")
        else:
            st.dataframe(merged_core[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions", "Term"]])

        # 🧾 Complementary Studies
        comp_df = df.iloc[comp_start:comp_end, [0, 1]].copy()
        comp_df.columns = ["Course", "Flag"]
        comp_df["Flag"] = pd.to_numeric(comp_df["Flag"], errors="coerce").fillna(0).astype(int)
        comp_taken = comp_df[comp_df["Flag"] == 1]

        st.subheader("📑 Complementary Studies Summary")
        st.markdown(f"✅ Completed: **{len(comp_taken)}**")
        st.markdown(f"❗ Still Required: **{max(0, 3 - len(comp_taken))}**")
        if not comp_taken.empty:
            st.markdown("**Courses Taken:**")
            for c in comp_taken["Course"]:
                st.markdown(f"- {c}")

        # 🧰 Technical Electives
        tech_df = df.iloc[tech_start:tech_end, [0, 1]].copy()
        tech_df.columns = ["Raw", "Flag"]
        tech_df["Course Code"] = tech_df["Raw"].apply(extract_course_code)
        tech_df["Flag"] = pd.to_numeric(tech_df["Flag"], errors="coerce").fillna(0).astype(int)

        tech_taken = tech_df[(tech_df["Flag"] == 1) & tech_df["Course Code"].notna()]
        tech_taken["Level"] = tech_taken["Course Code"].str.extract(r'(\d{3})').astype(float)
        taken_400 = tech_taken[tech_taken["Level"] >= 400]

        st.subheader("🛠️ Technical Electives Summary")
        st.markdown(f"✅ Taken: **{len(tech_taken)}**")
        st.markdown(f"✅ 400-level or above: **{len(taken_400)}**")
        missing_400 = max(0, 5 - len(taken_400))
        st.markdown(f"❗ You still need **{missing_400} 400-level technical electives.**")
        if not tech_taken.empty:
            st.markdown("**Courses Taken:**")
            for c in tech_taken["Raw"]:
                st.markdown(f"- {c}")

    except Exception as e:
        st.error(f"❌ Error: {e}")
