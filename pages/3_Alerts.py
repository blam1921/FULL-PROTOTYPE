import streamlit as st
import os
import requests

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

# In-memory lists
alerts = []
comments = {}

# Store coordinates globally to avoid scope issues
coords = None

st.title("💧 LifeDrop - Community Alert System")
st.caption("Manage and send alerts for water, meals, showers, and clinics.")

# Add New Resource
st.header("➕ Add New Resource")
with st.form(key='resource_form'):
    resource_type = st.selectbox("Type of Resource", ["Water Station", "Free Meal", "Shower", "Health Clinic"])
    location_name = st.text_input("Location Name")
    address = st.text_input("Address")
    hours = st.text_input("Hours Available (e.g., 9AM - 6PM)")

    # Define the form submission button
    submit_button = st.form_submit_button(label='Generate Alert')

# Automatically generate map when address is input
if address and OPENCAGE_API_KEY:
    try:
        geo_url = f"https://api.opencagedata.com/geocode/v1/json?q={address}&key={OPENCAGE_API_KEY}"
        geo_response = requests.get(geo_url).json()
        if geo_response['results']:
            coords = geo_response['results'][0]['geometry']
            st.success(f"📍 Coordinates found: {coords['lat']}, {coords['lng']}")

            # Show map for the coordinates
            st.map([{"lat": coords['lat'], "lon": coords['lng']}])
        else:
            st.error("No coordinates found for the provided address.")
    except Exception as e:
        st.error(f"Could not find coordinates. Check the address or try again: {e}")

# Submit the alert after generating the coordinates
if submit_button:
    if client:
        # Prepare prompt
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

            # Prepare the alert entry
            alert_entry = {
                "type": resource_type,
                "message": message,
                "location_name": location_name,
                "address": address,
                "coordinates": coords,  # Store coordinates here if they exist
                "comments": []
            }

            alerts.append(alert_entry)
            st.success("✅ Alert generated successfully!")
            st.info(message)

            # If we have coordinates, show the map below the alert
            if coords:
                st.map([{"lat": coords['lat'], "lon": coords['lng']}])

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

        # If we have coordinates, show the map beneath the alert
        if alert["coordinates"]:
            st.map([{"lat": alert["coordinates"]['lat'], "lon": alert["coordinates"]['lng']}])

else:
    st.info("No alerts to display.")

# Download option
st.download_button(
    label="📥 Download Alerts as Text File",
    data="\n\n".join([a["message"] for a in alerts]),
    file_name="alerts.txt",
    mime="text/plain"
)
