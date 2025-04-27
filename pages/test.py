import streamlit as st
import os
import requests
from datetime import datetime, timedelta
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from openai import OpenAI

# Check user consent
if "consent_given" not in st.session_state or not st.session_state.consent_given:
    st.error("❌ Consent is required to use this app. Please return to the homepage.")
    st.stop()

# Set API keys from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENCAGE_API_KEY = os.getenv('OPENCAGE_API_KEY')

client = OpenAI()

# Google Sheets Setup
SHEET_NAME = "alerts"
conn = st.connection("gsheets", type=GSheetsConnection)

# Set expiration duration (in hours)
ALERT_EXPIRATION_HOURS = 48

def load_data():
    # Load existing data from Google Sheets
    data = conn.read(worksheet=SHEET_NAME, ttl=5)
    data = data.dropna(how="all")  # Ensure no empty rows are included

    # Remove expired alerts
    now = datetime.now()
    if not data.empty:
        data['timestamp_dt'] = pd.to_datetime(data['timestamp'])
        not_expired = data['timestamp_dt'] + timedelta(hours=ALERT_EXPIRATION_HOURS) > now
        expired = data[~not_expired]

        if not expired.empty:
            # Some expired alerts found, remove them
            data = data[not_expired].drop(columns=["timestamp_dt"])
            conn.update(worksheet=SHEET_NAME, data=data)
        else:
            data = data.drop(columns=["timestamp_dt"])
    
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

    # Timer dropdown for users to select alert expiration time
    timer_duration = st.selectbox("Select Timer Duration (Minutes)", [5, 10, 15, 30, 60, 120], index=4)  # Default 60 minutes

    geocode_button = st.form_submit_button("Autofill Coordinates with Address")
    submit_button = st.form_submit_button(label='Generate Alert')

if geocode_button and address:
    if OPENCAGE_API_KEY:
        try:
            geo_url = f"https://api.opencagedata.com/geocode/v1/json?q={address}&key={OPENCAGE_API_KEY}"
            geo_response = requests.get(geo_url).json()
            coords = geo_response['results'][0]['geometry']
            st.success(f"📍 Coordinates found: {coords['lat']}, {coords['lng']}")

            st.map([{"lat": coords['lat'], "lon": coords['lng']}])
        except Exception as e:
            st.error(f"Could not find coordinates. Check the address or try again.")
    else:
        st.error("❌ OpenCage API key not set. Cannot autofill coordinates.")

if submit_button:
    if client:
        prompt = f"""
        You are helping homeless users find resources. 
        Write a very short, friendly SMS-style alert about a new {resource_type} available at {location_name}, {address}.
        It is available {hours}. 
        Keep it positive and encouraging.
        """
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You write short, friendly community alerts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            message = response.choices[0].message.content.strip()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            expiration_time = datetime.now() + timedelta(minutes=timer_duration)  # Set expiration time

            alert = {
                "timestamp": timestamp,
                "type": resource_type,
                "message": message,
                "location_name": location_name,
                "address": address,
                "hours": hours,
                "expiration_time": expiration_time.strftime("%Y-%m-%d %H:%M")  # Store expiration time
            }

            updated_alerts = pd.concat([alerts, pd.DataFrame([alert])], ignore_index=True)
            conn.update(worksheet=SHEET_NAME, data=updated_alerts)

            st.success("✅ Alert generated and submitted successfully!")
            st.info(message)

        except Exception as e:
            st.error(f"Error generating alert: {e}")
    else:
        st.error("❌ OpenAI API key not set. Cannot generate alerts.")

st.divider()

# Filtering
st.header("📋 Generated Alerts")
filter_type = st.selectbox("Filter by Type", ["All", "Water Station", "Free Meal", "Shower", "Health Clinic"])

alerts_dicts = alerts.to_dict(orient="records")

filtered_alerts = [
    alert for alert in alerts_dicts
    if filter_type == "All" or alert["type"] == filter_type
]

if filtered_alerts:
    for idx, alert in enumerate(filtered_alerts, 1):
        st.markdown(f"**{idx}.** {alert['message']}")

        # Calculate time remaining for each alert
        expiration_time = datetime.strptime(alert['expiration_time'], "%Y-%m-%d %H:%M")
        time_left = expiration_time - datetime.now()

        # Display the remaining time
        if time_left.total_seconds() > 0:
            st.markdown(f"🕒 Time Remaining: {str(time_left).split('.')[0]}")  # Format time without milliseconds
        else:
            st.markdown("❌ This alert has expired and will be removed shortly.")

            # Automatically remove expired alerts from the displayed list
            alerts = alerts[alerts['timestamp'] != alert['timestamp']]
            conn.update(worksheet=SHEET_NAME, data=alerts)

else:
    st.info("No alerts to display.")

st.download_button(
    label="📥 Download Alerts as Text File",
    data="\n\n".join([a["message"] for a in alerts_dicts]),
    file_name="alerts.txt",
    mime="text/plain"
)
