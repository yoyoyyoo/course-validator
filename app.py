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

def dedup_columns(cols):
    seen = {}
    result = []
    for col in cols:
        if col not in seen:
            seen[col] = 1
            result.append(col)
        else:
            count = seen[col]
            new_col = f"{col}.{count}"
            while new_col in seen:
                count += 1
                new_col = f"{col}.{count}"
            seen[col] += 1
            seen[new_col] = 1
            result.append(new_col)
    return result

# Program Summary - SAFE dynamic version
def process_program_summary(student_df, section_titles):
    summary_start_idx = find_section(section_titles, ["Program summary"])
    if summary_start_idx is None:
        st.info("ℹ️ Program summary not found in the uploaded file.")
        return

    # Dynamically detect the end of summary: next blank line or next big section
    df_rest = student_df.iloc[summary_start_idx:, :].copy()
    df_rest.reset_index(drop=True, inplace=True)

    # Look for where the "Section" column becomes NaN or empty for 2 consecutive rows (safe stop)
    stop_idx = None
    for i in range(2, len(df_rest)):
        row_values = df_rest.iloc[i, :].fillna("").astype(str).str.strip()
        if row_values[0] == "" and row_values[1] == "":
            stop_idx = i
            break

    if stop_idx is None:
        stop_idx = len(df_rest)

    summary_df = df_rest.iloc[:stop_idx].copy()

    # Clean header and data
    new_columns = summary_df.iloc[1].astype(str).tolist()
    new_columns[0] = "Section"
    summary_df.columns = new_columns
    summary_df = summary_df[2:]
    summary_df = summary_df.dropna(how="all")
    summary_df = summary_df.dropna(axis=1, how="all")

    summary_df["Section"] = summary_df["Section"].astype(str).str.strip()
    summary_df["Section"] = summary_df["Section"].str.replace("Requirements for program", "Requirements for total program", regex=False)
    summary_df = summary_df.drop_duplicates(subset="Section")

    summary_df.columns = dedup_columns(summary_df.columns)
    summary_df = summary_df.set_index("Section")

    # Display
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
    st.dataframe(
        summary_df.style
            .apply(style_program_summary, axis=1)
            .format(precision=2),
        use_container_width=True
    )
