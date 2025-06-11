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
            new_header = eleceng.iloc[32].fillna("").astype(str).tolist()
            eleceng = eleceng.iloc[33:].reset_index(drop=True)
            eleceng.columns = [f"col_{i}" if col.strip() == "" else col.strip() for i, col in enumerate(new_header)]

            st.write("### Cleaned Column Names:")
            st.write(eleceng.columns.tolist())  # 🔍 This will help us identify the exact column names

        except Exception as e:
            st.error(f"Error processing degree plan file: {e}")
    else:
        st.error("Sheet 'ElecEng' not found in the uploaded degree plan.")
