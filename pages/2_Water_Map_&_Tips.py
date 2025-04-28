import streamlit as st

# — require consent before loading anything else —
if "consent_given" not in st.session_state or not st.session_state.consent_given:
    st.error("❌ Consent is required to use this app. Please return to the homepage.")
    st.stop()

import openai
import os
import pandas as pd
import pydeck as pdk
import requests
import math
import random

# ✅ 1. Correct way to fetch key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# ✅ 2. Set page config first
st.set_page_config(
    page_title="💧 Water Access Support",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ✅ 3. Custom styling
st.markdown(
    """
    <style>
    body { background-color: #f9fbfd; }
    .main { max-width: 1000px; margin: auto; padding-top: 20px; }
    h1, h2, h3 { text-align: center; color: #0077b6; font-size: 26px; }
    .stButton>button {
        background-color: #4DA8DA; color: white; font-size: 18px;
        border-radius: 12px; padding: 10px 20px; width: 70%;
        margin: 10px auto; display: block;
    }
    .stSelectbox, .stTextInput, .css-1d391kg, .css-1v0mbdj { font-size: 18px; }
    </style>
    """,
    unsafe_allow_html=True
)

# ✅ 4. Water image for Help Center
water_image = "https://images.unsplash.com/photo-1589927986089-35812388d1b4"

# —————— 5. Dynamic Resources Pool & Helper ——————
RESOURCE_POOL = [
    ("Charity: Water",                          "https://www.charitywater.org"),
    ("WaterAid",                                "https://www.wateraid.org"),
    ("Clean Water Fund",                        "https://www.cleanwaterfund.org"),
    ("Lifewater International",                 "https://lifewater.org"),
    ("Water For People",                        "https://www.waterforpeople.org"),
    ("Planet Water Foundation",                 "https://planet-water.org"),
    ("Global Water Challenge",                  "https://globalwaterchallenge.org"),
    ("UNICEF WASH",                             "https://www.unicef.org/wash"),
    ("Drinking Water Academy",                  "https://www.drinkingwateracademy.org"),
    ("Alliance for Water Efficiency",           "https://www.allianceforwaterefficiency.org"),
    ("Waterkeeper Alliance",                    "https://waterkeeper.org"),
    ("The Water Project",                       "https://thewaterproject.org"),
    ("Splash",                                  "https://splash.org"),
    ("Blue Planet Network",                     "https://www.blueplanetnetwork.org"),
    ("Safe Water Network",                      "https://www.safewaternetwork.org"),
    ("WHO: Water Sanitation & Health",          "https://www.who.int/teams/environment-climate-change-and-health/water-sanitation-and-health"),
    ("Oxfam: Water & Sanitation",               "https://www.oxfam.org/en/what-we-do/water-sanitation-and-hygiene"),
    ("Mercy Corps WASH",                        "https://www.mercycorps.org/our-work/water-sanitation-and-hygiene"),
    ("CARE: Water, Sanitation & Hygiene",       "https://www.care.org"),
    ("Rotary: Water & Sanitation Programs",     "https://www.rotary.org/en/our-programs/water-sanitation-hygiene"),
    ("Engineers Without Borders",               "https://www.ewb-usa.org"),
    ("World Vision: Clean Water",               "https://www.worldvision.org"),
    ("Global Water Partnership",                "https://www.gwp.org"),
    ("International Water Association",         "https://iwa-network.org"),
    ("IWMI (CGIAR)",                            "https://www.iwmi.cgiar.org"),
    ("WSUP (Urban Poor WASH)",                  "https://www.wsup.com"),
    ("SIWI (Stockholm Water Inst.)",            "https://www.siwi.org"),
    ("WaterLex",                                "https://www.waterlex.org"),
    ("One Drop",                                "https://www.onedrop.org"),
    ("AWWA (American Water Works Assoc.)",      "https://www.awwa.org"),
    ("UNESCO WWAP",                             "http://www.unesco.org/water/wwap"),
    ("FAO – Water",                             "http://www.fao.org/water"),
    ("ICRC WASH",                               "https://www.icrc.org/en/what-we-do/water-and-hygiene"),
    ("The Nature Conservancy – Freshwater",     "https://www.nature.org/en-us/what-we-do/our-insights/priority-areas/water")
]

def get_random_resources(pool, count: int = 5) -> str:
    n = min(count, len(pool))
    picks = random.sample(pool, k=n)
    return "\n".join(f"- [{name}]({url})" for name, url in picks)

# —————— 6. Multilingual Setup ——————
msgs = {
    "nav_title":      {"English": "Navigation",            "Español": "Navegación"},
    "map":            {"English": "Find Water Nearby",      "Español": "Encontrar Agua Cercana"},
    "help_center":    {"English": "Water Safety Help 💧",   "Español": "Ayuda de Seguridad del Agua 💧"},
    "radius":         {"English": "Distance to Search (km)","Español": "Distancia de Búsqueda (km)"},
    "error_fetch":    {"English": "⚠️ Could not find any locations.", "Español": "⚠️ No se pudieron encontrar ubicaciones."},
    "no_results":     {"English": "No water sources found nearby.",  "Español": "No se encontraron fuentes cercanas."},
    "help_options": {
        "English": ["💡 Water Tips", "🧠 Ask for a Tip", "🏢 Resources"],
        "Español": ["💡 Consejos de Agua", "🧠 Pedir Consejo", "🏢 Recursos"]
    },
    "ask_question_tip": {
        "English": "🔍 What kind of water problem do you have?",
        "Español": "🔍 ¿Qué tipo de problema de agua tienes?"
    },
    "materials_info": {
        "English": "You can find these materials at supermarkets, camping stores, shelters, or community centers.",
        "Español": "Puedes encontrar estos materiales en supermercados, tiendas de campamento, refugios o centros comunitarios."
    },
    "generate_btn": {"English": "🔎 Get Water Tip", "Español": "🔎 Obtener Consejo"},
    "resources_list": {
        "English": get_random_resources(RESOURCE_POOL),
        "Español": get_random_resources(RESOURCE_POOL)
    }
}

# —————— 7. Sidebar & Navigation ——————
language = st.sidebar.selectbox(msgs["nav_title"]["English"], ["English", "Español"])
st.sidebar.title(msgs["nav_title"][language])

page = st.sidebar.radio("", [msgs["map"][language], msgs["help_center"][language]])

# —————— 8. Utility Functions ——————
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

@st.cache_data(show_spinner=False, ttl=3600)
def fetch_water_sources():
    try:
        bbox = (37.20, -122.00, 37.45, -121.70)
        query = f"""
        [out:json];
        node["amenity"="drinking_water"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        out;
        """
        resp = requests.get("http://overpass-api.de/api/interpreter", params={"data": query})
        elements = resp.json().get("elements", [])
        return pd.DataFrame([{
            "lat": el["lat"],
            "lon": el["lon"],
            "name": el.get("tags", {}).get("name", "Drinking Water")
        } for el in elements])
    except:
        return pd.DataFrame(columns=["lat", "lon", "name"])

# —————— 10. Pages ——————
if page == msgs["map"][language]:
    st.header(msgs["map"][language])
    df = fetch_water_sources()
    if df.empty:
        st.error(msgs["error_fetch"][language])
    else:
        center_lat, center_lon = 37.3382, -121.8863
        radius = st.sidebar.slider(msgs["radius"][language], 0.5, 10.0, 5.0, 0.5)
        df["distance_km"] = df.apply(
            lambda r: haversine(center_lat, center_lon, r["lat"], r["lon"]), axis=1
        )
        filtered = df[df["distance_km"] <= radius]
        if filtered.empty:
            st.info(msgs["no_results"][language])
        else:
            view = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=12)
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=filtered,
                get_position=["lon", "lat"],
                get_radius=30,
                radius_scale=3,
                radius_units="pixels",
                radius_min_pixels=1,
                radius_max_pixels=5,
                pickable=True,
                auto_highlight=True,
                get_fill_color=[0, 128, 255, 200],
                cluster=True
            )
            st.pydeck_chart(pdk.Deck(
                layers=[layer],
                initial_view_state=view,
                tooltip={"text": "💧 " + ("Agua Potable" if language=="Español" else "Drinking Water")}
            ))

elif page == msgs["help_center"][language]:
    st.header(msgs["help_center"][language])

    if "current_page" not in st.session_state:
        st.session_state.current_page = ""

    col1, col2, col3 = st.columns(3)
    if col1.button(msgs["help_options"][language][0], key="tips"):
        st.session_state.current_page = "tips"
    if col2.button(msgs["help_options"][language][1], key="generate"):
        st.session_state.current_page = "generate"
    if col3.button(msgs["help_options"][language][2], key="resources"):
        st.session_state.current_page = "resources"

    # — Tips Page —
    if st.session_state.current_page == "tips":
        st.subheader(msgs["ask_question_tip"][language])
        water_color = st.selectbox(
            "Is the water clear or cloudy?" if language=="English" else "¿El agua es clara o turbia?",
            ["Clear", "Cloudy"] if language=="English" else ["Clara", "Turbia"]
        )
        has_smell = st.selectbox(
            "Does the water smell bad?" if language=="English" else "¿El agua huele mal?",
            ["Yes", "No"] if language=="English" else ["Sí", "No"]
        )
        if st.button("💡 Show Water Tip" if language=="English" else "💡 Mostrar Consejo", key="showtip"):
            tip, materials, steps = "", [], []
            if water_color in ("Cloudy","Turbia"):
                tip += "- 🚱 " + ("Water is cloudy: Needs extra boiling." if language=="English"
                                  else "El agua está turbia: Necesita hervirse más tiempo.") + "\n"
                materials.append("Pot or metal container" if language=="English" else "Olla o recipiente metálico")
                steps.append("Boil the water for at least 3 minutes." if language=="English"
                             else "Hierve el agua durante al menos 3 minutos.")
            if has_smell in ("Yes","Sí"):
                tip += "- 🧴 " + ("Water smells bad: Needs filtering." if language=="English"
                                  else "El agua huele mal: Necesita filtración.") + "\n"
                materials.append("Cloth or charcoal filter" if language=="English" else "Tela o filtro de carbón")
                steps.append("Filter water using cloth or available basic water filter." if language=="English"
                             else "Filtra el agua usando una tela limpia o un filtro básico.")
            if not tip:
                tip = "- ✅ " + ("Water looks fine: Still boil for 1 minute before drinking." if language=="English"
                                else "El agua parece estar bien: De todas maneras hiérvela por 1 minuto antes de beber.")
            st.success(tip)
            if materials:
                st.info("🛠️ Materials Needed:\n- " + "\n- ".join(materials))
                st.warning("📋 Steps:\n- " + "\n- ".join(steps))
            st.caption(msgs["materials_info"][language])

    # — Generate GPT Tip Page —
    elif st.session_state.current_page == "generate":
        st.subheader(msgs["generate_btn"][language])
        example_questions = {
            "English": [
                "How do I clean river water to drink?",
                "Is rainwater safe to drink?",
                "How long should I boil water to make it safe?",
                "How to store water safely outdoors?"
            ],
            "Español": [
                "¿Cómo limpiar el agua de un río para beber?",
                "¿Es seguro beber agua de lluvia?",
                "¿Cuánto tiempo debo hervir el agua?",
                "¿Cómo almacenar agua de manera segura al aire libre?"
            ]
        }
        st.write("💬 " + ("Pick an example or ask your own question:" if language=="English"
                          else "Elige un ejemplo o escribe tu propia pregunta:"))
        example = st.selectbox(
            "Example Questions:" if language=="English" else "Preguntas de ejemplo:",
            [""] + example_questions[language]
        )
        user_question = st.text_input(
            "Ask your water safety question:" if language=="English"
            else "Pregunta sobre seguridad del agua:",
            value=example if example else ""
        )
        if user_question and st.button("🔎 Get Water Tip" if language=="English" else "🔎 Obtener Consejo"):
            with st.spinner("Thinking..."):
                try:
                    prompt = f"Answer simply for someone living outdoors: {user_question}"
                    resp = openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role":"user","content":prompt}]
                    )
                    st.success(resp.choices[0].message.content.strip())
                except:
                    st.error("⚠️ Sorry, couldn't generate a tip. Please try again later.")

    # — Resources Page with Refresh Button —
    elif st.session_state.current_page == "resources":
        st.subheader("🏢 " + msgs["help_options"][language][2])

        # initialize on first visit
        if "resources_md" not in st.session_state:
            st.session_state["resources_md"] = get_random_resources(RESOURCE_POOL)

        # allow user to reshuffle
        if st.button("🔄 Refresh Resources"):
            st.session_state["resources_md"] = get_random_resources(RESOURCE_POOL)

        # display the current list
        st.markdown(st.session_state["resources_md"])

# Sidebar logo
LOGO_URL = "https://raw.githubusercontent.com/blam1921/FULL-PROTOTYPE/refs/heads/main/waterwatchlogov2.png"
with st.sidebar:
    st.image(LOGO_URL, width=300)
