import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="EE Course Validator", layout="centered")
st.title("📘 Electrical Engineering Course Validator")

def extract_course_code(cell_value):
    """Extract course code from formula or plain text"""
    if pd.isna(cell_value):
        return None
    
    # Handle Excel formula case (='Course Units'!A8)
    if isinstance(cell_value, str) and cell_value.startswith("='"):
        match = re.search(r"'!A\d+", cell_value)
        if match:
            # Get the row number and look up in Course Units sheet
            row_num = int(match.group(0)[3:])
            if 'Course Units' in degree_sheets:
                return degree_sheets['Course Units'].iloc[row_num-1, 0]
    
    # Handle plain text case (ELEC 221)
    match = re.match(r'([A-Z]+\s*\d+[A-Z]*)', str(cell_value).strip())
    return match.group(0) if match else None

# Upload inputs
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload Student Record (EE_2026.xlsx)", type=["xlsx"])

if course_file and degree_file:
    try:
        # Load course metadata
        course_df = pd.read_excel(course_file, sheet_name="Sheet1")
        
        # Clean course data
        course_df.columns = [col.strip() for col in course_df.columns]
        course_df["Course Code"] = course_df["Course Code"].str.strip().str.upper()
        
        # Load EE degree file
        degree_sheets = pd.read_excel(degree_file, sheet_name=None)
        
        if "ElecEng" not in degree_sheets:
            st.error("❌ 'ElecEng' sheet not found.")
            st.stop()
            
        eleceng = degree_sheets["ElecEng"]
        
        # Process Core Courses (Rows 19-63)
        core = eleceng.iloc[18:63].copy()
        core["Course Code"] = core.iloc[:, 0].apply(extract_course_code)
        core["Flag"] = pd.to_numeric(core.iloc[:, 1], errors="coerce").fillna(0)
        
        core_missing = core[core["Flag"] == 0]
        core_merged = pd.merge(
            core_missing, 
            course_df, 
            on="Course Code", 
            how="left"
        ).dropna(subset=["Course Code"])

        st.subheader("📋 Missing Required Core Courses")
        if not core_merged.empty:
            st.dataframe(core_merged[["Course Code", "Name", "Type","Prerequisite", "Corequisite", "Exclusions"]])
        else:
            st.success("✅ All core courses are completed.")

        # Process Complementary Studies (Rows 67-69)
        comp = eleceng.iloc[66:69].copy()
        comp["Flag"] = pd.to_numeric(comp.iloc[:, 1], errors="coerce").fillna(0)
        comp_taken = comp[comp["Flag"] == 1]
        
        st.subheader("🧾 Complementary Studies")
        st.markdown(f"- ✅ Completed: **{len(comp_taken)}**")
        st.markdown(f"- ❗ Still need: **{max(0, 3 - len(comp_taken))} more**")
        
        if not comp_taken.empty:
            st.markdown("**Courses Taken:**")
            for _, row in comp_taken.iterrows():
                course_name = str(row.iloc[0]).split(")")[-1].strip()
                if course_name:
                    st.markdown(f"• {course_name}")

        # Process Technical Electives (Rows 78-135)
        tech = eleceng.iloc[76:136].copy()  # Rows 78-136 in Excel (0-based 77-135)
        tech["Course Code"] = tech.iloc[:, 0].apply(extract_course_code)
        tech["Flag"] = pd.to_numeric(tech.iloc[:, 1], errors="coerce").fillna(0)
        
        # Get all taken courses (Flag = 1)
        tech_taken = tech[tech["Flag"] == 1].dropna(subset=["Course Code"])
        
        # Merge with course info
        tech_merged = pd.merge(
            tech_taken,
            course_df,
            on="Course Code",
            how="left"
        )
        
        # Count all technical electives (both A and B)
        all_tech_electives = tech_merged[
            tech_merged["Type"].str.contains("tech elective", case=False, na=False)
        ]
        
        # Extract course level
        all_tech_electives["Level"] = all_tech_electives["Course Code"].str.extract(r'(\d{3})')[0].astype(float)
        
        # Count List A electives
        list_a_electives = all_tech_electives[
            all_tech_electives["Type"].str.contains("tech elective A", case=False, na=False)
        ]
        
        count_taken = len(all_tech_electives)
        count_400 = (all_tech_electives["Level"] >= 400).sum()
        count_list_a = len(list_a_electives)
        
        missing_400 = max(0, 5 - count_400)
        missing_list_a = max(0, 5 - count_list_a)

        st.subheader("📗 Technical Electives")
        st.markdown(f"- ✅ Total Taken: **{count_taken}**")
        st.markdown(f"- ✅ 400-level or above: **{count_400}** (need 5)")
        st.markdown(f"- ✅ List A Electives: **{count_list_a}** (need 5)")
        
        if missing_400 > 0:
            st.markdown(f"- ❗ Still need: **{missing_400} more at 400-level**")
        if missing_list_a > 0:
            st.markdown(f"- ❗ Still need: **{missing_list_a} more from List A**")

        if not all_tech_electives.empty:
            st.dataframe(all_tech_electives[["Course Code", "Name", "Type", "Credits", "Level"]])

    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")
        st.error("Please ensure:")
        st.error("1. Files are in the correct format")
        st.error("2. Course codes match between files")
        st.error("3. No empty or malformed cells in critical columns")
