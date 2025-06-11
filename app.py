import streamlit as st
import pandas as pd

st.title("Technical Elective Validator")

course_file = st.file_uploader("Upload Course Info Excel", type=["xlsx"])
degree_file = st.file_uploader("Upload Degree Plan Excel", type=["xlsx"])

if course_file and degree_file:
    course_df = pd.read_excel(course_file)
    degree_df = pd.read_excel(degree_file, sheet_name=None)

    if 'ElecEng' in degree_df:
        eleceng = degree_df['ElecEng']

        try:
            # Set row 35 as header and deduplicate
            raw_headers = eleceng.iloc[35].fillna("").astype(str).tolist()
            seen = {}
            def dedup(col):
                if col not in seen:
                    seen[col] = 0
                    return col
                seen[col] += 1
                return f"{col}_{seen[col]}"
            headers = [dedup(col.strip() or f"col_{i}") for i, col in enumerate(raw_headers)]

            eleceng = eleceng.iloc[36:].reset_index(drop=True)
            eleceng.columns = headers
            if headers[0] != "Course":
                eleceng.rename(columns={headers[0]: "Course"}, inplace=True)

            # Filter missing courses
            if 'Course' in eleceng.columns and 'Flag' in eleceng.columns:
                eleceng = eleceng[eleceng['Course'].notna()]
                missing = eleceng[eleceng['Flag'] != 1].copy()
                missing['Course Code'] = missing['Course'].astype(str).str.extract(r'^([A-Z]+\\s*\\d+)', expand=False)

                # Clean and merge course info
                course_df.columns = [col.strip().capitalize() for col in course_df.columns]
                course_df = course_df.rename(columns={"Course": "Course Code"})

                tech_courses = course_df[course_df['Type'].isin(['A', 'B'])].copy()
                merged = pd.merge(missing, tech_courses, on='Course Code', how='inner')

                # Count how many are 400-level+
                merged['Level'] = merged['Course Code'].str.extract(r'(\d{3})').astype(float)
                total_missing = len(merged)
                missing_400 = (merged['Level'] >= 400).sum()

                # Display summary
                st.info(f"📌 You are missing {total_missing} technical electives.")
                st.info(f"✅ Of these, {missing_400} are 400-level or higher.")
                if total_missing < 5:
                    st.warning("⚠️ Students must complete at least 5 technical electives.")
                if missing_400 < 4:
                    st.warning("⚠️ Students must include at least 4 technical electives at the 400 level or higher.")

                # Show selected columns
                st.subheader("📋 Missing Technical Electives")
                st.dataframe(merged[['Course Code', 'Name', 'Prerequisite', 'Corequisite', 'Exclusions', 'Type']])
            else:
                st.error("Missing 'Course' or 'Flag' columns.")
        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.error("Sheet 'ElecEng' not found in the uploaded degree plan.")
