import streamlit as st
import pandas as pd
from datetime import datetime
import os
from streamlit_gsheets import GSheetsConnection
import matplotlib.pyplot as plt

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# App Setup
st.set_page_config(page_title="Report a Water Source", layout="wide")
st.title("🚰 Report a Water Source")

st.markdown("""
Report information about water sources in your area.
""")

# Google Sheets Setup
SHEET_NAME = "Water-Report"
conn = st.connection("gsheets", type=GSheetsConnection)

# Fetch existing reports data
def load_data():
    data = conn.read(worksheet=SHEET_NAME, ttl=5)
    data = data.dropna(how="all")

    # Convert zipcodes to string early to prevent formatting issues
    if "zipcode" in data.columns:
        data["zipcode"] = data["zipcode"].astype(str).str.strip()

    return data


# Tabs
report_tab, gallery_tab, table_tab, trends_tab, ai_analysis_tab = st.tabs(
    ["📋 Report", "🖼️ Gallery", "📊 Tabular View", "📈 Community Trends", "🤖AI Analysis"]
)

# REPORT TAB
with report_tab:
    st.subheader("📝 Submit a Water Report")
    with st.form("report_form"):
        address = st.text_input("📍 Address")
        zipcode = st.text_input("🏷️ Zipcode")
        description = st.text_area("Description")
        concerns = st.multiselect("Concerns", ["Discoloration", "Foul smell", "Foam on surface", "Bugs or larvae", "Near industrial area", "Trash nearby", "Other"])
        source_type = st.selectbox("Water Source Type", ["Faucet", "River/Stream", "Pipe Leak", "Fountain", "Rainwater Pool", "Other"])
        used = st.radio("Did you use it?", ["Yes", "No"])
        symptoms = st.text_input("Symptoms after use (optional)")

        submitted = st.form_submit_button("Submit Report")
        if submitted:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            report = {
                "timestamp": timestamp,
                "address": address,
                "zipcode": zipcode,
                "description": description,
                "concerns": ", ".join(concerns),
                "type": source_type,
                "used": used,
                "symptoms": symptoms,
            }
            existing_data = load_data()
            updated_data = pd.concat([existing_data, pd.DataFrame([report])], ignore_index=True)
            conn.update(worksheet=SHEET_NAME, data=updated_data)
            st.success("✅ Report submitted successfully!")

# GALLERY TAB
with gallery_tab:
    st.header("🖼️ Report Gallery")
    df = load_data()

    if not df.empty:
        # Ensure the 'zipcode' column is treated as strings
        df['zipcode'] = df['zipcode'].astype(str).str.strip()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        st.subheader("🔎 Filter Logs")
        zipcodes = df['zipcode'].dropna().unique()
        selected_zip = st.selectbox("Filter by ZIP Code (optional):", ["All"] + sorted(zipcodes))

        # Apply ZIP code filter
        if selected_zip != "All":
            df = df[df['zipcode'] == selected_zip]

        # Sort by time
        sort_option = st.radio("Sort by:", ["Newest First", "Oldest First"], horizontal=True)
        df = df.sort_values(by='timestamp', ascending=(sort_option == "Oldest First"))

        # Convert filtered DataFrame to a list of dictionaries
        reports = df.to_dict(orient='records')

        # View selection: Detailed View or Grid View
        view_option = st.radio("Choose view:", ["Detailed View", "Grid View"], horizontal=True)

        # --- Detailed View ---
        if view_option == "Detailed View":
            for report in reports:
                with st.expander(f"📍 {report['address']} ({report['timestamp']})"):
                    st.write(f"**Source Type:** {report['type']} | **Used:** {report['used']}")
                    if report["concerns"]:
                        st.write(f"**Concerns:** {report['concerns']}")
                    if report["symptoms"]:
                        st.write(f"**Symptoms after use:** {report['symptoms']}")
                    st.write(f"**Description:** {report['description']}")

        # --- Grid View ---
        elif view_option == "Grid View":
            num_columns = 3
            rows = [reports[i:i + num_columns] for i in range(0, len(reports), num_columns)]

            for row in rows:
                cols = st.columns(len(row))
                for col, report in zip(cols, row):
                    with col:
                        st.markdown(f"**📍 {report['address']}**")
                        st.markdown(f"🕒 {report['timestamp']}")
                        st.markdown(f"**Type:** {report['type']}")
                        st.markdown(f"**Used:** {report['used']}")
                        if report.get('symptoms'):
                            st.markdown(f"*Symptoms:* {report['symptoms']}")
                        if report.get('description'):
                            st.markdown(f"*Description:* {report['description']}")
    else:
        st.info("No reports yet.")

# TABLE TAB
with table_tab:
    st.subheader("📊 Tabular View")
    df = load_data()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Reports CSV", csv, "water_reports.csv", "text/csv")
    else:
        st.info("No reports to display.")

# TRENDS TAB
with trends_tab:
    st.header("📈 Community Trends by Zip Code")
    data = load_data()
    if not data.empty:
        # Convert timestamp to datetime and extract weekly periods
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['week'] = data['timestamp'].dt.to_period("W").astype(str)

        # Group data by ZIP code and week
        trend_data = data.groupby(['zipcode', 'week']).size().reset_index(name='report_count')
        zipcodes = trend_data['zipcode'].unique()

        # Dropdown to select a ZIP code
        selected_zip = st.selectbox("Select a ZIP Code to View Trends", zipcodes)
        selected_data = trend_data[trend_data['zipcode'] == selected_zip]

        if not selected_data.empty:
            # Plot trends for the selected ZIP code
            st.subheader(f"📍 Reports Over Time for ZIP Code: {selected_zip}")
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(selected_data['week'], selected_data['report_count'], marker='o', color='b', linestyle='-', linewidth=2)

            # Show every Nth week (e.g., every 4th week)
            nth_week = 4
            week_labels = selected_data['week'][::nth_week]
            ax.set_xticks(selected_data['week'][::nth_week])
            ax.set_xticklabels(week_labels, rotation=45, ha='right', fontsize=10)

            # Add labels and title for clarity
            ax.set_xlabel("Week", fontsize=12)
            ax.set_ylabel("Number of Reports", fontsize=12)
            ax.set_title(f"Water Source Reports Over Time - {selected_zip}", fontsize=14)

            st.pyplot(fig)

            st.markdown("---")
            st.subheader("Top ZIP Codes by Total Reports")

            # Aggregate reports by ZIP code and show the top 5
            top_zips = trend_data.groupby('zipcode')['report_count'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_zips)
        else:
            st.info("No data available for the selected ZIP code.")
    else:
        st.info("No data available yet. Submit some reports to see trends!")

# AI ANALYSIS TAB
with ai_analysis_tab:
    st.header("🤖 AI Analysis of Water Reports by ZIP Code")
    data = load_data()
    if not data.empty:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['week'] = data['timestamp'].dt.to_period("W").astype(str)

        trend_data = data.groupby(['zipcode', 'week']).size().reset_index(name='report_count')
        zipcodes = trend_data['zipcode'].unique()

        selected_zip = st.selectbox("Select a ZIP Code to Analyze", ["All"] + sorted(zipcodes))
        if selected_zip != "All":
            trend_data = trend_data[trend_data['zipcode'] == selected_zip]

        if not trend_data.empty:
            aisubmit = st.button("🔍 Analyze This ZIP Code")
            if aisubmit:
                try:
                    from openai import OpenAI
                    import openai
                    client = OpenAI()

                    st.subheader(f"🧠 AI Analysis for ZIP Code {selected_zip}")
                    weekly_summary = trend_data.tail(12).to_dict(orient='records')

                    system_prompt = f"""
                    You are an expert assistant reviewing a collection of user-submitted reports about unsanitary water issues.
                    Each report includes a ZIP code, date, and a short description of the problem.

                    Your task is to analyze the reports for ZIP code {selected_zip} and provide a structured summary of the specific water-related problems being reported.

                    Instructions:
                    - Group similar issues together (e.g., bad smell, unusual color, poor taste, contamination, etc.).
                    - If certain issues happen repeatedly over time, point that out with approximate dates.
                    - If certain neighborhoods, streets, or areas are mentioned frequently, highlight them.
                    - Focus on the nature and severity of the water problems, not how many reports there are.
                    - Do not include report counts or mention that more analysis is needed.

                    Present the summary in a clear, organized format that would be useful to local officials or utility workers trying to understand what's happening in this area.
                    """

                    user_prompt = f"Here is the latest report data for ZIP {selected_zip}:\n{weekly_summary}"

                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": system_prompt.strip()},
                            {"role": "user", "content": user_prompt},
                        ],
                        max_tokens=300,
                        temperature=0.5,
                    )
                    st.markdown(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error during analysis: {e}")
        else:
            st.info("No data available for the selected ZIP code.")
    else:
        st.info("No data available yet. Submit some reports to see trends!")
