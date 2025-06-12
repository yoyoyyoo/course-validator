import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="EE Course Validator", layout="centered")
st.title("📘 Electrical Engineering Course Validator")

# Upload files
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload Student Record (EE_202X.xlsx)", type=["xlsx"])

if course_file and degree_file:
    try:
        course_df = pd.read_excel(course_file)
        course_df.columns = [col.strip() for col in course_df.columns]
        course_df["Course Code"] = course_df["Course Code"].astype(str).str.strip().str.upper()

        sheets = pd.read_excel(degree_file, sheet_name=None)
        if "ElecEng" not in sheets:
            st.error("❌ 'ElecEng' sheet not found.")
            st.stop()

        eleceng_df = sheets["ElecEng"]

        def find_row(df, keyword):
            for i, val in enumerate(df.iloc[:, 0].astype(str)):
                if keyword.lower() in val.lower():
                    return i
            return None

        # ---- Auto-locate sections ----
        core_start = find_row(eleceng_df, "Common core - 1st year")
        core_end = find_row(eleceng_df, "Program core - 2nd/3rd-year")

        comp_start = find_row(eleceng_df, "Complementary studies electives")
        comp_end = find_row(eleceng_df, "Subtotal complementary studies")

        tech_start = find_row(eleceng_df, "Technical electives")
        tech_end = find_row(eleceng_df, "Subtotal technical electives")

        # 🧩 Extract Core
        core = eleceng_df.iloc[core_start + 2 : core_end, [0, 1]].copy()
        core.columns = ["Course", "Flag"]
        core["Flag"] = pd.to_numeric(core["Flag"], errors="coerce").fillna(0).astype(int)
        core["Course Code"] = core["Course"].astype(str).str.extract(r'([A-Z]+\s*\d+[A-Z]*)')[0]
        core["Course Code"] = core["Course Code"].str.replace(r"\s+", " ", regex=True).str.strip().str.upper()

        core_missing = core[(core["Flag"] == 0) & core["Course Code"].notna()]
        core_merged = pd.merge(core_missing, course_df, on="Course Code", how="left")

        st.subheader("📋 Missing Required Core Courses")
        if not core_merged.empty:
            st.dataframe(core_merged[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions"]])
        else:
            st.success("✅ All core courses are completed.")

        # 🧾 Complementary Studies
        if comp_start and comp_end:
            comp = eleceng_df.iloc[comp_start + 2 : comp_end, [0, 1]].copy()
            comp.columns = ["Course", "Flag"]
            comp["Flag"] = pd.to_numeric(comp["Flag"], errors="coerce").fillna(0).astype(int)

            comp_taken = comp[comp["Flag"] == 1]
            st.subheader("🧾 Complementary Studies")
            st.markdown(f"✅ Completed: **{len(comp_taken)}**")
            st.markdown(f"❗ Still Required: **{max(0, 3 - len(comp_taken))}**")

            if not comp_taken.empty:
                st.markdown("**Courses Taken:**")
                for course in comp_taken["Course"]:
                    st.markdown(f"- {course}")

        # ⚙️ Technical Electives
        if tech_start and tech_end:
            tech = eleceng_df.iloc[tech_start + 2 : tech_end, [0, 1]].copy()
            tech.columns = ["Course", "Flag"]
            tech["Flag"] = pd.to_numeric(tech["Flag"], errors="coerce").fillna(0).astype(int)
            tech["Course Code"] = tech["Course"].astype(str).str.extract(r'([A-Z]+\s*\d+[A-Z]*)')[0]
            tech["Course Code"] = tech["Course Code"].str.replace(r"\s+", " ", regex=True).str.strip().str.upper()

            tech_taken = tech[(tech["Flag"] == 1) & tech["Course Code"].notna()]
            tech_merged = pd.merge(tech_taken, course_df, on="Course Code", how="left")

            tech_merged["Level"] = tech_merged["Course Code"].str.extract(r'(\d{3})')[0].astype(float)
            count_taken = len(tech_merged)
            count_400 = (tech_merged["Level"] >= 400).sum()
            missing_400 = max(0, 5 - count_400)

            st.subheader("⚙️ Technical Electives")
            st.markdown(f"- ✅ Taken: **{count_taken}**")
            st.markdown(f"- ✅ 400-level or above: **{count_400}**")
            st.markdown(f"- ❗ Still need: **{missing_400} more at 400-level**")

            if not tech_merged.empty:
                st.dataframe(tech_merged[["Course Code", "Name", "Credits"]])

    except Exception as e:
        st.error(f"❌ Error: {e}")
