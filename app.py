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
        
        # Extract course codes and names
        tech_taken["Course Code"] = tech_taken["Course"].str.extract(r"([A-Z]{4}\s?\d{3})")[0].str.strip()
        tech_taken["Course Name"] = tech_taken["Course"].str.replace(r"[A-Z]{4}\s?\d{3}\s*", "", regex=True).str.strip()
        tech_taken = tech_taken.dropna(subset=["Course Code"])
        tech_taken["Level"] = tech_taken["Course Code"].str.extract(r"(\d{3})").astype(float)
        
        return tech_taken
        
    except Exception as e:
        st.error(f"Error processing technical electives: {str(e)}")
        with st.expander("Debug Info"):
            if 'tech_df' in locals():
                st.write("Technical electives data sample:", tech_df.head())
            st.write("Student DF columns:", student_df.columns.tolist())
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
        section_titles = student_df.iloc[:, 0].astype(str)

        # SECTION 1: CORE COURSES
        with st.spinner("Analyzing core courses..."):
            # Locate core sections
            core_start = find_section(section_titles, ["Common core"])
            core_end = find_section(section_titles, ["Program core", "Technical core"])
            progcore_end = find_section(section_titles, ["Subtotal program core"])
            
            if None in [core_start, core_end, progcore_end]:
                st.error("❌ Could not locate all core course sections")
            else:
                # Process core courses
                core = student_df.iloc[core_end+1:progcore_end].copy()
                core.columns = student_df.iloc[core_start+1]
                core = core[core["Flag"] == 0]  # Flag=0 means incomplete
                core["Course Code"] = core.iloc[:, 0].astype(str).str.extract(r"([A-Z]{4}\s?\d{3})")[0].str.strip()
                core = core.dropna(subset=["Course Code"])
                core = pd.merge(core, course_df, on="Course Code", how="inner")
                
                st.subheader("📋 Incomplete Core Courses")
                if core.empty:
                    st.success("✅ All core courses completed")
                else:
                    st.dataframe(core[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions", "Term"]]
                                 .style.highlight_null("red")
                                 .set_properties(**{'text-align': 'left'}))

        # SECTION 2: COMPLEMENTARY STUDIES
        with st.spinner("Checking complementary studies..."):
            comp_start = find_section(section_titles, ["Complementary studies"])
            comp_end = find_section(section_titles, ["Subtotal complementary"])
            
            if None in [comp_start, comp_end]:
                st.error("❌ Could not locate complementary studies section")
            else:
                comp = student_df.iloc[comp_start+2:comp_end, [0, 1]].copy()
                comp.columns = ["Course", "Flag"]
                comp["Flag"] = pd.to_numeric(comp["Flag"], errors="coerce").fillna(0).astype(int)
                comp_taken = comp[comp["Flag"] == 1]
                
                st.subheader("🧾 Complementary Studies")
                cols = st.columns(2)
                cols[0].metric("Completed", len(comp_taken))
                cols[1].metric("Still Required", max(0, 3 - len(comp_taken)))
                
                if not comp_taken.empty:
                    with st.expander("View taken courses"):
                        st.dataframe(comp_taken.reset_index(drop=True))

        # SECTION 3: TECHNICAL ELECTIVES
        with st.spinner("Analyzing technical electives..."):
            tech_taken = process_technical_electives(student_df)
            
            if tech_taken is not None:
                total_taken = len(tech_taken)
                taken_400 = (tech_taken["Level"] >= 400).sum()
                taken_under_400 = total_taken - taken_400
                
                # Calculate remaining 400+ level requirements
                remaining_400 = max(0, 5 - taken_400)
                
                st.subheader("🛠 Technical Electives")
                
                # Display metrics
                cols = st.columns(3)
                cols[0].metric("Total Taken", total_taken)
                cols[1].metric("400+ Level", taken_400)
                cols[2].metric("400+ Needed", remaining_400)
                
                if not tech_taken.empty:
                    with st.expander("View taken electives"):
                        st.dataframe(tech_taken[["Course Code", "Course Name", "Level"]]
                                   .sort_values("Level", ascending=False)
                                   .reset_index(drop=True))
                else:
                    st.warning("No technical electives marked as completed (Flag = 1)")
                
                # Additional guidance if needed
                if remaining_400 > 0:
                    st.warning(f"You need {remaining_400} more 400+ level technical electives")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        with st.expander("Technical details"):
            st.exception(e)

if __name__ == "__main__":
    main()
