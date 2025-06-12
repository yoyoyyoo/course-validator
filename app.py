import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="EE Course Validator", layout="centered")
st.title("📘 Electrical Engineering Course Validator")

def extract_course_code(cell):
    if pd.isna(cell):
        return None
    match = re.search(r'([A-Z]{4})\s*([0-9]{3})', str(cell).upper())
    return f"{match.group(1)} {match.group(2)}" if match else None

# Upload files
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload Student Record (EE_2026.xlsx)", type=["xlsx"])

if course_file and degree_file:
    try:
        # Load course metadata
        course_df = pd.read_excel(course_file)
        course_df.columns = [col.strip() for col in course_df.columns]
        course_df["Course Code"] = course_df["Course Code"].str.strip().str.upper()

        # Load degree plan
        degree_sheets = pd.read_excel(degree_file, sheet_name=None)
        if "ElecEng" not in degree_sheets:
            st.error("❌ 'ElecEng' sheet not found.")
            st.stop()
        eleceng = degree_sheets["ElecEng"]

        # 1️⃣ Required Core Courses (Rows 19–63)
        core = eleceng.iloc[18:63].copy()
        core["Course Code"] = core.iloc[:, 0].apply(extract_course_code)
        core["Flag"] = pd.to_numeric(core.iloc[:, 1], errors="coerce").fillna(0).astype(int)
        core_missing = core[(core["Flag"] == 0) & core["Course Code"].notna()]
        core_merged = pd.merge(core_missing, course_df, on="Course Code", how="left")

        st.subheader("📋 Missing Required Core Courses")
        if not core_merged.empty:
            st.dataframe(core_merged[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions"]])
        else:
            st.success("✅ All core courses are completed.")

        # 2️⃣ Complementary Studies (Rows 67–69)
        comp = eleceng.iloc[66:69].copy()
        comp["Flag"] = pd.to_numeric(comp.iloc[:, 1], errors="coerce").fillna(0).astype(int)
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

        # 3️⃣ Technical Electives (Rows 76–135, inclusive of ELEC 270)
        tech = eleceng.iloc[76:136].copy()
        tech["Course Code"] = tech.iloc[:, 0].apply(extract_course_code)
        tech["Flag"] = pd.to_numeric(tech.iloc[:, 1], errors="coerce").fillna(0).astype(int)

        tech_taken = tech[(tech["Flag"] == 1) & tech["Course Code"].notna()]
        tech_merged = pd.merge(
            tech_taken,
            course_df[["Course Code", "Name", "Type"]],
            on="Course Code",
            how="left"
        )

        tech_merged["Level"] = tech_merged["Course Code"].str.extract(r'(\d{3})')[0].astype(float)
        total_taken = len(tech_merged)
        taken_400 = (tech_merged["Level"] >= 400).sum()
        missing_400 = max(0, 5 - taken_400)

        st.subheader("📗 Technical Electives")
        st.markdown(f"- ✅ Taken: **{total_taken}**")
        st.markdown(f"- ✅ 400-level or above: **{taken_400}**")
        st.markdown(f"- ❗ Still need: **{missing_400} more at 400-level** to meet the 5 required")
        if not tech_merged.empty:
            st.dataframe(tech_merged[["Course Code", "Name", "Level"]])

    except Exception as e:
        st.error(f"❌ Error processing files: {str(e)}")
        st.error("📌 Please ensure:")
        st.error("1. Files are correct and contain expected sheets.")
        st.error("2. Course Code column exists and matches.")
