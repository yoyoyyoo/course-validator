import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Course Validator", layout="centered")

def find_section(section_titles, possible_names):
    for name in possible_names:
        matches = section_titles.str.contains(name, case=False, na=False)
        if matches.any():
            return matches.idxmax()
    return None

def process_technical_electives(student_df, program_type):
    try:
        section_titles = student_df.iloc[:, 0].astype(str)
        if program_type.lower() in ['ce', 'compeng', 'computer']:
            tech_electives_pattern = r"(Courses Offered by ECE|Courses Offered by Other Departments)"
            section_headers = section_titles[section_titles.str.contains(tech_electives_pattern, case=False)].index
            if len(section_headers) < 2:
                st.warning("⚠️ Could not find both technical elective sections for CE")
                return None
            ece_courses = student_df.iloc[section_headers[0]+1:section_headers[1]-1, :3]
            ece_courses.columns = ["Course", "Flag", "Credit"]
            other_courses = student_df.iloc[section_headers[1]+1:, :3]
            other_courses.columns = ["Course", "Flag", "Credit"]
            tech_df = pd.concat([ece_courses, other_courses])
        elif program_type.lower() in ['ee', 'eleceng', 'electrical']:
            tech_section = find_section(section_titles, ["technical electives", "electives"])
            if tech_section is None:
                st.warning("⚠️ Could not find technical electives section for EE")
                return None
            next_sections = section_titles.str.contains(r"(subtotal|total)", case=False)
            next_section_idx = next_sections[next_sections].index
            next_section_idx = next_section_idx[next_section_idx > tech_section]
            end_idx = next_section_idx[0] if len(next_section_idx) > 0 else len(student_df)
            tech_df = student_df.iloc[tech_section+1:end_idx, :3]
            tech_df.columns = ["Course", "Flag", "Credit"]
        else:
            st.error(f"Unknown program type: {program_type}")
            return None
        tech_df["Flag"] = pd.to_numeric(tech_df["Flag"], errors="coerce").fillna(0).astype(int)
        tech_taken = tech_df[tech_df["Flag"] == 1].copy()
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
    course_file = st.file_uploader("Course Info (test_courses.xlsx)", type=["xlsx"])
    student_file = st.file_uploader("Student Progress (EE/CE)", type=["xlsx"])
    if not course_file or not student_file:
        st.info("ℹ️ Please upload both files to begin validation")
        return
    try:
        with st.spinner("Loading files..."):
            course_df = pd.read_excel(course_file)
            student_sheets = pd.read_excel(student_file, sheet_name=None)
            course_df.columns = [col.strip() for col in course_df.columns]
            course_df["Course Code"] = course_df["Course Code"].str.strip().str.upper()

        sheet_mapping = {
            'eleceng': 'EE', 'ee': 'EE', 'electrical': 'EE',
            'compeng': 'CE', 'ce': 'CE', 'computer': 'CE'
        }
        sheet_name = next((name for name in student_sheets.keys() if name.strip().lower() in sheet_mapping.keys()), None)
        if not sheet_name:
            st.error(f"❌ Couldn't find expected sheet. Available sheets: {list(student_sheets.keys())}")
            return
        program_type = sheet_mapping[sheet_name.strip().lower()]
        student_df = student_sheets[sheet_name]
        section_titles = student_df.iloc[:, 0].astype(str)

        with st.spinner("Analyzing core courses..."):
            core_start = find_section(section_titles, ["Common core"])
            core_end = find_section(section_titles, ["Program core", "Technical core"])
            progcore_end = find_section(section_titles, ["Subtotal program core"])
            if None in [core_start, core_end, progcore_end]:
                st.error("❌ Could not locate all core course sections")
            else:
                common_core = student_df.iloc[core_start + 2:core_end].copy()
                program_core = student_df.iloc[core_end + 1:progcore_end].copy()
                column_headers = student_df.iloc[core_start + 1].copy()
                column_headers.iloc[0] = "Course"
                common_core.columns = column_headers
                program_core.columns = column_headers

                core_df_all = pd.concat([common_core, program_core], ignore_index=True)
                core_df_all["Flag"] = pd.to_numeric(core_df_all["Flag"], errors="coerce").fillna(0).astype(int)
                core = core_df_all[core_df_all["Flag"] == 0]

                show_ce_note = False
                if program_type == "CE":
                    elective_options = ["CMPE 223", "ELEC 376"]
                    completed_codes = core_df_all[core_df_all["Flag"] == 1]["Course"].astype(str)
                    completed_elective = any(any(opt in course for opt in elective_options) for course in completed_codes)
                    if completed_elective:
                        core = core[~core["Course"].astype(str).str.contains("CMPE 223|ELEC 376")]
                    else:
                        show_ce_note = True

                core["Course Code"] = core["Course"].astype(str).str.extract(r"([A-Z]{4}\s?\d{3})")[0].str.strip()
                core = core.dropna(subset=["Course Code"])
                core = pd.merge(core, course_df, on="Course Code", how="inner")

                st.subheader(f"📋 Incomplete Core Courses ({len(core)})")
                if core.empty:
                    st.success("✅ All core courses completed")
                else:
                    core_display = core[["Course Code", "Name", "Prerequisite", "Corequisite", "Exclusions", "Term"]].reset_index(drop=True)
                    core_display.index += 1
                    st.dataframe(core_display.style.set_properties(**{'text-align': 'left'}))
                    if show_ce_note:
                        st.warning("⚠️ Note: For CMPE 223 and ELEC 376, only one course is required.")

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

        with st.spinner("Analyzing technical electives..."):
            tech_taken = process_technical_electives(student_df, program_type)
            if tech_taken is not None:
                required_400 = 5
                total_taken = len(tech_taken)
                taken_400 = (tech_taken["Level"] >= 400).sum()
                remaining_400 = max(0, required_400 - taken_400)
                st.subheader(f"🛠 Technical Electives ({program_type} Requirements)")
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
                if remaining_400 > 0:
                    st.warning(f"You need {remaining_400} more 400+ level technical electives")

        with st.spinner("Loading program summary..."):
            summary_start = section_titles.str.contains("Program summary", case=False, na=False)
            if summary_start.any():
                start_row = summary_start.idxmax()
                summary_df = student_df.iloc[start_row:start_row + 15].copy()
                summary_df.reset_index(drop=True, inplace=True)

                new_columns = summary_df.iloc[1].astype(str).tolist()
                new_columns[0] = "Section"
                summary_df.columns = new_columns
                summary_df = summary_df[2:]
                summary_df = summary_df.dropna(how="all")
                summary_df = summary_df.dropna(axis=1, how="all")

                summary_df["Section"] = summary_df["Section"].astype(str).str.strip()
                summary_df = summary_df.set_index("Section")
                st.dataframe(
                    summary_df.style
                    .apply(style_program_summary, axis=1)
                    .format(precision=2),  # 保留两位小数但不转字符串
                    use_container_width=True
                )


                def style_program_summary(row):
                    styles = []
                    row_name = row.name.strip().lower()
                    for val in row:
                        style = ""
                        if row_name == "difference" and pd.notna(val) and isinstance(val, (int, float)) and float(val) < 0:
                            style += "background-color: red; color: white"
                        if row_name == "requirements for total program":
                            style += "; color: blue"
                        if row_name == "total for program":
                            style += "; font-weight: bold"
                        styles.append(style)
                    return styles

                st.subheader("📊 Program Summary")
                st.dataframe(summary_df.style.apply(style_program_summary, axis=1), use_container_width=True)
            else:
                st.info("ℹ️ Program summary not found in the uploaded file.")
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        with st.expander("Technical details"):
            st.exception(e)

if __name__ == "__main__":
    main()
