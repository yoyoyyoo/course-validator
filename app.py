import streamlit as st
import pandas as pd

st.title("Course Validation Tool")

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

            # Deduplicate headers like ['AU', 'AU'] → ['AU', 'AU_1']
            seen = {}
            def dedup(col):
                if col not in seen:
                    seen[col] = 0
                    return col
                else:
                    seen[col] += 1
                    return f"{col}_{seen[col]}"
            cleaned_headers = [dedup(col.strip() if col.strip() else f"col_{i}") for i, col in enumerate(raw_headers)]

            eleceng = eleceng.iloc[36:].reset_index(drop=True)
            eleceng.columns = cleaned_headers

            # Rename first column to 'Course' if needed
            if cleaned_headers[0] != "Course":
                eleceng.rename(columns={cleaned_headers[0]: 'Course'}, inplace=True)

            # Proceed only if 'Course' and 'Flag' exist
            if 'Course' in eleceng.columns and 'Flag' in eleceng.columns:
                eleceng = eleceng[eleceng['Course'].notna()]
                eleceng = eleceng[eleceng['Flag'] != 1]
                eleceng['Course Code'] = eleceng['Course'].astype(str).str.extract(r'^([A-Z]+\\s*\\d+)', expand=False)

                course_df.columns = [col.strip().capitalize() for col in course_df.columns]
                course_df = course_df.rename(columns={"Course": "Course Code"})

                merged = pd.merge(eleceng, course_df[['Course Code', 'Prerequisite', 'Type']], on='Course Code', how='left')

                st.subheader("📋 Missing Courses with Prerequisites")
                st.dataframe(merged)
            else:
                st.error("Missing 'Course' or 'Flag' column after header assignment.")
        except Exception as e:
            st.error(f"Error processing file: {e}")
    else:
        st.error("Sheet 'ElecEng' not found in the uploaded degree plan.")
