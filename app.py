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
            # Clean and deduplicate header row (row 35)
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

            # ✅ CORE COURSES (not tech electives) – only rows 19 to 70
            core_section = full.iloc[18:70]
            core_missing = core_section[(core_section["Flag"] != 1) & (~core_section["Type"].isin(["tech elective A", "tech elective B"]))]

            # ✅ TECH ELECTIVES (taken only)
            tech_taken = full[
                (full["Flag"] == 1) &
                (full["Type"].isin(["tech elective A", "tech elective B"])) &
                (full["Course Code"].notna())
            ].copy()

            tech_taken["Level"] = tech_taken["Course Code"].str.extract(r'(\d{3})').astype(float)
            tech_taken["Level Tag"] = tech_taken["Level"].apply(lambda x: f"{int(x)}xx" if pd.notna(x) else "Unknown")

            total_taken = len(tech_taken)
            taken_400 = (tech_taken["Level"] >= 400).sum()
            missing_400 = max(0, 5 - taken_400)

            # 🎓 CORE
            st.subheader("📋 Missing Core Courses (Row 19–70 Only)")
            if len(core_missing) > 0:
                st.dataframe(core_missing[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions", "Type"]])
            else:
                st.success("✅ No missing core courses in the selected range!")

            # 📊 TECH ELECTIVE SUMMARY
            st.subheader("🧮 Technical Elective Summary")
            st.markdown(f"""
            - ✅ Taken: **{total_taken}**
            - ✅ 400-level or above: **{taken_400}**
            - ❗ Still need **{missing_400}** more at 400-level to reach the required 5
            """)

            if total_taken < 5:
                st.warning("⚠️ You must complete **at least 5 technical electives.**")
            if taken_400 < 5:
                st.warning("⚠️ You must complete **at least 5 technical electives at 400-level or above.**")

            if total_taken > 0:
                st.subheader("✅ Completed Technical Electives")
                st.dataframe(tech_taken[["Course Code", "Name", "Level Tag", "Type"]])

        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.error("Sheet 'ElecEng' not found in the uploaded degree plan.")
