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
            # Parse and clean header row at Excel row 36
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

            # Remove subtotal/core/flag rows
            eleceng = eleceng[eleceng["Course"].notna()]
            eleceng = eleceng[~eleceng["Course"].str.contains("subtotal|core|flag", case=False, na=False)]

            # Extract course code
            eleceng["Course Code"] = eleceng["Course"].astype(str).str.extract(r'^([A-Z]+\s*\d+)', expand=False)

            # Normalize course info
            course_df.columns = [col.strip().capitalize() for col in course_df.columns]
            course_df = course_df.rename(columns={"Course": "Course Code"})
            full = pd.merge(eleceng, course_df, on="Course Code", how="left")

            # ✅ CORE COURSES (only Excel row 19–70 = iloc[18:70])
            core_section = full.iloc[18:70]
            core_missing = core_section[(core_section["Flag"] != 1)]

            # ✅ TECH ELECTIVES (Flag == 1 only)
            tech_taken = full[
                (full["Flag"] == 1) &
                (full["Type"].isin(["tech elective A", "tech elective B"])) &
                (full["Course Code"].notna())
            ].copy()
            tech_taken["Level"] = tech_taken["Course Code"].str.extract(r'(\d{3})').astype(float)
            tech_taken["Level Tag"] = tech_taken["Level"].apply(lambda x: f"{int(x)}xx" if pd.notna(x) else "Unknown")

            total_taken = len(tech_taken)
            taken_400 = (tech_taken["Level"] >= 400).sum()

            # 🎓 Show missing core courses
            st.subheader("📋 Missing Required Core Courses (Rows 19–70)")
            if len(core_missing) > 0:
                st.dataframe(core_missing[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions", "Type"]])
            else:
                st.success("✅ All required core courses completed!")

            # 📊 Show tech electives taken
            st.subheader("🧮 Technical Elective Summary")
            st.markdown(f"""
            - ✅ Total technical electives taken: **{total_taken}**
            - ✅ Number of 400-level electives: **{taken_400}**
            """)

            if total_taken > 0:
                st.subheader("✅ Completed Technical Electives")
                st.dataframe(tech_taken[["Course Code", "Name", "Level Tag", "Type"]])

        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.error("Sheet 'ElecEng' not found in the uploaded degree plan.")
