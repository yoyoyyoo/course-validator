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

def process_technical_electives(student_df):
    """Process technical electives from CE format"""
    try:
        # Find all course rows in the technical electives sections
        section_titles = student_df.iloc[:, 0].astype(str)
        tech_electives_pattern = r"(Courses Offered by ECE|Courses Offered by Other Departments)"
        tech_sections = section_titles[section_titles.str.contains(tech_electives_pattern, case=False)].index
        
        if len(tech_sections) < 2:
            st.warning("⚠️ Could not find both technical elective sections")
            return None
            
        # Process ECE courses
        ece_courses = student_df.iloc[tech_sections[0]+1:tech_sections[1]-1, :3]  # Take first 3 columns
        ece_courses.columns = ["Course", "Flag", "Credit"]
        
        # Process Other Departments courses
        other_courses = student_df.iloc[tech_sections[1]+1:, :3]  # Take first 3 columns
        other_courses.columns = ["Course", "Flag", "Credit"]
        
        # Combine both sections
        tech_df = pd.concat([ece_courses, other_courses])
        
        # Convert Flag to numeric (1 = taken, 0 = not taken)
        tech_df["Flag"] = pd.to_numeric(tech_df["Flag"], errors="coerce").fillna(0).astype(int)
        
        # Filter taken courses (Flag = 1)
        tech_taken = tech_df[tech_df["Flag"] == 1].copy()
        
        # Extract course codes and levels
        tech_taken["Course Code"] = tech_taken["Course"].str.extract(r"([A-Z]{4}\s?\d{3})")[0].str.strip()
        tech_taken = tech_taken.dropna(subset=["Course Code"])
        tech_taken["Level"] = tech_taken["Course Code"].str.extract(r"(\d{3})").astype(float)
        
        return tech_taken
        
    except Exception as e:
        st.error(f"Error processing technical electives: {str(e)}")
        with st.expander("Debug Info"):
            if 'tech_df' in locals():
                st.write("Technical electives data sample:", tech_df.head())
            st.write("Student DF columns:", student_df.columns.tolist())
            st.write("Student DF shape:", student_df.shape)
        return None

def main():
    st.title("📘 Course Completion Validator")
    st.write("Upload your files to validate course completion")
    
    # File upload widgets
    course_file = st.file_uploader("Course Info (test_courses.xlsx)", type=["xlsx"])
    student_file = st.file_uploader("Student Progress (EE/CE)", type=["xlsx"])
    
    if not course_file or not student_file:
        st.info("ℹ️ Please upload both files to begin validation")
        return

    try:
        # Load data
        with st.spinner("Loading files..."):
            course_df = pd.read_excel(course_file)
            student_sheets = pd.read_excel(student_file, sheet_name=None)
            
            # Clean course data
            course_df.columns = [col.strip() for col in course_df.columns]
            course_df["Course Code"] = course_df["Course Code"].str.strip().str.upper()
        
        # Sheet detection
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
        
        # Process technical electives
        with st.spinner("Analyzing technical electives..."):
            tech_taken = process_technical_electives(student_df)
            
            if tech_taken is not None:
                total_taken = len(tech_taken)
                taken_400 = (tech_taken["Level"] >= 400).sum()
                remaining = max(0, 5 - total_taken)
                
                st.subheader("🛠 Technical Electives Summary")
                cols = st.columns(3)
                cols[0].metric("Total Taken", total_taken)
                cols[1].metric("400+ Level", taken_400)
                cols[2].metric("Remaining", remaining)
                
                if not tech_taken.empty:
                    with st.expander("View taken electives"):
                        st.dataframe(tech_taken[["Course Code", "Level", "Credit"]].reset_index(drop=True))
                else:
                    st.warning("No technical electives marked as completed (Flag = 1)")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        with st.expander("Technical details"):
            st.exception(e)

if __name__ == "__main__":
    main()
