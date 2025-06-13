import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="EE Course Validator", layout="centered")
st.title("📘 Electrical Engineering Course Validator")

# Upload section
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload Student Record (EE_202X.xlsx)", type=["xlsx"])

if course_file and degree_file:
    try:
        # Read and clean course info
        course_df = pd.read_excel(course_file)
        course_df.columns = [col.strip() for col in course_df.columns]
        course_df.rename(columns=lambda x: x.strip().title(), inplace=True)

        # ✅ Ensure Course Code exists
        if "Course Code" not in course_df.columns:
            st.error("❌ 'Course Code' column not found in uploaded test_courses.xlsx")
            st.write("Found columns:", list(course_df.columns))
            st.stop()

        course_df["Course Code"] = course_df["Course Code"].str.strip().str.upper()

        # Read degree plan
        degree_df = pd.read_excel(degree_file, sheet_name=None)
        eleceng = degree_df.get("ElecEng")

        if eleceng is None:
            st.error("❌ 'ElecEng' sheet not found.")
            st.stop()

        # Identify section markers
        section_indices = {}
        for i, val in enumerate(eleceng.iloc[:, 0]):
            if isinstance(val, str):
                key = val.strip().lower()
                if "common core" in key:
                    section_indices["core_start"] = i
                elif "program core" in key:
                    section_indices["core_end"] = i
                elif "complementary" in key:
                    section_indices["comp_start"] = i
                elif "list a" in key:
                    section_indices["comp_end"] = i
                elif "technical electives" in key:
                    section_indices["tech_start"] = i
                elif "list b" in key:
                    section_indices["tech_end"] = i

        # 📋 Incomplete Core Courses
        if "core_start" in section_indices and "core_end" in section_indices:
            core = eleceng.iloc[section_indices["core_start"] + 1 : section_indices["core_end"], [0, 1]].copy()
            core.columns = ["Course", "Flag"]
            core["Course Code"] = core["Course"].str.extract(r'([A-Z]+\s*\d{3})')
            core["Flag"] = pd.to_numeric(core["Flag"], errors="coerce").fillna(0).astype(int)
            core_missing = core[(core["Flag"] == 0) & (core["Course Code"].notna())]

            merged_core = pd.merge(core_missing, course_df, on="Course Code", how="inner")

            st.subheader("📋 Incomplete Core Courses")
            if not merged_core.empty:
                st.dataframe(merged_core[["Course Code", "Name", "Term", "Prerequisite", "Corequisite", "Exclusions"]])
            else:
                st.success("✅ All core courses completed.")

        # 🧾 Complementary Studies
        if "comp_start" in section_indices and "comp_end" in section_indices:
            comp = eleceng.iloc[section_indices["comp_start"] + 2 : section_indices["comp_end"], [0, 1]].copy()
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

        # 🛠️ Technical Electives
        if "tech_start" in section_indices and "tech_end" in section_indices:
            tech = eleceng.iloc[section_indices["tech_start"] + 1 : section_indices["tech_end"], [0, 1]].copy()
            tech.columns = ["Course", "Flag"]
            tech["Flag"] = pd.to_numeric(tech["Flag"], errors="coerce").fillna(0).astype(int)
            tech["Course Code"] = tech["Course"].str.extract(r'([A-Z]+\s*\d{3})')
            tech["Level"] = tech["Course Code"].str.extract(r'(\d{3})').astype(float)

            tech_completed = tech[(tech["Flag"] == 1) & (tech["Course Code"].notna())]
            total_taken = len(tech_completed)
            taken_400 = (tech_completed["Level"] >= 400).sum()
            missing_400 = max(0, 5 - taken_400)

            st.subheader("🛠️ Technical Electives Summary")
            st.markdown(f"✅ Taken: **{total_taken}**")
            st.markdown(f"✅ 400-level or above: **{taken_400}**")
            st.markdown(f"❗ You still need **5 400-level technical electives**.")
            st.markdown(f"❗ Missing 400-level: **{missing_400}**")

            if not tech_completed.empty:
                st.markdown("**Courses Taken:**")
                for course in tech_completed["Course"]:
                    st.markdown(f"- {course}")

    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.info("Please verify the structure of both Excel files.")
