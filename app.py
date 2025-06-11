import streamlit as st
import pandas as pd

st.title("🛠️ Debug Header Row")

degree_file = st.file_uploader("Upload Degree Plan Excel", type=["xlsx"])
if degree_file:
    df = pd.read_excel(degree_file, sheet_name=None)
    if 'ElecEng' in df:
        eleceng = df['ElecEng']
        st.subheader("Rows 30–45 (Raw Data):")
        for i in range(30, 46):
            row = eleceng.iloc[i].fillna("").astype(str).tolist()
            st.write(f"Row {i}: {row}")
    else:
        st.error("No 'ElecEng' sheet found.")
