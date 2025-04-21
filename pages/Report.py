import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import matplotlib.pyplot as plt
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Google Sheets Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SPREADSHEET_ID = st.secrets["spreadsheet_id"]
SHEET_NAME = "Water-Report"

# Setup Google Sheets connection
def connect_to_gsheets():
    creds_dict = st.secrets["gsheets"]  # 👈 this accesses the dict stored in secrets.toml
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    return sheet

def get_all_reports():
    sheet = connect_to_gsheets()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def append_report_to_sheet(report):
    sheet = connect_to_gsheets()
    row = [
        report["timestamp"],
        report["address"],
        report["zipcode"],
        report["description"],
        report["concerns"],
        report["type"],
        report["used"],
        report["symptoms"],
        str(report["alert"]),
        report["photo_path"] or ""
    ]
    sheet.append_row(row)

# App Setup
st.set_page_config(page_title="Report a Water Source", layout="wide")
st.title("🚰 Report a Water Source")

IMAGE_DIR = "uploaded_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# UI Tabs
report_tab, gallery_tab, table_tab, trends_tab, ai_analysis_tab = st.tabs(["📋 Report", "🖼️ Gallery", "📊 Tabular View", "📈 Community Trends", "🤖AI Analysis"])

# REPORT TAB
with report_tab:
    st.subheader("📝 Submit a Water Report")
    with st.form("report_form"):
        address = st.text_input("📍 Address")
        zipcode = st.text_input("🏷️ Zipcode")
        photo = st.file_uploader("📸 Upload Photo", type=["jpg", "jpeg", "png"])
        description = st.text_area("Description")
        concerns = st.multiselect("Concerns", ["Discoloration", "Smell", "Trash nearby", "Other"])
        source_type = st.selectbox("Water Source Type", ["Faucet", "River", "Leak", "Other"])
        used = st.radio("Did you use it?", ["Yes", "No"])
        symptoms = st.text_input("Symptoms after use (optional)")
        alert_others = st.checkbox("🚨 Send alert to community")

        submitted = st.form_submit_button("Submit Report")
        if submitted:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            photo_path = None
            if photo:
                filename = f"{timestamp.replace(':', '').replace(' ', '_')}_{photo.name}"
                photo_path = os.path.join(IMAGE_DIR, filename)
                with open(photo_path, "wb") as f:
                    f.write(photo.getbuffer())

            report = {
                "timestamp": timestamp,
                "address": address,
                "zipcode": zipcode,
                "description": description,
                "concerns": ", ".join(concerns),
                "type": source_type,
                "used": used,
                "symptoms": symptoms,
                "alert": alert_others,
                "photo_path": photo_path
            }

            append_report_to_sheet(report)
            st.success("✅ Report submitted successfully!")

# GALLERY TAB
with gallery_tab:
    st.subheader("🖼️ Report Gallery")
    df = get_all_reports()
    if not df.empty:
        for i, row in df.iterrows():
            with st.expander(f"{row['address']} ({row['timestamp']})"):
                st.write(f"**Source Type:** {row['type']} | **Used:** {row['used']}")
                if row["concerns"]:
                    st.write(f"**Concerns:** {row['concerns']}")
                if row["symptoms"]:
                    st.write(f"**Symptoms:** {row['symptoms']}")
                st.write(f"**Description:** {row['description']}")
                if row["photo_path"] and os.path.exists(row["photo_path"]):
                    st.image(row["photo_path"], caption="Uploaded Photo", use_container_width=True)
    else:
        st.info("No reports yet.")

# TABLE TAB
with table_tab:
    st.subheader("📊 Tabular View")
    df = get_all_reports()
    if not df.empty:
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", csv, "water_reports.csv", "text/csv")
    else:
        st.info("No reports to display.")

# Trends Tab
with trends_tab:
    st.header("📈 Community Trends by Zip Code")
    data = get_all_reports()
    if not data.empty:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['week'] = data['timestamp'].dt.to_period("W").astype(str)

        trend_data = data.groupby(['zipcode', 'week']).size().reset_index(name='report_count')
        zipcodes = trend_data['zipcode'].unique()

        selected_zip = st.selectbox("Select a Zip Code to View Trends", zipcodes)
        selected_data = trend_data[trend_data['zipcode'] == selected_zip]

        st.subheader(f"📍 Reports Over Time for Zip Code: {selected_zip}")
        fig, ax = plt.subplots(figsize=(12, 6))  # Adjust the size of the graph

        ax.plot(selected_data['week'], selected_data['report_count'], marker='o', color='b', linestyle='-', linewidth=2, markersize=5)

        # Show every Nth week (e.g., every 4th week)
        nth_week = 4
        week_labels = selected_data['week'][::nth_week]  # Get every nth week
        ax.set_xticks(selected_data['week'][::nth_week])  # Set only these weeks as ticks
        ax.set_xticklabels(week_labels, rotation=45, ha='right', fontsize=10)

        # Add labels and title for clarity
        ax.set_xlabel("Week", fontsize=12)
        ax.set_ylabel("Number of Reports", fontsize=12)
        ax.set_title(f"Water Source Reports Over Time - {selected_zip}", fontsize=14)

        st.pyplot(fig)

        st.markdown("---")
        st.subheader("Top Zip Codes by Total Reports")
        
        # Aggregate reports by ZIP code and show the top 5
        top_zips = trend_data.groupby('zipcode')['report_count'].sum().sort_values(ascending=False).head(5)
        st.bar_chart(top_zips)
    else:
        st.info("No data available yet. Submit some reports to see trends!")

# AI Analysis Tab
with ai_analysis_tab:
    st.header("🤖 AI Analysis of Water Reports by Zip Code")
    data = get_all_reports()
    if not data.empty:
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['week'] = data['timestamp'].dt.to_period("W").astype(str)

        trend_data = data.groupby(['zipcode', 'week']).size().reset_index(name='report_count')
        zipcodes = trend_data['zipcode'].unique()

        selected_zip = st.selectbox("Select a Zip Code to Analyze", zipcodes)
        aisubmit = st.button("🔍 Analyze This Zip Code")
        if aisubmit:
            from openai import OpenAI  # Lazy import
            import openai
            client = OpenAI()

            st.subheader(f"🧠 AI Analysis for Zip Code {selected_zip}")

            # Trimmed summary for GPT
            selected_data = trend_data[trend_data['zipcode'] == selected_zip]
            weekly_summary = selected_data.tail(12).to_dict(orient='records')  # Last 12 weeks only

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

            # Call OpenAI API (token-friendly)
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt.strip()},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=300,
                    temperature=0.5,
                )
                analysis = response.choices[0].message.content
                st.markdown(analysis)

            except Exception as e:
                st.error(f"Error during analysis: {e}")
    else:
        st.info("No data available yet. Submit some reports to see trends!")
