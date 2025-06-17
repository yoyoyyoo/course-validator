import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Course Validator", layout="centered")

def find_section(section_titles, possible_names):
    for name in possible_names:
        matches = section_titles.str.contains(name, case=False, na=False)
        if matches.any():
            return matches.idxmax()
    return None

def process_technical_electives(student_df, program_type):
    try:
        section_titles = student_df.iloc[:, 0].astype(str)
        if program_type.lower() in ['ce', 'compeng', 'computer']:
            tech_electives_pattern = r"(Courses Offered by ECE|Courses Offered by Other Departments)"
            section_headers = section_titles[section_titles.str.contains(tech_electives_pattern, case=False)].index
            if len(section_headers) < 2:
                st.warning("⚠️ Could not find both technical elective sections for CE")
                return None
            ece_courses = student_df.iloc[section_headers[0]+1:section_headers[1]-1, :3]
            ece_courses.columns = ["Course", "Flag", "Credit"]
            other_courses = student_df.iloc[section_headers[1]+1:, :3]
            other_courses.columns = ["Course", "Flag", "Credit"]
            tech_df = pd.concat([ece_courses, other_courses])
        elif program_type.lower() in ['ee', 'eleceng', 'electrical']:
            tech_section = find_section(section_titles, ["technical electives", "electives"])
            if tech_section is None:
                st.warning("⚠️ Could not find technical electives section for EE")
                return None
            next_sections = section_titles.str.contains(r"(subtotal|total)", case=False)
            next_section_idx = next_sections[next_sections].index
            next_section_idx = next_section_idx[next_section_idx > tech_section]
            end_idx = next_section_idx[0] if len(next_section_idx) > 0 else len(student_df)
            tech_df = student_df.iloc[tech_section+1:end_idx, :3]
            tech_df.columns = ["Course", "Flag", "Credit"]
        else:
            st.error(f"Unknown program type: {program_type}")
            return None
        tech_df["Flag"] = pd.to_numeric(tech_df["Flag"], errors="coerce").fillna(0).astype(int)
        tech_taken = tech_df[tech_df["Flag"] =_]()
