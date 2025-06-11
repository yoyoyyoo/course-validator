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
            # Use row 32 as header
            new_header = eleceng.iloc[32].fillna("").astype(str).tolist()
            eleceng = eleceng.iloc[33:].reset_index(drop=True)
            eleceng.columns = [f"col_{i}" if col.strip() == "" else col.strip() for i, col in enumerate(new_header)]

            # Rename first column to 'Course' if needed
            if 'Course' not in eleceng.columns:
                eleceng.rename(columns={eleceng.columns[0]: 'Course'}, inplace=True)

            # Only proceed if 'Flag' and 'Course' exist
            if 'Course' in eleceng.columns and 'Flag' in eleceng.columns:
                eleceng = eleceng[eleceng['Course'].notna()]
                eleceng = eleceng[eleceng['Flag'] != 1]
                eleceng['Course Code'] = eleceng['Course'].astype(str).str.extract(r'^([A-Z]+\s*\d+)', expand=False)

                # Clean course_df
                course_df.columns = [col.strip().capitalize() for col in course_df.columns]
                course_df = course_df.rename(columns={"Course": "Course Code"})

                # Merge and display
                merged = pd.merge(eleceng, course_df[['Course Code', 'Prerequisite', 'Type']], on='Course Code', how='left')
                st.subheader("Missing Courses with Prerequisites")
                st.dataframe(merged)
            else:
                st.error("Missing 'Course' or 'Flag' column after cleaning headers.")
        except Exception as e:
            st.error(f"Error processing degree plan file: {e}")
    else:
        st.error("Sheet 'ElecEng' not found in the uploaded degree plan.")
