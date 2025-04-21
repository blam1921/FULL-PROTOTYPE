import streamlit as st
import requests
import os
from openai import OpenAI

# Read API keys from environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize session state for alerts
if "alerts" not in st.session_state:
    st.session_state.alerts = []

st.set_page_config(layout="wide")
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

# Geocoding with Google Maps API (clean version)
if geocode_button:
    if not GOOGLE_API_KEY:
        st.error("❌ GOOGLE_API_KEY is missing. Please set it as an environment variable.")
    elif not address:
        st.warning("⚠️ Please enter an address before clicking the autofill button.")
    else:
        try:
            geo_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}"
            response = requests.get(geo_url)
            geo_response = response.json()

            if geo_response["status"] == "OK" and geo_response["results"]:
                coords = geo_response["results"][0]["geometry"]["location"]
                lat, lng = coords['lat'], coords['lng']
                st.success(f"📍 Coordinates found: Latitude: `{lat}`, Longitude: `{lng}`")
            else:
                st.warning(f"❌ Google API did not return coordinates. Status: {geo_response['status']}")
        except Exception as e:
            st.error(f"🚨 Error while requesting coordinates: {e}")

# Alert Generation with OpenAI
if submit_button:
    if not OPENAI_API_KEY:
        st.error("Missing OpenAI API key. Set OPENAI_API_KEY in your environment.")
    else:
        prompt = (
            f"You are helping homeless users find resources. "
            f"Write a very short, friendly SMS-style alert about a new {resource_type} available at {location_name}, {address}. "
            f"It is available {hours}. Keep it positive and encouraging."
        )
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You write short, friendly community alerts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )
            message = response.choices[0].message.content.strip()

            alert_entry = {
                "type": resource_type,
                "message": message,
                "comments": []
            }
            st.session_state.alerts.append(alert_entry)
            st.success("✅ Alert generated successfully!")
            st.info(message)

        except Exception as e:
            st.error(f"Error generating alert: {e}")

st.divider()

# Filtering
st.header("📋 Generated Alerts")
filter_type = st.selectbox("Filter by Type", ["All", "Water Station", "Free Meal", "Shower", "Health Clinic"])

filtered_alerts = [
    alert for alert in st.session_state.alerts
    if filter_type == "All" or alert["type"] == filter_type
]

if filtered_alerts:
    for idx, alert in enumerate(filtered_alerts, 1):
        st.markdown(f"**{idx}.** {alert['message']}")

        with st.expander("💬 Add/View Comments"):
            for comment in alert['comments']:
                st.write(f"🗨️ {comment}")
            new_comment = st.text_input(f"Add a comment for alert #{idx}", key=f"comment_{idx}")
            if st.button(f"Submit Comment #{idx}", key=f"submit_comment_{idx}"):
                alert['comments'].append(new_comment)
                st.success("Comment added!")
else:
    st.info("No alerts to display.")

st.download_button(
    label="📥 Download Alerts as Text File",
    data="\n\n".join([a["message"] for a in st.session_state.alerts]),
    file_name="alerts.txt",
    mime="text/plain"
)
