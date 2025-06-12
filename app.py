import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="EE Course Validator", layout="centered")
st.title("📘 Electrical Engineering Course Validator")

# Upload inputs
course_file = st.file_uploader("Upload Course Info (test_courses.xlsx)", type=["xlsx"])
degree_file = st.file_uploader("Upload Student Record (EE_202X.xlsx)", type=["xlsx"])

if course_file and degree_file:
    try:
        # Load course metadata
        course_df = pd.read_excel(course_file)
        course_df.columns = [col.strip() for col in course_df.columns]
        course_df["Course Code"] = course_df["Course Code"].astype(str).str.strip().str.upper()

        # Load degree file
        sheets = pd.read_excel(degree_file, sheet_name=None)
        if "ElecEng" not in sheets:
            st.error("❌ Sheet 'ElecEng' not found.")
            st.stop()
        eleceng = sheets["ElecEng"]

        # Helper: Find row index by keyword
        def find_row(df, keyword):
            for i, v in enumerate(df.iloc[:, 0].astype(str)):
                if keyword.lower() in v.lower():
                    return i
            return None

        # Detect section positions
        comp_start = find_row(eleceng, "Complementary studies electives")
        comp_end = find_row(eleceng, "Subtotal complementary studies")

        # 🧾 Complementary Studies
        if comp_start is not None and comp_end is not None:
            comp_section = eleceng.iloc[comp_start + 1:comp_end].copy()
            comp_section.columns = eleceng.iloc[comp_start + 1].index  # Ensure clean headers
            comp_section = comp_section.rename(columns={comp_section.columns[0]: "Course", comp_section.columns[1]: "Flag"})

            # Normalize and filter
            comp_section["Flag"] = pd.to_numeric(comp_section["Flag"], errors="coerce").fillna(0).astype(int)
            comp_completed = comp_section[(comp_section["Flag"] == 1) & (comp_section["Course"].notna())]

            count_comp = len(comp_completed)
            remaining = max(0, 3 - count_comp)

            st.subheader("🧾 Complementary Studies")
            st.markdown(f"✅ Completed: **{count_comp}**")
            st.markdown(f"❗ Still Required: **{remaining}**")

            if not comp_completed.empty:
                st.markdown("**Courses Taken:**")
                for course in comp_completed["Course"]:
                    st.markdown(f"- {course}")

        else:
            st.warning("⚠️ Complementary studies section not detected properly.")

    except Exception as e:
        st.error(f"❌ Error: {e}")
