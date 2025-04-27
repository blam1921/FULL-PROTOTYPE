import streamlit as st
import os
import requests
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

# Pull existing alerts from the Google Sheet
 existing_alerts = gsheets_conn.read()
 existing_alerts = conn.read(worksheet=SHEET_NAME)
 alerts = existing_alerts if existing_alerts is not None else []

# Sheet columns
columns = ["ID", "Type", "Message", "Comments", "Location Name", "Address", "Hours Available", "Coordinates (Lat)", "Coordinates (Lng)"]

# In-memory list of alerts
alerts = []

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

if geocode_button and address:
    if OPENCAGE_API_KEY:
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
    else:
        st.error("❌ OpenCage API key not set. Cannot autofill coordinates.")

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
                messages=[{"role": "system", "content": "You write short, friendly community alerts."},
                          {"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            message = response.choices[0].message.content.strip()

            alert_entry = {
                "type": resource_type,
                "message": message,
                "comments": [],
                "location_name": location_name,
                "address": address,
                "hours": hours
            }
            alerts.append(alert_entry)

            # Write the alert entry to Google Sheets
            gsheets.append_row([
                len(alerts),  # ID (auto-incremented by length of alerts list)
                resource_type,
                message,
                "",  # Empty comment field initially
                location_name,
                address,
                hours,
                coords['lat'] if 'coords' in locals() else "",
                coords['lng'] if 'coords' in locals() else ""
            ])

            st.success("✅ Alert generated and saved to Google Sheets!")
            st.info(message)

        except Exception as e:
            st.error(f"Error generating alert: {e}")
    else:
        st.error("❌ OpenAI API key not set. Cannot generate alerts.")

st.divider()

# Filtering
st.header("📋 Generated Alerts")
filter_type = st.selectbox("Filter by Type", ["All", "Water Station", "Free Meal", "Shower", "Health Clinic"])

# Read alerts from Google Sheets
alerts_from_sheet = gsheets.get_all_rows()

filtered_alerts = [
    alert for alert in alerts_from_sheet
    if filter_type == "All" or alert["Type"] == filter_type
]

if filtered_alerts:
    for idx, alert in enumerate(filtered_alerts, 1):
        st.markdown(f"**{idx}.** {alert['Message']}")

        # Comments Section
        with st.expander("💬 Add/View Comments"):
            comments = alert['Comments']
            for comment in comments:
                st.write(f"🗨️ {comment}")
            new_comment = st.text_input(f"Add a comment for alert #{idx}", key=f"comment_{idx}")
            if st.button(f"Submit Comment #{idx}", key=f"submit_comment_{idx}"):
                # Add comment to Google Sheets
                updated_comments = comments + [new_comment]
                gsheets.update_row(idx, {"Comments": updated_comments})
                st.success("Comment added!")
else:
    st.info("No alerts to display.")

# Download option
st.download_button(
    label="📥 Download Alerts as Text File",
    data="\n\n".join([a["Message"] for a in alerts_from_sheet]),
    file_name="alerts.txt",
    mime="text/plain"
)

