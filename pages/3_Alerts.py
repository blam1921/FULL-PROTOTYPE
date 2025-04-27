import streamlit as st
if "consent_given" not in st.session_state or not st.session_state.consent_given:
    st.error("❌ Consent is required to use this app. Please return to the homepage.")
    st.stop()
import requests
from openai import OpenAI

# Set your API keys
client = OpenAI(OpenAPI)
OPENCAGE_API_KEY = (GoogleAPI)

# In-memory lists
alerts = []
comments = {}
st.title("💧 LifeDrop - Community Alert System")
st.caption("Manage and send alerts for water, meals, showers, and clinics.")

# Add New Resource
st.header("➕ Add New Resource")
with st.form(key='resource_form'):
    resource_type = st.selectbox("Type of Resource", ["Water Station", "Free Meal", "Shower", "Health Clinic"])
    location_name = st.text_input("Location Name")
    address = st.text_input("Address")
    hours = st.text_input("Hours Available (e.g., 9AM - 6PM)")

    # Autofill Coordinates via Geocoding (optional)
    geocode_button = st.form_submit_button("Autofill Coordinates with Address")
    submit_button = st.form_submit_button(label='Generate Alert')

if geocode_button and address:
    try:
        geo_url = f"https://api.opencagedata.com/geocode/v1/json?q={address}&key={OPENCAGE_API_KEY}"
        geo_response = requests.get(geo_url).json()
        coords = geo_response['results'][0]['geometry']
        st.success(f"📍 Coordinates found: {coords['lat']}, {coords['lng']}")

        # ➡️ Add the map WITHOUT pandas
        st.map([{"lat": coords['lat'], "lon": coords['lng']}])
        # ⬅️ End of added map
    except Exception as e:
        st.error(f"Could not find coordinates. Check the address or try again.")

if submit_button:
    # Prepare prompt
    prompt = f"""
    You are helping homeless users find resources. 
    Write a very short, friendly SMS-style alert about a new {resource_type} available at {location_name}, {address}.
    It is available {hours}. 
    Keep it positive and encouraging.
    """

    # Generate alert with OpenAI
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
        alerts.append(alert_entry)
        st.success("✅ Alert generated successfully!")
        st.info(message)

    except Exception as e:
        st.error(f"Error generating alert: {e}")

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
else:
    st.info("No alerts to display.")

# Download option
st.download_button(
    label="📥 Download Alerts as Text File",
    data="\n\n".join([a["message"] for a in alerts]),
    file_name="alerts.txt",
    mime="text/plain"
)
