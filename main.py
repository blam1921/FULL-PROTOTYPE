import streamlit as st

LOGO_URL = "https://github.com/blam1921/FULL-PROTOTYPE/blob/main/waterwatchlogo.png?raw=true"

# Set page config
st.set_page_config(page_title="WaterWatch Community", layout="wide")

# 🔹 Global CSS Styling (Dark/Light Mode)
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', sans-serif;
    }

    @media (prefers-color-scheme: light) {
        html, body, [class*="css"] {
            background-color: #f8fcfd;
            color: #000000;
        }
        .consent-box {
            background-color: #e0f7fa;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .stButton > button {
            background-color: #00acc1;
            color: white;
        }
    }

    @media (prefers-color-scheme: dark) {
        html, body, [class*="css"] {
            background-color: #121212;
            color: #ffffff;
        }
        .consent-box {
            background-color: #263238;
            box-shadow: 0 4px 12px rgba(255,255,255,0.1);
        }
        .stButton > button {
            background-color: #26c6da;
            color: #000000;
        }
    }

    .stButton > button {
        border-radius: 0.5rem;
        padding: 0.5rem 1.2rem;
    }
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
    <div class="consent-box" style='padding: 2rem; border-radius: 1rem; max-width: 700px; margin: auto;'>
        <h2 style='text-align: center;'>🔒 Consent Required</h2>
        <p style='text-align: center;'>Before using this app, please review and agree to the following:</p>
        <ul>
            <li>We collect anonymous information to improve the app.</li>
            <li>No personal data is stored.</li>
            <li>Your contributions help support the community.</li>
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
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Home", "Alerts"])

    st.title("💧 WaterWatch Community Support System")
    st.markdown("""
    Welcome to **WaterWatch**, a community support hub for accessing and logging water resources, meals, showers, and clinics.

    Use the sidebar to navigate to features.
    """)
    st.markdown(
        f'<div style="text-align: center;"><img src="{LOGO_URL}" width="500"></div>',
        unsafe_allow_html=True
    )
    

st.logo(LOGO_URL, size="large", link=None, icon_image=None)
# Center and enlarge the logo using custom HTML and CSS
st.markdown(
    f"""
    <style>
        .logo-container img {{
            width: 800px;  /* Adjust the width to make the logo larger */
        }}
    </style>
    <div class="logo-container" style="text-align: center;">
        <img src="{LOGO_URL}" alt="Streamlit Logo">
    </div>
    """, unsafe_allow_html=True
)
