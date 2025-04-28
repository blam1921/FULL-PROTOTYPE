import streamlit as st

LOGO_URL = "https://raw.githubusercontent.com/blam1921/FULL-PROTOTYPE/refs/heads/main/waterwatchlogov2.png"

# Set page config
st.set_page_config(page_title="WaterWatch Community", layout="wide")

# Get Streamlit's current theme settings
primary_color = st.get_option('theme.primaryColor')
background_color = st.get_option('theme.backgroundColor')
text_color = st.get_option('theme.textColor')
secondary_background_color = st.get_option('theme.secondaryBackgroundColor')

# 🔹 Global CSS Styling (using Streamlit's theme settings)
st.markdown(f"""
<style>
    html, body, [class*="css"] {{
        font-family: 'Segoe UI', sans-serif;
    }}

    .consent-box {{
        padding: 2rem;
        border-radius: 1rem;
        max-width: 700px;
        margin: auto;
        background-color: {secondary_background_color};
        color: {text_color};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }}

    .stButton > button {{
        background-color: {primary_color};
        color: white;
        border-radius: 0.5rem;
        padding: 0.5rem 1.2rem;
    }}
</style>
""", unsafe_allow_html=True)

# 🧠 Initialize session state
if "consent_given" not in st.session_state:
    st.session_state.consent_given = False
if "analytics_consent" not in st.session_state:
    st.session_state.analytics_consent = None

# 📢 Consent Form
def show_consent_form():
    st.markdown("""
    <div class="consent-box">
        <h2 style='text-align: center;'>🔒 Consent Required</h2>
        <p style='text-align: center;'>Before using this app, please review and agree to the following:</p>
        <ul>
            <li>We collect anonymous information to improve the app. This information may include your contributions to the community.</li>
            <li>Your data is stored at your own discretion and is shared publicly with other community members.</li>
            <li>Since there is no account system, data deletion is not currently available. Please consider this before sharing any information.</li>
            <li>By using this app, you consent to your contributions being shared with the community. This data may be visible to others and used to improve the app.</li>
        </ul>
        <p><b>Consent is required to use WaterWatch Community Support System.</b></p>
    </div>
    """, unsafe_allow_html=True)

    consent_choice = st.radio(
        label="Do you agree to the data collection policy?",
        options=["I consent", "I do not consent"],
        index=1
    )

    if st.button("Continue"):
        if consent_choice == "I consent":
            st.session_state.consent_given = True
            st.session_state.analytics_consent = True
            st.success("✅ Thank you! Please refresh the page to continue.")
            st.stop()
        else:
            st.error("❌ Consent is required to use this app. Please close the tab if you do not agree.")
            st.stop()

# 🚀 Main Program
if not st.session_state.consent_given:
    show_consent_form()
else:
    # Sidebar and Main Content appear after consent
    st.title("💧 WaterWatch Community Support System")
    st.markdown("""
    Welcome to **WaterWatch**, a community support hub for accessing and logging water resources, meals, showers, and clinics.

    Use the sidebar to navigate to features.
    """)
    st.markdown(
        f'<div style="text-align: center;"><img src="{LOGO_URL}" width="500"></div>',
        unsafe_allow_html=True
    )
    
with st.sidebar:
    st.image(LOGO_URL, width=300)
