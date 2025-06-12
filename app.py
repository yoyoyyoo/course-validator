import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="EE Course Validator", layout="centered")
st.title("📘 Electrical Engineering Course Validator")

def find_section_index(df, keyword):
    """Find the first row index containing the keyword in column 0."""
    for i in range(len(df)):
        val = str(df.iloc[i, 0])
        if keyword.lower() in val.lower():
            return i
    return None

def extract_section(df, start, end, header_offset=1):
    header_row = df.iloc[start - header_offset]
    section_df = df.iloc[start:end].copy()
    section_df.columns = header_row
    section_df.reset_index(drop=True, inplace=True)
    section_df.columns = [str(col).strip() if col else f"col_{i}" for i, col in enumerate(section_df.columns)]
    section_df.rename(columns={section_df.columns[0]: "Course Raw"}, inplace=True)
    section_df["Flag"] = pd.to_numeric(section_df.get("Flag", section_df.iloc[:, 1]), errors="coerce").fillna(0)
    section_df["Course Code"] = section_df["Course Raw"].astype(str).str.extract(r'([A-Z]+\s*\d+[A-Z]*)')
    section_df["Course Code"] = section_df["Course Code"].str.replace(r'\s+', ' ', regex=True).str.upper().str.strip()
    return section_df

def merge_missing_courses(section_df, course_df, title="Missing Courses"):
    missing = section_df[(section_df["Flag"] == 0) & (section_df["Course Code"].notna())]
    merged = pd.merge(
        missing,
        course_df[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions"]],
        on="Course Code",
        how="left"
    )
    if not merged.empty:
        st.subheader(f"📋 {title}")
        st.dataframe(merged[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions"]])
    return merged

# Upload files
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload Student Record (EE_2026.xlsx)", type=["xlsx"])

if course_file and degree_file:
    try:
        course_df = pd.read_excel(course_file)
        course_df.columns = [col.strip() for col in course_df.columns]
        course_df["Course Code"] = course_df["Course Code"].str.strip().str.upper()
        course_df["Course Code"] = course_df["Course Code"].str.replace(r'([A-Z]+)(\d{3})', r'\1 \2', regex=True)

        df = pd.read_excel(degree_file, sheet_name="ElecEng", header=None)

        # --- Identify sections dynamically ---
        common_core_start = find_section_index(df, "Common core - 1st year")
        program_core_start = find_section_index(df, "Program core - 2nd/3rd-year")
        technical_core_start = find_section_index(df, "Technical core - 4th year")
        complementary_start = find_section_index(df, "Complementary studies")
        complementary_end = complementary_start + 3 if complementary_start else None
        tech_electives_start = find_section_index(df, "Technical Electives")
        tech_electives_end = find_section_index(df, "Capstone Design Project") or len(df)

        # --- Extract sections ---
        core1_df = extract_section(df, common_core_start + 1, program_core_start)
        core2_df = extract_section(df, program_core_start + 2, technical_core_start)
        complementary_df = extract_section(df, complementary_start + 1, complementary_end, header_offset=1)
        tech_df = extract_section(df, tech_electives_start + 1, tech_electives_end, header_offset=1)

        # --- Missing Core Courses ---
        merge_missing_courses(core1_df, course_df, "Missing Common Core Courses")
        merge_missing_courses(core2_df, course_df, "Missing ELEC Core Courses")

        # --- Complementary Studies ---
        st.subheader("📘 Complementary Studies")
        complementary_taken = complementary_df[complementary_df["Flag"] == 1]
        taken_comp = len(complementary_taken)
        missing_comp = max(0, 3 - taken_comp)
        st.markdown(f"- ✅ Completed: **{taken_comp}**")
        st.markdown(f"- ❗ Still Required: **{missing_comp}**")
        if not complementary_taken.empty:
            st.dataframe(complementary_taken[["Course Raw", "Course Code"]])

        # --- Technical Electives ---
        st.subheader("📗 Technical Electives")
        tech_taken = tech_df[tech_df["Flag"] == 1].copy()
        tech_taken["Level"] = tech_taken["Course Code"].str.extract(r'(\d{3})')[0].astype(float)
        num_taken = len(tech_taken)
        num_400 = (tech_taken["Level"] >= 400).sum()
        missing_400 = max(0, 5 - num_400)

        st.markdown(f"- ✅ Taken: **{num_taken}**")
        st.markdown(f"- ✅ 400-level or higher: **{num_400}**")
        st.markdown(f"- ❗ Still need **{missing_400} more 400-level** courses to meet the minimum")

        tech_taken_named = pd.merge(
            tech_taken,
            course_df[["Course Code", "Name"]],
            on="Course Code",
            how="left"
        )

        if not tech_taken_named.empty:
            st.dataframe(tech_taken_named[["Course Code", "Name", "Level"]])

    except Exception as e:
        st.error(f"❌ Error: {e}")
