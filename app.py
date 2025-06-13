# Updated technical electives processing section
with st.spinner("Analyzing technical electives..."):
    # Find all course rows with Flag = 1 in the technical electives sections
    tech_electives_pattern = r"(Courses Offered by ECE|Courses Offered by Other Departments)"
    tech_sections = section_titles[section_titles.str.contains(tech_electives_pattern, case=False)].index
    
    if len(tech_sections) < 2:
        st.warning("⚠️ Could not find both technical elective sections")
    else:
        # Combine both ECE and Other Departments sections
        tech_df = pd.concat([
            student_df.iloc[tech_sections[0]+1:tech_sections[1]-1],
            student_df.iloc[tech_sections[1]+1:]
        ])
        
        # Clean and filter technical electives
        tech_taken = tech_df.copy()
        tech_taken.columns = student_df.iloc[tech_sections[0]-1] if tech_sections[0] > 0 else None
        tech_taken = tech_taken[tech_taken["Flag"] == 1]
        
        # Extract course codes and levels
        tech_taken["Course Code"] = tech_taken.iloc[:, 0].astype(str).str.extract(r"([A-Z]{4}\s?\d{3})")[0].str.strip()
        tech_taken = tech_taken.dropna(subset=["Course Code"])
        tech_taken["Level"] = tech_taken["Course Code"].str.extract(r"(\d{3})").astype(float)
        
        # Calculate metrics
        total_taken = len(tech_taken)
        taken_400 = (tech_taken["Level"] >= 400).sum()
        missing_400 = max(0, 5 - taken_400)
        
        # Display results
        st.subheader("🛠 Technical Electives")
        cols = st.columns(3)
        cols[0].metric("Total Taken", total_taken)
        cols[1].metric("400+ Level", taken_400)
        cols[2].metric("Remaining", max(0, 5 - total_taken))
        
        if not tech_taken.empty:
            with st.expander("View technical electives"):
                st.dataframe(tech_taken[["Course Code", "Credit"]])
        else:
            st.warning("No technical electives found with Flag = 1")
