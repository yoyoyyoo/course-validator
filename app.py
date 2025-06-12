import streamlit as st
import pandas as pd

st.set_page_config(page_title="EE Course Validator", layout="centered")
st.title("📘 Electrical Engineering Course Validator")

# Upload input files
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload Student Record (EE_2026.xlsx)", type=["xlsx"])

if course_file and degree_file:
    try:
        # Load course info
        course_df = pd.read_excel(course_file)

        # Normalize headers
        course_df.columns = [col.strip() for col in course_df.columns]
        # Rename "Course" to "Course Code" if needed
        if "Course" in course_df.columns:
            course_df.rename(columns={"Course": "Course Code"}, inplace=True)

        # Confirm Course Code column exists
        if "Course Code" not in course_df.columns:
            st.error("❌ 'Course Code' column not found in uploaded course info.")
            st.stop()

        # Clean Course Code values
        course_df["Course Code"] = course_df["Course Code"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip().str.upper()

        # Load degree plan
        sheets = pd.read_excel(degree_file, sheet_name=None)
        if "ElecEng" not in sheets:
            st.error("❌ 'ElecEng' sheet not found in uploaded student file.")
            st.stop()

        eleceng = sheets["ElecEng"]

        # 🟦 Core Courses: Rows 19–63
        core = eleceng.iloc[18:63].copy()
        core["Course Raw"] = core.iloc[:, 0].astype(str)
        core["Flag"] = pd.to_numeric(core["Flag"], errors="coerce")
        core["Course Code"] = (
            core["Course Raw"]
            .str.extract(r'^([A-Z]+\s*\d+)', expand=False)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .str.upper()
        )

        core_missing = core[core["Flag"] == 0]
        core_result = pd.merge(core_missing, course_df, on="Course Code", how="left")

        st.subheader("📋 Missing Required Core Courses")
        if not core_result.empty:
            st.dataframe(core_result[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions"]])
        else:
            st.success("✅ All core courses are completed.")

        # 🟦 Complementary Studies: Rows 67–69
        comp = eleceng.iloc[66:69].copy()
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

        # 🟦 Technical Electives: Rows 78–136
        tech = eleceng.iloc[77:136].copy()
        tech["Course Raw"] = tech.iloc[:, 0].astype(str)
        tech["Flag"] = pd.to_numeric(tech["Flag"], errors="coerce")
        tech["Course Code"] = (
            tech["Course Raw"]
            .str.extract(r'^([A-Z]+\s*\d+)', expand=False)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
            .str.upper()
        )

        tech_taken = tech[tech["Flag"] == 1]
        tech_merged = pd.merge(
            tech_taken,
            course_df[["Course Code", "Name", "Type"]],
            on="Course Code",
            how="left"
        )

        # Filter only tech elective A or B
        tech_filtered = tech_merged[tech_merged["Type"].isin(["tech elective A", "tech elective B"])]
        tech_filtered["Level"] = tech_filtered["Course Code"].str.extract(r'(\d{3})').astype(float)

        taken_total = len(tech_filtered)
        taken_400 = (tech_filtered["Level"] >= 400).sum()
        missing_400 = max(0, 5 - taken_400)

        st.subheader("📗 Technical Electives")
        st.markdown(f"- ✅ Taken: **{taken_total}**")
        st.markdown(f"- ✅ 400-level or above: **{taken_400}**")
        st.markdown(f"- ❗ Still need: **{missing_400} more at 400-level** to meet the 5 required")

        if not tech_filtered.empty:
            st.dataframe(tech_filtered[["Course Code", "Name", "Type"]])

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
