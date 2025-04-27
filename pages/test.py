import streamlit as st
import os
import requests
from datetime import datetime
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Check user consent
if "consent_given" not in st.session_state or not st.session_state.consent_given:
    st.error("❌ Consent is required to use this app. Please return to the homepage.")
    st.stop()

# Set API keys from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENCAGE_API_KEY = os.getenv('OPENCAGE_API_KEY')

# Allow manual entry if OpenCage API key is missing
if not OPENCAGE_API_KEY:
    OPENCAGE_API_KEY = st.text_input("🔑 Enter your OpenCage API Key:", type="password")

# Initialize OpenAI client if key is available
if OPENAI_API_KEY:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None

# Google Sheets Setup
SHEET_NAME = "alerts"
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Load the existing data from Google Sheets
    data = conn.read(worksheet=SHEET_NAME, ttl=5)
    data = data.dropna(how="all")
    return data

# Initialize the alerts data from Google Sheets
alerts = load_data()

st.title("💧 LifeDrop - Community Alert System")
st.caption("Manage and send alerts for water, meals, showers, and clinics.")

# Add New Resource
st.header("➕ Add New Resource")
with st.form(key='resource_form'):
    resource_type = st.selectbox("Type of Resource", ["Water Station", "Free Meal", "Shower", "Health Clinic"])
    location_name = st.text_input("Location Name")
    address = st.text_input("Address")
    hours = st.text_input("Hours Available (e.g., 9AM - 6PM)")

    geocode_button = st.form_submit_button("Autofill Coordinates with Address")
    submit_button = st.form_submit_button(label='Generate Alert')

# Validate the fields when submitting the form
if submit_button:
    # Prepare prompt for generating the alert message
    prompt = f"""
    You are helping homeless users find resources. 
    Write a very short, friendly SMS-style alert about a new {resource_type} available at {location_name}, {address}.
    It is available {hours}. 
    Keep it positive and encouraging.
    """

        if client:
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": "You write short, friendly community alerts."},
                              {"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=100
                )
                message = response.choices[0].message.content.strip()

                # Build the alert dictionary
                alert_entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "type": resource_type,
                    "message": message,
                    "location_name": location_name,
                    "address": address,
                    "hours": hours,
                    "comments": []
                }

                # Append the new alert to the existing alerts
                alerts = alerts.append(alert_entry, ignore_index=True)

                # Update Google Sheets with the new data
                conn.update(worksheet=SHEET_NAME, data=alerts)

                st.success("✅ Alert generated successfully!")
                st.info(message)

            except Exception as e:
                st.error(f"Error generating alert: {e}")
        else:
            st.error("❌ OpenAI API key not set. Cannot generate alerts.")

st.divider()

# Filtering
st.header("📋 Generated Alerts")
filter_type = st.selectbox("Filter by Type", ["All", "Water Station", "Free Meal", "Shower", "Health Clinic"])

filtered_alerts = [
    alert for alert in alerts
    if filter_type == "All" or alert["type"] == filter_type
]

if filtered_alerts:
    for idx, alert in enumerate(filtered_alerts, 1):
        st.markdown(f"**{idx}.** {alert['message']}")

        # Comments Section
        with st.expander("💬 Add/View Comments"):
            for comment in alert['comments']:
                st.write(f"🗨️ {comment}")
            new_comment = st.text_input(f"Add a comment for alert #{idx}", key=f"comment_{idx}")
            if st.button(f"Submit Comment #{idx}", key=f"submit_comment_{idx}"):
                alert['comments'].append(new_comment)
                st.success("Comment added!")
                # Save updated alerts with new comment to Google Sheets
                conn.update(worksheet=SHEET_NAME, data=alerts)
else:
    st.info("No alerts to display.")

# Download option
st.download_button(
    label="📥 Download Alerts as Text File",
    data="\n\n".join([a["message"] for a in alerts]),
    file_name="alerts.txt",
    mime="text/plain"
)
