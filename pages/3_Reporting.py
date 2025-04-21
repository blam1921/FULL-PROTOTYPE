import streamlit as st
from datetime import datetime
import pandas as pd
import os
from PIL import Image
import matplotlib.pyplot as plt

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


st.set_page_config(page_title="Report a Water Source", layout="wide")
st.title("🚰 Report a Water Source")

st.markdown("""
Help your community by sharing information about local water sources. 
This tool is for awareness only — we do not verify the safety of any water.
""")



# Directory for saving uploaded images
IMAGE_DIR = "uploaded_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# Initialize a session state list to store reports if not already present
if "reports" not in st.session_state:
    st.session_state.reports = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

def update_key():
    st.session_state.uploader_key += 1

# Function to load data from session state
def load_data():
    # Return data from session state
    return pd.DataFrame(st.session_state.reports)

# Add this function to handle CSV uploads and merging
def process_uploaded_csv(uploaded_file):
    try:
        # Read the uploaded CSV into a DataFrame
        uploaded_df = pd.read_csv(uploaded_file)

        # Ensure the uploaded CSV has the required columns
        required_columns = ["timestamp", "address", "zipcode", "description", "concerns", "type", "used", "symptoms", "alert", "photo_path"]
        missing_columns = [col for col in required_columns if col not in uploaded_df.columns]
        if missing_columns:
            st.error(f"The uploaded CSV is missing the following required columns: {', '.join(missing_columns)}")
            return

        # Convert timestamp column to datetime
        uploaded_df["timestamp"] = pd.to_datetime(uploaded_df["timestamp"], errors="coerce")

        # Convert the DataFrame to a list of dictionaries
        uploaded_reports = uploaded_df.to_dict(orient="records")

        # Merge the uploaded reports with the existing reports
        st.session_state.reports.extend(uploaded_reports)
        st.success("✅ CSV uploaded and merged successfully!")
    
    except Exception as e:
        st.error(f"An error occurred while processing the uploaded CSV: {e}")

# Tabs
report_tab, gallery_tab, table_tab, trends_tab, ai_analysis_tab = st.tabs(["📋 Report", "🖼️ Gallery", "📊 Tabular View", "📈 Community Trends", "🤖AI Analysis"])

with report_tab:
    st.header("Submit a Water Report or Upload a CSV")

    # CSV Upload Section
    st.subheader("📤 Upload a CSV File")
    uploaded_file = st.file_uploader(
        "Upload a CSV file to add reports",
        type=["csv"],
        key=f"uploader_{st.session_state.uploader_key}",
    )

    if uploaded_file:
        try:
            # Read the uploaded CSV into a DataFrame
            uploaded_df = pd.read_csv(uploaded_file)

            # Ensure the uploaded CSV has the required columns
            required_columns = ["timestamp", "address", "zipcode", "description", "concerns", "type", "used", "symptoms", "alert", "photo_path"]
            missing_columns = [col for col in required_columns if col not in uploaded_df.columns]
            if missing_columns:
                st.error(f"The uploaded CSV is missing the following required columns: {', '.join(missing_columns)}")
            else:
                # Convert timestamp column to datetime
                uploaded_df["timestamp"] = pd.to_datetime(uploaded_df["timestamp"], errors="coerce")

                # Convert the DataFrame to a list of dictionaries
                uploaded_reports = uploaded_df.to_dict(orient="records")

                # Merge the uploaded reports with the existing reports
                st.session_state.reports.extend(uploaded_reports)
                st.success("✅ CSV uploaded and merged successfully!")

                # Reset the file uploader
                update_key()
        except Exception as e:
            st.error(f"An error occurred while processing the uploaded CSV: {e}")

    # Report Submission Form
    with st.form("water_report_form"):
        st.subheader("🗺️ Location Details")
        address = st.text_input("Address or general location", placeholder="123 Riverside Blvd, City, State")

        st.subheader("📍 Zip Code")
        zipcode = st.text_input("Zip Code", placeholder="Enter zip code")

        st.subheader("📷 Optional Photo Upload")
        photo = st.file_uploader("Upload a photo (optional)", type=["jpg", "jpeg", "png"])

        st.subheader("📝 Description")
        description = st.text_area("What does the water look/smell like? Is it flowing or still?", max_chars=300)

        st.subheader("🚩 Concerns")
        concerns = st.multiselect(
            "Select any observed issues:",
            ["Discoloration", "Foul smell", "Foam on surface", "Bugs or larvae", "Near industrial area", "Trash nearby"]
        )

        st.subheader("🧭 Water Source Type")
        source_type = st.selectbox("Choose type of source:", ["Faucet", "River/Stream", "Pipe Leak", "Fountain", "Rainwater Pool", "Other"])

        used = st.radio("Did you use this water?", ["Yes", "No"])

        symptoms = st.text_input("Any symptoms after use? (optional)")

        alert_others = st.checkbox("Send community alert")

        submitted = st.form_submit_button("Submit Report")

        if submitted:
            photo_path = None
            if photo:
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp_str}_{photo.name}"
                photo_path = os.path.join(IMAGE_DIR, filename)
                with open(photo_path, "wb") as f:
                    f.write(photo.getbuffer())

            report = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "address": address,
                "zipcode": zipcode,
                "description": description,
                "concerns": ", ".join(concerns),
                "type": source_type,
                "used": used,
                "symptoms": symptoms,
                "alert": alert_others,
                "photo_path": photo_path,
            }
            st.session_state.reports.append(report)
            st.success("✅ Your report has been submitted. Thank you for keeping the community informed!")
            
# Display reports summary below the form
if st.session_state.reports:
    st.markdown("---")

    with gallery_tab:
        st.header("🖼️ Community Gallery of Reports")

        # Convert session state reports to a DataFrame
        df = pd.DataFrame(st.session_state.reports)

        # Ensure the 'zipcode' column is treated as strings
        if 'zipcode' in df.columns:
            df['zipcode'] = df['zipcode'].astype(str)

        # Convert 'timestamp' to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        # --- Filter Section ---
        st.subheader("🔎 Filter Reports")

        # Drop missing ZIP codes and get unique values
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

        # --- View Selection ---
        view_option = st.radio("Choose view:", ["Grid View", "Detailed View"], horizontal=True)

        # --- Grid View ---
        if view_option == "Grid View":
            num_columns = 3
            rows = [reports[i:i + num_columns] for i in range(0, len(reports), num_columns)]

            for row in rows:
                cols = st.columns(len(row))
                for col, report in zip(cols, row):
                    with col:
                        st.markdown(f"**📍 {report['address']}**")
                        st.markdown(f"🕒 {report['timestamp']}")
                        if pd.notna(report["photo_path"]) and os.path.exists(report["photo_path"]):
                            st.image(report["photo_path"], caption=None, use_container_width=True)
                        st.markdown(f"**Type:** {report['type']}")
                        st.markdown(f"**Used:** {report['used']}")
                        if report['symptoms']:
                            st.markdown(f"*Symptoms:* {report['symptoms']}")

        # --- Detailed View ---
        else:
            for report in reports:
                with st.expander(f"📍 {report['address']} ({report['timestamp']})"):
                    st.write(f"**Source Type:** {report['type']} | **Used:** {report['used']}")
                    if report['concerns']:
                        st.write(f"**Concerns:** {report['concerns']}")
                    if report['symptoms']:
                        st.write(f"**Symptoms after use:** {report['symptoms']}")
                    st.write(f"**Description:** {report['description']}")
                    if pd.notna(report["photo_path"]) and os.path.exists(report["photo_path"]):
                        st.image(report["photo_path"], caption="Reported Photo", use_container_width=True)

    # Optional CSV export and live table view
    with table_tab:
        df = pd.DataFrame(st.session_state.reports).drop(columns=["photo_path"])
        st.subheader("📊 Tabular View of Reports")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Reports CSV", csv, "water_reports.csv", "text/csv")
else:
    st.info("No reports submitted yet.")

# Trends Tab
with trends_tab:
    st.header("📈 Community Trends by Zip Code")
    data = load_data()
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
    data = load_data()
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