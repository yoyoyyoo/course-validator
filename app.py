import streamlit as st
import pandas as pd

st.set_page_config(page_title="EE Course Validator", layout="centered")
st.title("📘 Electrical Engineering Course Validator")

# Upload inputs
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload Student Record (EE_2026.xlsx)", type=["xlsx"])

if course_file and degree_file:
    try:
        # Load files
        course_df = pd.read_excel(course_file)
        degree_sheets = pd.read_excel(degree_file, sheet_name=None)

        if "ElecEng" not in degree_sheets:
            st.error("❌ 'ElecEng' sheet not found in uploaded student record.")
        else:
            eleceng_sheet = degree_sheets["ElecEng"]

            # Normalize course sheet
            course_df.columns = [col.strip().capitalize() for col in course_df.columns]
            course_df["Course Code"] = course_df["Course Code"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip().str.upper()

            ### 🔹 1. CORE COURSES CHECK (Rows 19–63)
            core = eleceng_sheet.iloc[18:63].copy()
            core["Course Code"] = core.iloc[:, 0].astype(str).str.extract(r'^([A-Z]+\s*\d+)', expand=False)
            core["Course Code"] = core["Course Code"].str.replace(r"\s+", " ", regex=True).str.strip().str.upper()
            core["Flag"] = pd.to_numeric(core["Flag"], errors="coerce")
            core_missing = core[core["Flag"] == 0]
            core_result = pd.merge(core_missing, course_df, on="Course Code", how="left")

            st.subheader("📋 Missing Required Core Courses")
            if not core_result.empty:
                st.dataframe(core_result[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions"]])
            else:
                st.success("✅ All core courses are completed.")

            ### 🔹 2. COMPLEMENTARY STUDIES CHECK (Rows 67–69)
            comp = eleceng_sheet.iloc[66:69].copy()
            comp["Course Code"] = comp.iloc[:, 0].astype(str).str.extract(r'^([A-Z]+\s*\d+)', expand=False)
            comp["Course Code"] = comp["Course Code"].str.replace(r"\s+", " ", regex=True).str.strip().str.upper()
            comp["Flag"] = pd.to_numeric(comp["Flag"], errors="coerce")
            comp_taken = comp[comp["Flag"] == 1]

            st.subheader("🧾 Complementary Studies")
            st.markdown(f"- ✅ Completed: **{len(comp_taken)}**")
            st.markdown(f"- ❗ Still need: **{max(0, 3 - len(comp_taken))} more**")

            if not comp_taken.empty:
                names = comp_taken.iloc[:, 0].astype(str).str[10:].tolist()
                st.markdown("**Courses Taken:**")
                for name in names:
                    st.markdown(f"• {name}")

            ### 🔹 3. TECHNICAL ELECTIVES (Rows 78–136)
            tech = eleceng_sheet.iloc[77:136].copy()
            tech["Course Code"] = tech.iloc[:, 0].astype(str).str.extract(r'^([A-Z]+\s*\d+)', expand=False)
            tech["Course Code"] = tech["Course Code"].str.replace(r"\s+", " ", regex=True).str.strip().str.upper()
            tech["Flag"] = pd.to_numeric(tech["Flag"], errors="coerce")
            tech_taken = tech[tech["Flag"] == 1]

            # Merge with course type info to confirm it's A or B
            tech_info = pd.merge(tech_taken, course_df[["Course Code", "Name", "Type"]], on="Course Code", how="left")
            tech_info = tech_info[tech_info["Type"].isin(["tech elective A", "tech elective B"])]
            tech_info["Level"] = tech_info["Course Code"].str.extract(r'(\d{3})').astype(float)

            taken_total = len(tech_info)
            taken_400 = (tech_info["Level"] >= 400).sum()
            missing_400 = max(0, 5 - taken_400)

            st.subheader("📗 Technical Electives")
            st.markdown(f"- ✅ Taken: **{taken_total}**")
            st.markdown(f"- ✅ 400-level or above: **{taken_400}**")
            st.markdown(f"- ❗ Still need **{missing_400} more at 400-level** to meet minimum of 5")

            if not tech_info.empty:
                st.dataframe(tech_info[["Course Code", "Name", "Type"]])

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
