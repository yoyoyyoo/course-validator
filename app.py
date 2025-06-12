import streamlit as st
import pandas as pd

st.title("📘 EE Course Completion Validator")

course_file = st.file_uploader("Upload Course Info Excel (.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload EE_2026 Excel File", type=["xlsx"])

if course_file and degree_file:
    course_df = pd.read_excel(course_file)
    degree_df = pd.read_excel(degree_file, sheet_name=None)
    eleceng_sheet = degree_df["ElecEng"]

    # === Core (rows 19–62)
    core_check = eleceng_sheet.iloc[18:62]
    core_missing = core_check[core_check["Unnamed: 13"] == 0].copy()
    core_missing["Course Code"] = core_missing.iloc[:, 0]
    core_missing = core_missing[["Course Code"]]
    course_df.columns = [col.strip().capitalize() for col in course_df.columns]
    core_df = pd.merge(core_missing, course_df, on="Course Code", how="left")
    st.subheader("📋 Missing Required Core Courses")
    st.dataframe(core_df[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions"]])

    # === Complementary (rows 67–69)
    comp_check = eleceng_sheet.iloc[66:69]
    comp_taken = comp_check[comp_check["Unnamed: 13"] == 1].iloc[:, 0].dropna().tolist()
    comp_needed = max(0, 3 - len(comp_taken))
    st.subheader("📘 Complementary Studies")
    st.write(f"- ✅ Completed: {len(comp_taken)}")
    st.write(f"- ❗ Still need: {comp_needed} more")
    if comp_taken:
        st.markdown("**Courses Taken:**")
        st.write(comp_taken)

    # === Technical Electives (rows 78–136)
    tech_check = eleceng_sheet.iloc[77:136]
    tech_taken = tech_check[tech_check["Unnamed: 13"] == 1].copy()
    tech_taken["Course Code"] = tech_taken.iloc[:, 0]
    tech_merged = pd.merge(tech_taken, course_df, on="Course Code", how="left")
    tech_merged = tech_merged[tech_merged["Type"].isin(["tech elective A", "tech elective B"])]
    tech_merged["Level"] = tech_merged["Course Code"].str.extract(r'(\d{3})').astype(float)
    tech_count = len(tech_merged)
    tech_400_count = (tech_merged["Level"] >= 400).sum()
    missing_400 = max(0, 5 - tech_400_count)

    st.subheader("📗 Technical Electives")
    st.write(f"- ✅ Taken: {tech_count}")
    st.write(f"- ✅ 400-level or above: {tech_400_count}")
    st.write(f"- ❗ Still need {missing_400} more at 400-level to meet minimum of 5")
    if tech_count > 0:
        st.markdown("**Courses Taken:**")
        st.dataframe(tech_merged[["Course Code", "Name", "Type"]])
