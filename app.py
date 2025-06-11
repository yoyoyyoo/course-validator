
import streamlit as st
import pandas as pd

st.title("Course Validation Tool")

course_file = st.file_uploader("Upload Course Info Excel", type=["xlsx"])
degree_file = st.file_uploader("Upload Degree Plan Excel", type=["xlsx"])

if course_file and degree_file:
    course_df = pd.read_excel(course_file)
    degree_df = pd.read_excel(degree_file, sheet_name=None)
    eleceng = degree_df.get('ElecEng')

    if eleceng is not None:
        eleceng.columns = eleceng.iloc[32]
        eleceng = eleceng.drop(index=range(0, 33)).reset_index(drop=True)
        eleceng.columns = ["Course" if pd.isna(col) else col for col in eleceng.columns]
        eleceng = eleceng[eleceng["Course"].notna()]
        df_missing = eleceng[eleceng["Flag"] != 1].copy()
        df_missing['Course Code'] = df_missing['Course'].str.extract(r'^([A-Z]+\s*\d+)')
        course_df.columns = [col.strip().capitalize() for col in course_df.columns]
        course_df = course_df.rename(columns={"Course": "Course Code"})

        merged = pd.merge(df_missing, course_df[['Course Code', 'Prerequisite', 'Type']], on='Course Code', how='left')
        st.subheader("Missing Courses with Prerequisites")
        st.dataframe(merged)
    else:
        st.error("Sheet 'ElecEng' not found in degree plan file.")
