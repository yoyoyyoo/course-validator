import streamlit as st
import pandas as pd

# Load the data
@st.cache_data
def load_data():
    # Load test_courses.xlsx
    test_courses = pd.read_excel('test_courses.xlsx', sheet_name='Sheet1')
    
    # Load EE_2026.xlsx
    ee_2026 = pd.read_excel('EE_2026.xlsx', sheet_name='ElecEng')
    
    # Load Course Units sheet from EE_2026.xlsx for course names
    course_units = pd.read_excel('EE_2026.xlsx', sheet_name='Course Units')
    
    return test_courses, ee_2026, course_units

test_courses, ee_2026, course_units = load_data()

# Clean and prepare the data
def prepare_data(test_courses, ee_2026, course_units):
    # Clean test_courses
    test_courses = test_courses.dropna(how='all')
    test_courses.columns = test_courses.iloc[0]
    test_courses = test_courses[1:]
    
    # Clean ee_2026
    ee_2026 = ee_2026.dropna(how='all')
    
    # Extract course names from course_units
    course_names = {}
    for _, row in course_units.iterrows():
        if pd.notna(row['A']) and pd.notna(row['B']):
            course_code = str(row['A']).strip()
            course_name = str(row['B']).strip()
            course_names[course_code] = course_name
    
    return test_courses, ee_2026, course_names

test_courses, ee_2026, course_names = prepare_data(test_courses, ee_2026, course_units)

# Streamlit app
st.title('Electrical Engineering Course Validation Tool')

# 1. Missing Core Courses
st.header('1. Missing Core Courses')

# Get core courses from EE_2026 (rows 19-62 where Flag == 0)
core_courses = ee_2026.iloc[18:62]  # Rows 19-62 (0-indexed)
missing_core = core_courses[core_courses['B'] == 0]

# Merge with test_courses to get details
missing_core_details = []
for _, row in missing_core.iterrows():
    course_code = str(row['A']).split('!A')[1] if '!A' in str(row['A']) else str(row['A'])
    course_code = course_code.strip("='")
    
    # Find course in test_courses
    course_info = test_courses[test_courses['Course Code'] == course_code]
    if not course_info.empty:
        course_info = course_info.iloc[0]
        missing_core_details.append({
            'Course Code': course_code,
            'Name': course_info['Name'],
            'Prerequisite': course_info['Prerequisite'],
            'Corequisite': course_info['Corequisite'],
            'Exclusions': course_info['Exclusions']
        })

if missing_core_details:
    st.write(f"Number of missing core courses: {len(missing_core_details)}")
    st.dataframe(pd.DataFrame(missing_core_details))
else:
    st.success("All core courses are completed!")

# 2. Complementary Studies
st.header('2. Complementary Studies')

# Get complementary studies from EE_2026 (rows 67-69 where Flag == 1)
comp_studies = ee_2026.iloc[66:69]  # Rows 67-69
completed_comp = comp_studies[comp_studies['B'] == 1]

completed_count = len(completed_comp)
needed_count = max(0, 3 - completed_count)

st.write(f"Completed: {completed_count}/3")
st.write(f"Still needed: {needed_count}")

if completed_count > 0:
    st.write("Courses taken:")
    for _, row in completed_comp.iterrows():
        course_desc = str(row['A']).strip("(fill in course number/name/credit)")
        st.write(f"- {course_desc}")

# 3. Technical Electives
st.header('3. Technical Electives')

# Get technical electives from EE_2026 (rows 78-136 where Flag == 1)
tech_electives = ee_2026.iloc[77:136]  # Rows 78-136
completed_tech = tech_electives[tech_electives['B'] == 1]

# Filter only tech elective A or B from test_courses
tech_electives_list = test_courses[
    (test_courses['Type'].str.contains('tech elective A', na=False)) | 
    (test_courses['Type'].str.contains('tech elective B', na=False))
]['Course Code'].unique()

# Get completed tech electives that are in our list
completed_tech_details = []
level_400_count = 0

for _, row in completed_tech.iterrows():
    course_code = str(row['A']).split('!A')[1] if '!A' in str(row['A']) else str(row['A'])
    course_code = course_code.strip("='")
    
    if course_code in tech_electives_list:
        course_info = test_courses[test_courses['Course Code'] == course_code]
        if not course_info.empty:
            course_info = course_info.iloc[0]
            is_400_level = course_code.split()[1][0] == '4'
            
            completed_tech_details.append({
                'Course Code': course_code,
                'Name': course_info['Name'],
                'Type': course_info['Type'],
                '400-level': 'Yes' if is_400_level else 'No'
            })
            
            if is_400_level:
                level_400_count += 1

total_completed = len(completed_tech_details)
missing_400 = max(0, 5 - level_400_count)

st.write(f"Total technical electives taken: {total_completed}")
st.write(f"400-level courses taken: {level_400_count}/5")
st.write(f"400-level courses still needed: {missing_400}")

if completed_tech_details:
    st.write("Completed technical electives:")
    st.dataframe(pd.DataFrame(completed_tech_details))
else:
    st.write("No technical electives completed yet.")
