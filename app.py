        # FULL HTML EXPORT — WITH FIXED COMPLEMENTARY NOTES
        with st.spinner("Preparing full HTML export..."):
            html_parts = []
            html_parts.append(f"<h1>Course Completion Report — {program_type}</h1>")

            # CORE COURSES
            html_parts.append(f"<h2>📋 Incomplete Core Courses ({len(core)})</h2>")
            if core.empty:
                html_parts.append("<p style='color:green;'>✅ All core courses completed</p>")
            else:
                html_parts.append(core_display.to_html(index=True, escape=False))
                if show_ce_note:
                    html_parts.append("<p style='color:orange;'>⚠️ Note: For CMPE 223 and ELEC 376, only one course is required.</p>")

            # COMPLEMENTARY STUDIES
            comp_completed = len(comp_taken)
            comp_required = max(0, 3 - comp_completed)
            html_parts.append("<h2>🧾 Complementary Studies</h2>")
            html_parts.append(f"<p>Completed: {comp_completed} &nbsp;&nbsp; Still Required: {comp_required}</p>")

            if comp_taken.empty:
                html_parts.append("<p style='color:red;'>No complementary studies taken yet.</p>")
            else:
                html_parts.append(comp_taken.to_html(index=False, escape=False))

            # TECHNICAL ELECTIVES
            html_parts.append(f"<h2>🛠 Technical Electives ({program_type} Requirements)</h2>")
            html_parts.append(f"<p>Total Taken: {total_taken} &nbsp;&nbsp; 400+ Level: {taken_400} &nbsp;&nbsp; 400+ Needed: {remaining_400}</p>")

            if tech_taken is not None and not tech_taken.empty:
                html_parts.append(
                    tech_taken[["Course Code", "Course Name", "Level"]]
                    .sort_values("Level", ascending=False)
                    .reset_index(drop=True)
                    .to_html(index=False, escape=False)
                )
            else:
                html_parts.append("<p style='color:red;'>No technical electives marked as completed (Flag = 1).</p>")

            if remaining_400 > 0:
                html_parts.append(f"<p style='color:red;'>You need {remaining_400} more 400+ level technical electives.</p>")

            # PROGRAM SUMMARY
            html_parts.append("<h2>📊 Program Summary</h2>")
            html_parts.append(summary_df.to_html(escape=False))

            # Combine
            full_html = "".join(html_parts)

            st.download_button(
                "📥 Save FULL REPORT as HTML",
                full_html,
                file_name="course_report.html",
                mime="text/html"
            )
