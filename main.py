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
if "language" not in st.session_state:
    st.session_state.language = "English"

# 🌎 Language Switcher
with st.sidebar:
    st.image(LOGO_URL, width=300)
    st.session_state.language = st.selectbox("🌎 Language / Idioma", ["English", "Español"])

language = st.session_state.language

# 🔵 Messages based on language
texts = {
    "consent_title": {"English": "🔒 Consent Required", "Español": "🔒 Consentimiento Requerido"},
    "consent_intro": {
        "English": "Before using this app, please review and agree to the following:",
        "Español": "Antes de usar esta aplicación, por favor revisa y acepta lo siguiente:"
    },
    "consent_points": {
        "English": [
            "We collect anonymous information to improve the app. This may include your contributions.",
            "Your data is stored at your discretion and shared publicly with the community.",
            "There is no account system; data deletion is not available.",
            "By using this app, you consent to your contributions being visible and helping improve the app."
        ],
        "Español": [
            "Recopilamos información anónima para mejorar la aplicación. Esto puede incluir tus contribuciones.",
            "Tu información se almacena bajo tu responsabilidad y se comparte públicamente con la comunidad.",
            "No existe un sistema de cuentas; actualmente no es posible eliminar datos.",
            "Al usar esta aplicación, aceptas que tus contribuciones sean visibles y ayuden a mejorar la app."
        ]
    },
    "consent_required": {
        "English": "Consent is required to use WaterWatch Community Support System.",
        "Español": "Se requiere consentimiento para usar el Sistema de Apoyo Comunitario de WaterWatch."
    },
    "consent_question": {
        "English": "Do you agree to the data collection policy?",
        "Español": "¿Aceptas la política de recopilación de datos?"
    },
    "consent_options": {
        "English": ["I consent", "I do not consent"],
        "Español": ["Consiento", "No consiento"]
    },
    "continue_button": {
        "English": "Continue",
        "Español": "Continuar"
    },
    "thank_you": {
        "English": "✅ Thank you! Please refresh the page to continue.",
        "Español": "✅ ¡Gracias! Por favor actualiza la página para continuar."
    },
    "error_consent": {
        "English": "❌ Consent is required to use this app. Please close the tab if you do not agree.",
        "Español": "❌ Se requiere consentimiento para usar esta aplicación. Cierra la pestaña si no estás de acuerdo."
    },
    "main_title": {
        "English": "💧 WaterWatch Community Support System",
        "Español": "💧 Sistema de Apoyo Comunitario WaterWatch"
    },
    "main_intro": {
        "English": "Welcome to **WaterWatch**, a community hub for accessing and logging water resources, meals, showers, and clinics.\n\nUse the sidebar to navigate between features.",
        "Español": "Bienvenido a **WaterWatch**, un centro comunitario para acceder y registrar fuentes de agua, comidas, duchas y clínicas.\n\nUsa la barra lateral para navegar entre las funciones."
    },
}

# 📢 Consent Form
def show_consent_form():
    st.markdown(f"""
    <div class="consent-box">
        <h2 style='text-align: center;'>{texts['consent_title'][language]}</h2>
        <p style='text-align: center;'>{texts['consent_intro'][language]}</p>
        <ul>
            {''.join(f"<li>{point}</li>" for point in texts['consent_points'][language])}
        </ul>
        <p><b>{texts['consent_required'][language]}</b></p>
    </div>
    """, unsafe_allow_html=True)

    consent_choice = st.radio(
        label=texts["consent_question"][language],
        options=texts["consent_options"][language],
        index=1
    )

    if st.button(texts["continue_button"][language]):
        if consent_choice == texts["consent_options"][language][0]:
            st.session_state.consent_given = True
            st.session_state.analytics_consent = True
            st.success(texts["thank_you"][language])
            st.stop()
        else:
            st.error(texts["error_consent"][language])
            st.stop()

# 🚀 Main Program
if not st.session_state.consent_given:
    show_consent_form()
else:
    st.title(texts["main_title"][language])
    st.markdown(texts["main_intro"][language])
    st.markdown(
        f'<div style="text-align: center;"><img src="{LOGO_URL}" width="500"></div>',
        unsafe_allow_html=True
    )
