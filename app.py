import streamlit as st
import pandas as pd

st.title("📘 EE Course Completion Validator")

# Upload files
course_file = st.file_uploader("Upload Course Info Excel (.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload EE_2026 Excel File (.xlsx)", type=["xlsx"])

if course_file and degree_file:
    try:
        # Load course info and EE plan
        course_df = pd.read_excel(course_file)
        degree_df = pd.read_excel(degree_file, sheet_name=None)

        if "ElecEng" not in degree_df:
            st.error("❌ 'ElecEng' sheet not found. Sheets available: " + ", ".join(degree_df.keys()))
        else:
            eleceng_raw = degree_df["ElecEng"]

            # Use row 36 as header
            headers = eleceng_raw.iloc[35].fillna("").astype(str).tolist()
            eleceng = eleceng_raw.iloc[36:].copy()
            eleceng.columns = headers
            eleceng = eleceng.reset_index(drop=True)

            # Extract and clean Course Code and Name
            eleceng["Course Raw"] = eleceng.iloc[:, 0].astype(str)
            eleceng["Course Code"] = (
                eleceng["Course Raw"]
                .str.extract(r'^([A-Z]+\s*\d+)', expand=False)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
                .str.upper()
            )
            eleceng["Course Name"] = eleceng["Course Raw"].str[9:].str.strip()

            # Clean course_df
            course_df.columns = [col.strip() for col in course_df.columns]
            course_df = course_df.rename(columns={col: "Course Code" for col in course_df.columns if col.lower() in ["course", "course code"]})
            course_df["Course Code"] = (
                course_df["Course Code"]
                .astype(str)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
                .str.upper()
            )

            # === 1. Missing Core Courses (Rows 19-63) ===
            core_rows = eleceng.iloc[18:63].copy()
            core_rows["Flag"] = pd.to_numeric(core_rows["Flag"], errors="coerce")
            core_missing = core_rows[core_rows["Flag"] == 0].copy()

            core_merged = pd.merge(core_missing, course_df, on="Course Code", how="left")

            st.subheader("📋 Missing Required Core Courses")
            st.dataframe(core_merged[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions"]])

            # === 2. Complementary Studies (Rows 67–69) ===
            comp_rows = eleceng.iloc[66:69]  # Rows 67-69
            comp_rows["Flag"] = pd.to_numeric(comp_rows["Flag"], errors="coerce")
            comp_taken = comp_rows[comp_rows["Flag"] == 1]
            comp_needed = max(0, 3 - len(comp_taken))

            st.subheader("📘 Complementary Studies")
            st.write(f"- ✅ Completed: {len(comp_taken)}")
            st.write(f"- ❗ Still need: {comp_needed} more")
            if len(comp_taken) > 0:
                st.markdown("**Courses Taken:**")
                st.write(comp_taken["Course Raw"].tolist())

            # === 3. Technical Electives (Rows 78–136) ===
            tech_rows = eleceng.iloc[77:136].copy()
            tech_rows["Flag"] = pd.to_numeric(tech_rows["Flag"], errors="coerce")
            tech_taken = tech_rows[tech_rows["Flag"] == 1].copy()

            tech_taken["Course Code"] = tech_taken["Course Code"].astype(str)
            tech_merged = pd.merge(tech_taken, course_df, on="Course Code", how="left")
            tech_merged["Level"] = tech_merged["Course Code"].str.extract(r'(\d{3})').astype(float)

            if "Type" in tech_merged.columns:
                tech_merged = tech_merged[tech_merged["Type"].isin(["tech elective A", "tech elective B"])]

            total_taken = len(tech_merged)
            taken_400 = (tech_merged["Level"] >= 400).sum()
            missing_400 = max(0, 5 - taken_400)

            st.subheader("📗 Technical Electives")
            st.write(f"- ✅ Taken: {total_taken}")
            st.write(f"- ✅ 400-level or above: {taken_400}")
            st.write(f"- ❗ Still need {missing_400} more at 400-level to meet minimum of 5")
            if total_taken > 0:
                st.markdown("**Courses Taken:**")
                st.dataframe(tech_merged[["Course Code", "Name", "Type"]])

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
