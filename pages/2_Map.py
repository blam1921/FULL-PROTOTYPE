import streamlit as st

# 🔒 Consent check FIRST
if "consent_given" not in st.session_state or not st.session_state.consent_given:
    st.error("❌ Consent is required to use this app. Please return to the homepage.")
    st.stop()

# ✅ After consent check, import everything else
import openai
import pandas as pd
import pydeck as pdk
import requests
import math
import os

LOGO_URL = "https://raw.githubusercontent.com/blam1921/FULL-PROTOTYPE/refs/heads/main/waterwatchlogov2.png"
    
# OpenAI Key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Page Setup
st.set_page_config(
    page_title="Water Access Support",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
  st.image(LOGO_URL, width=300)

# Multilingual Setup
msgs = {
    "nav_title": {"English": "Navigation", "Español": "Navegación"},
    "map": {"English": "Map", "Español": "Mapa"},
    "tips": {"English": "Water Sanitation Tips", "Español": "Consejos de Saneamiento del Agua"},
    "generate": {"English": "Generate Water Safety Tip", "Español": "Generar Consejo de Seguridad del Agua"},
    "resources": {"English": "Water Help Resources", "Español": "Recursos de Ayuda con Agua"},
    "report": {"English": "Report an Issue", "Español": "Reportar un Problema"},
    "report_placeholder": {"English": "Describe the issue...", "Español": "Describe el problema..."},
    "submit": {"English": "Submit", "Español": "Enviar"},
    "radius": {"English": "Radius (km)", "Español": "Radio (km)"},
    "lang_label": {"English": "🌐 Choose language / Elige idioma", "Español": "🌐 Elige idioma / Choose language"},
    "tips_list": {
        "English": """
- Boil water for at least **1 minute** to kill bacteria.
- Let the water cool before drinking.
- Use a cloth to filter out large particles.
- If you have a water filter, clean it regularly.
""",
        "Español": """
- Hierve el agua durante al menos **1 minuto** para eliminar bacterias.
- Deja que el agua se enfríe antes de beberla.
- Usa un paño limpio para filtrar partículas grandes.
- Si tienes un filtro de agua, límpialo con frecuencia.
"""
    },
    "resources_list": {
        "English": """
- [Downtown Streets Team](https://www.streetsteam.org/)
- [Sacred Heart Community Service](https://sacredheartcs.org/)
- [Water.org](https://water.org)
""",
        "Español": """
- [Downtown Streets Team](https://www.streetsteam.org/)
- [Sacred Heart Community Service](https://sacredheartcs.org/)
- [Water.org](https://water.org)
"""
    },
    "generate_prompt": {
        "English": "Give me step-by-step instructions for making dirty water safe to drink.",
        "Español": "Explica paso a paso cómo hacer que el agua contaminada sea segura para beber en español."
    },
    "generate_btn": {"English": "🔄 Generate Tip", "Español": "🔄 Generar Consejo"},
    "error_fetch": {"English": "⚠️ Could not fetch locations.", "Español": "⚠️ No se pudieron obtener ubicaciones."},
    "no_results": {"English": "No sources found within the selected radius.", "Español": "No se encontraron fuentes dentro del radio seleccionado."},
    "thanks_report": {"English": "Thanks for your feedback!", "Español": "¡Gracias por tus comentarios!"}
}

# 🌟 Only show sidebar menu if consent was given
language = st.sidebar.selectbox(
    msgs["lang_label"]["English"],
    ["English", "Español"]
)

st.sidebar.title(msgs["nav_title"][language])

page = st.sidebar.radio(
    "",
    [
        msgs["map"][language],
        msgs["tips"][language],
        msgs["generate"][language],
        msgs["resources"][language],
        msgs["report"][language]
    ]
)

# Utilities
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

@st.cache_data(show_spinner=False)
def fetch_water_sources():
    try:
        # Overpass API: drinking_water nodes in San José bbox
        bbox = (37.20, -122.00, 37.45, -121.70)
        query = f"""
        [out:json];
        node["amenity"="drinking_water"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
        out;
        """
        resp = requests.get("http://overpass-api.de/api/interpreter", params={"data": query})
        elements = resp.json().get("elements", [])
        df = pd.DataFrame([{
            "lat": el["lat"],
            "lon": el["lon"],
            "name": el.get("tags", {}).get("name", "Drinking Water")
        } for el in elements])
        return df
    except:
        return pd.DataFrame(columns=["lat","lon","name"])

# Pages
if page == msgs["map"][language]:
    st.header(msgs["map"][language])
    df = fetch_water_sources()
    if df.empty:
        st.error(msgs["error_fetch"][language])
    else:
        center_lat, center_lon = 37.3382, -121.8863
        radius = st.sidebar.slider(
            msgs["radius"][language], 0.5, 10.0, 5.0, 0.5
        )
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
                get_radius=50,
                pickable=True,
                auto_highlight=True,
                radius_scale=20,
                radius_min_pixels=5,
                radius_max_pixels=30,
                get_fill_color=[0, 128, 255, 200],
                cluster=True
            )
            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view,
                tooltip={"text": "{name}"}
            )
            st.pydeck_chart(deck)

elif page == msgs["tips"][language]:
    st.header(msgs["tips"][language])
    st.markdown(msgs["tips_list"][language])

elif page == msgs["generate"][language]:
    st.header(msgs["generate"][language])
    if st.button(msgs["generate_btn"][language]):
        with st.spinner("Thinking..."):
            try:
                resp = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": msgs["generate_prompt"][language]}]
                )
                st.success(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"⚠️ {e}")

elif page == msgs["resources"][language]:
    st.header(msgs["resources"][language])
    st.markdown(msgs["resources_list"][language])

elif page == msgs["report"][language]:
    st.header(msgs["report"][language])
    feedback = st.text_area(msgs["report_placeholder"][language])
    if st.button(msgs["submit"][language]):
        st.success(msgs["thanks_report"][language])
