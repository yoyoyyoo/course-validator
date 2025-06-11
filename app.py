import streamlit as st
import pandas as pd

st.title("Course Progress Validator")

course_file = st.file_uploader("Upload Course Info Excel", type=["xlsx"])
degree_file = st.file_uploader("Upload Degree Plan Excel", type=["xlsx"])

if course_file and degree_file:
    course_df = pd.read_excel(course_file)
    degree_df = pd.read_excel(degree_file, sheet_name=None)

    if 'ElecEng' in degree_df:
        eleceng = degree_df['ElecEng']

        try:
            # Load header at row 35
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
            eleceng = eleceng.rename(columns={"col_0": "Course"})

            # Filter valid rows
            eleceng = eleceng[eleceng["Course"].notna()]
            missing_courses = eleceng[eleceng["Flag"] != 1].copy()
            missing_courses["Course Code"] = missing_courses["Course"].astype(str).str.extract(r'^([A-Z]+\s*\d+)', expand=False)

            # Normalize course info
            course_df.columns = [col.strip().capitalize() for col in course_df.columns]
            course_df = course_df.rename(columns={"Course": "Course Code"})

            # Merge to get full course info
            merged = pd.merge(missing_courses, course_df, on="Course Code", how="left")

            # Split core vs tech elective
            tech_missing = merged[merged["Type"].isin(["A", "B"])].copy()
            core_missing = merged[~merged["Type"].isin(["A", "B"])].copy()

            # Count 400-level electives
            tech_missing["Level"] = tech_missing["Course Code"].str.extract(r'(\d{3})').astype(float)
            total_tech = len(tech_missing)
            total_400 = (tech_missing["Level"] >= 400).sum()

            # Show stats
            st.subheader("📊 Technical Elective Summary")
            st.write(f"🔹 Missing technical electives: **{total_tech}**")
            st.write(f"🔹 400-level or higher: **{total_400}**")
            if total_tech < 5:
                st.warning("⚠️ Students must complete at least **5** technical electives.")
            if total_400 < 4:
                st.warning("⚠️ At least **4** technical electives must be at the 400 level or above.")

            # Show core missing list
            st.subheader("📋 Missing Core Courses")
            if len(core_missing) > 0:
                st.dataframe(core_missing[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions", "Type"]])
            else:
                st.success("✅ No missing core courses detected!")

        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.error("Sheet 'ElecEng' not found in the uploaded degree plan.")
