import streamlit as st
import pandas as pd

st.title("Course Completion Validator")

course_file = st.file_uploader("Upload Course Info Excel", type=["xlsx"])
degree_file = st.file_uploader("Upload Degree Plan Excel", type=["xlsx"])

if course_file and degree_file:
    course_df = pd.read_excel(course_file)
    degree_df = pd.read_excel(degree_file, sheet_name=None)

    if 'ElecEng' in degree_df:
        eleceng = degree_df['ElecEng']

        try:
            # Set row 35 as header
            raw_headers = eleceng.iloc[35].fillna("").astype(str).tolist()
            seen = {}
            def dedup(col):
                if col not in seen:
                    seen[col] = 0
                    return col
                seen[col] += 1
                return f"{col}_{seen[col]}"
            headers = [dedup(col.strip() if col.strip() else f"col_{i}") for i, col in enumerate(raw_headers)]

            eleceng = eleceng.iloc[36:].reset_index(drop=True)
            eleceng.columns = headers
            eleceng.rename(columns={"col_0": "Course"}, inplace=True)

            # Normalize and merge with course database
            eleceng = eleceng[eleceng["Course"].notna()]
            eleceng["Course Code"] = eleceng["Course"].astype(str).str.extract(r'^([A-Z]+\s*\d+)', expand=False)

            course_df.columns = [col.strip().capitalize() for col in course_df.columns]
            course_df = course_df.rename(columns={"Course": "Course Code"})
            full = pd.merge(eleceng, course_df, on="Course Code", how="left")

            ### 🔹 CORE COURSES (non-tech electives)
            core_missing = full[(full["Flag"] != 1) & (~full["Type"].isin(["A", "B"]))]

            ### 🔹 TECH ELECTIVES (List A + B)
            tech_taken = full[(full["Flag"] == 1) & (full["Type"].isin(["A", "B"]))].copy()
            tech_taken["Level"] = tech_taken["Course Code"].str.extract(r'(\d{3})').astype(float)

            count_total = len(tech_taken)
            count_400 = (tech_taken["Level"] >= 400).sum()

            ### 🔸 Display Results
            st.subheader("📋 Missing Core Courses")
            if len(core_missing) > 0:
                st.dataframe(core_missing[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions", "Type"]])
            else:
                st.success("✅ No missing core courses detected!")

            st.subheader("🧮 Technical Elective Summary")
            st.markdown(f"""
                - ✅ Completed technical electives (A + B): **{count_total}**
                - ✅ Of which are 400-level or above: **{count_400}**
            """)
            if count_total < 5:
                st.warning("⚠️ Students must complete **at least 5** technical electives.")
            if count_400 < 5:
                st.warning("⚠️ Students must complete **at least 5 at the 400 level or higher.**")

            if count_total > 0:
                st.subheader("✅ Completed Technical Electives (A/B)")
                st.dataframe(tech_taken[["Course Code", "Name", "Type", "Prerequisite", "Corequisite", "Exclusions"]])

        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.error("Sheet 'ElecEng' not found in the uploaded degree plan.")
