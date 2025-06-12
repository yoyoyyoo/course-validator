import streamlit as st
import pandas as pd

st.title("📘 EE Course Completion Validator")

# Upload files
course_file = st.file_uploader("Upload Course Info Excel (.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload EE_2026 Excel File (.xlsx)", type=["xlsx"])

if course_file and degree_file:
    try:
        # Load both files
        course_df = pd.read_excel(course_file)
        degree_df = pd.read_excel(degree_file, sheet_name=None)

        # Check and load ElecEng sheet
        if "ElecEng" not in degree_df:
            st.error("❌ 'ElecEng' sheet not found. Sheets available: " + ", ".join(degree_df.keys()))
        else:
            eleceng_sheet_raw = degree_df["ElecEng"]

            # Extract headers from row 36 (index 35)
            headers = eleceng_sheet_raw.iloc[35].fillna("").astype(str).tolist()
            eleceng_sheet = eleceng_sheet_raw.iloc[36:].copy()
            eleceng_sheet.columns = headers
            eleceng_sheet = eleceng_sheet.reset_index(drop=True)

            # Normalize course_df headers and Course Code format
            course_df.columns = [col.strip() for col in course_df.columns]
            course_code_col = next((c for c in course_df.columns if c.lower() in ["course code", "course"]), None)
            if not course_code_col:
                st.error("❌ No 'Course Code' column found in course info.")
            else:
                course_df = course_df.rename(columns={course_code_col: "Course Code"})
                course_df["Course Code"] = course_df["Course Code"].astype(str).str.replace(r"\s+", "", regex=True).str.upper()

                # === 1. Required Core (Rows 19–62)
                core_check = eleceng_sheet_raw.iloc[18:62]
                core_missing = core_check[core_check["Unnamed: 13"] == 0].copy()
                core_missing["Course Code"] = core_missing.iloc[:, 0].astype(str).str.replace(r"\s+", "", regex=True).str.upper()

                core_df = pd.merge(core_missing[["Course Code"]], course_df, on="Course Code", how="left")

                st.subheader("📋 Missing Required Core Courses")
                st.dataframe(core_df[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions"]])

                # === 2. Complementary Studies (Rows 67–69)
                comp_check = eleceng_sheet.iloc[30:33]  # Relative to row 36
                comp_taken = comp_check[comp_check["Flag"] == 1].iloc[:, 0].dropna().tolist()
                comp_needed = max(0, 3 - len(comp_taken))

                st.subheader("📘 Complementary Studies")
                st.write(f"- ✅ Completed: {len(comp_taken)}")
                st.write(f"- ❗ Still need: {comp_needed} more")
                if comp_taken:
                    st.markdown("**Courses Taken:**")
                    st.write(comp_taken)

                # === 3. Technical Electives (Rows 78–136)
                tech_check = eleceng_sheet.iloc[42:101]  # Relative to row 36
                tech_taken = tech_check[tech_check["Flag"] == 1].copy()
                tech_taken["Course Code"] = tech_taken.iloc[:, 0].astype(str).str.replace(r"\s+", "", regex=True).str.upper()

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

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
