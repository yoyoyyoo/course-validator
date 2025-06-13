import streamlit as st
import pandas as pd
import re

# Page config MUST be first
st.set_page_config(page_title="Course Validator", layout="centered")

def find_section(section_titles, possible_names):
    """Flexible section finder with debug info"""
    for name in possible_names:
        matches = section_titles.str.contains(name, case=False, na=False)
        if matches.any():
            return matches.idxmax()
    return None

def main():
    st.title("📘 Course Completion Validator")
    st.write("Upload your files to validate course completion")
    
    # File upload widgets
    col1, col2 = st.columns(2)
    with col1:
        course_file = st.file_uploader("Course Info (test_courses.xlsx)", type=["xlsx"])
    with col2:
        student_file = st.file_uploader("Student Progress (EE/CE)", type=["xlsx"])
    
    if not course_file or not student_file:
        st.info("ℹ️ Please upload both files to begin validation")
        return

    try:
        # Load data with progress indicators
        with st.spinner("Loading course data..."):
            course_df = pd.read_excel(course_file)
            course_df.columns = [col.strip() for col in course_df.columns]
            course_df["Course Code"] = course_df["Course Code"].str.strip().str.upper()

        with st.spinner("Loading student progress..."):
            student_sheets = pd.read_excel(student_file, sheet_name=None)
            
            # Flexible sheet detection
            possible_sheets = ["eleceng", "compeng", "ee", "ce", "electrical", "computer"]
            sheet_name = next(
                (name for name in student_sheets.keys() 
                 if name.strip().lower() in possible_sheets),
                None
            )
            
            if not sheet_name:
                st.error(f"❌ Couldn't find expected sheet. Available sheets: {list(student_sheets.keys())}")
                return
                
            student_df = student_sheets[sheet_name]
            section_titles = student_df.iloc[:, 0].astype(str)

        # Section detection with multiple possible names
        sections = {
            'core_start': find_section(section_titles, ["Common core"]),
            'core_end': find_section(section_titles, ["Program core", "Technical core"]),
            'progcore_end': find_section(section_titles, ["Subtotal program core"]),
            'comp_start': find_section(section_titles, ["Complementary studies"]),
            'comp_end': find_section(section_titles, ["Subtotal complementary"]),
            'tech_start': find_section(section_titles, ["List A:", "Technical Electives"]),
            'tech_end': find_section(section_titles, ["List B:", "Technical Electives"])
        }

        # Validate sections
        missing = [k for k,v in sections.items() if v is None]
        if missing:
            st.error(f"❌ Missing sections: {missing}")
            with st.expander("Show sheet structure"):
                st.dataframe(student_df.head(15))
            return

        # Process core courses
        with st.spinner("Analyzing core courses..."):
            core = student_df.iloc[sections['core_end']+1:sections['progcore_end']].copy()
            core.columns = student_df.iloc[sections['core_start']+1]
            core = core[core["Flag"] == 0]
            core["Course Code"] = core.iloc[:, 0].astype(str).str.extract(r"([A-Z]{4}\s?\d{3})")[0].str.strip()
            core = core.dropna(subset=["Course Code"])
            core = pd.merge(core, course_df, on="Course Code", how="inner")
            
            st.subheader("📋 Core Courses Status")
            if core.empty:
                st.success("✅ All core courses completed")
            else:
                st.dataframe(core[["Course Code", "Name", "Term"]].style.highlight_null("red"))

        # Process complementary studies
        with st.spinner("Checking complementary studies..."):
            comp = student_df.iloc[sections['comp_start']+2:sections['comp_end'], [0, 1]].copy()
            comp.columns = ["Course", "Flag"]
            comp["Flag"] = pd.to_numeric(comp["Flag"], errors="coerce").fillna(0).astype(int)
            comp_taken = comp[comp["Flag"] == 1]
            
            st.subheader("🧾 Complementary Studies")
            cols = st.columns(2)
            cols[0].metric("Completed", len(comp_taken))
            cols[1].metric("Remaining", max(0, 3 - len(comp_taken)))
            
            if not comp_taken.empty:
                with st.expander("View taken courses"):
                    st.dataframe(comp_taken)

        # Process technical electives
        with st.spinner("Analyzing technical electives..."):
            tech = student_df.iloc[sections['tech_start']+1:sections['tech_end'], [0, 1]].copy()
            tech.columns = ["Course", "Flag"]
            tech["Flag"] = pd.to_numeric(tech["Flag"], errors="coerce").fillna(0).astype(int)
            tech_taken = tech[tech["Flag"] == 1].copy()
            tech_taken["Course Code"] = tech_taken["Course"].str.extract(r"([A-Z]{4}\s?\d{3})")[0].str.strip()
            tech_taken = tech_taken.dropna(subset=["Course Code"])
            tech_taken["Level"] = tech_taken["Course Code"].str.extract(r"(\d{3})").astype(float)
            
            st.subheader("🛠 Technical Electives")
            cols = st.columns(3)
            cols[0].metric("Total Taken", len(tech_taken))
            cols[1].metric("400+ Level", (tech_taken["Level"] >= 400).sum())
            cols[2].metric("Remaining", max(0, 5 - len(tech_taken)))
            
            if not tech_taken.empty:
                with st.expander("View technical electives"):
                    st.dataframe(tech_taken)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.write("Please check your file formats and try again.")
        with st.expander("Technical details"):
            st.exception(e)

if __name__ == "__main__":
    main()
