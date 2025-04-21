import streamlit as st
from datetime import datetime

st.set_page_config(page_title="WaterWatch Community", layout="wide")

# 🔹 Global Theme Styling
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
        background-color: #f8fcfd;
    }
    .stButton > button {
        background-color: #00acc1;
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# 🧠 Session Variables
if "consent_given" not in st.session_state:
    st.session_state.consent_given = False
if "analytics_consent" not in st.session_state:
    st.session_state.analytics_consent = None

# 🔐 Consent Gate UI
if not st.session_state.consent_given:
    st.markdown("""
    <div style='background-color: #e0f7fa; padding: 2rem; border-radius: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-width: 700px; margin: auto;'>
        <h2 style='text-align: center;'>🔒 Consent Required</h2>
        <p style='text-align: center;'>Before using this app, please review and agree to the following:</p>
        <ul>
            <li>We collect anonymous information to improve the app.</li>
            <li>No personal data is stored.</li>
            <li>Your contributions help support the community.</li>
        </ul>
        <p><b>Would you like to allow anonymous usage data to be collected to improve WaterWatch?</b></p>
    </div>
    """, unsafe_allow_html=True)

    consent_choice = st.radio(
        label="Consent for Data Usage",
        options=["I consent", "I do not consent"],
        index=1
    )

    if st.button("Continue"):
        st.session_state.consent_given = True
        st.session_state.analytics_consent = (consent_choice == "I consent")
        st.success("✅ Response recorded. Please refresh the page to continue.")
        st.stop()
    else:
        st.stop()

# ✅ Optional: Show message if consent already accepted
st.markdown("✅ Consent previously accepted.")

# 📊 Optional Logger
def log_event(event_name, detail=""):
    if st.session_state.get("analytics_consent"):
        with open("usage_log.txt", "a") as f:
            f.write(f"{datetime.now()}, {event_name}, {detail}\n")

# 📍 Main App Content
st.title("💧 LifeDrop Community Support System")
st.markdown("""
Welcome to **LifeDrop**, a community support hub for accessing and reporting water resources, meals, showers, and clinics.

Use the sidebar to navigate:
- Create and view alerts
- Report water issues
- View clean water locations and tips
""")

log_event("Homepage Visited")
