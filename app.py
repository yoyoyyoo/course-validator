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
            # 🔍 Try to detect the true header row automatically
            header_index = None
            for i in range(30, 45):
                row = eleceng.iloc[i].astype(str).str.lower()
                if "course" in row.values and "flag" in row.values:
                    header_index = i
                    break

            if header_index is None:
                st.error("Could not find a header row with both 'Course' and 'Flag'.")
            else:
                # Use detected header row
                new_header = eleceng.iloc[header_index].fillna("").astype(str).tolist()
                eleceng = eleceng.iloc[header_index + 1:].reset_index(drop=True)
                eleceng.columns = [f"col_{i}" if col.strip() == "" else col.strip() for i, col in enumerate(new_header)]

                st.write("✅ Detected header row:", header_index)
                st.write("Columns:", eleceng.columns.tolist())

                # Rename if needed
                if 'Course' not in eleceng.columns:
                    eleceng.rename(columns={eleceng.columns[0]: 'Course'}, inplace=True)

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
                    st.error("Missing 'Course' or 'Flag' column after header detection.")
        except Exception as e:
            st.error(f"Error processing degree plan file: {e}")
    else:
        st.error("Sheet 'ElecEng' not found in the uploaded degree plan.")
