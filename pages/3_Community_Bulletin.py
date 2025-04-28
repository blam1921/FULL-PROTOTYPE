import streamlit as st
import os
import requests
from datetime import datetime, timedelta
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from openai import OpenAI
import ast

# Check user consent
if "consent_given" not in st.session_state or not st.session_state.consent_given:
    st.error("❌ Consent is required to use this app. Please return to the homepage.")
    st.stop()

# Logo
LOGO_URL = "https://raw.githubusercontent.com/blam1921/FULL-PROTOTYPE/refs/heads/main/waterwatchlogov2.png"
with st.sidebar:
    st.image(LOGO_URL, width=300)

# Language selection
language = st.sidebar.selectbox("Language / Idioma", ["English", "Español"])

# Multilingual messages
msgs = {
    "title": {"English": "💧 Community Bulletin System", "Español": "💧 Sistema de Boletines Comunitarios"},
    "caption_main": {"English": "Manage and send notifications for water, meals, showers, and clinics.",
                     "Español": "Gestiona y envía notificaciones sobre agua, comidas, duchas y clínicas."},
    "add_new": {"English": "➕ Add New Resource", "Español": "➕ Agregar Nuevo Recurso"},
    "type_resource": {"English": "Type of Resource", "Español": "Tipo de Recurso"},
    "location_name": {"English": "Location Name", "Español": "Nombre del Lugar"},
    "address": {"English": "Address", "Español": "Dirección"},
    "hours": {"English": "Hours Available (e.g., 9AM - 6PM)", "Español": "Horario Disponible (ej. 9AM - 6PM)"},
    "timer": {"English": "Select Timer Duration (Minutes)", "Español": "Selecciona Duración del Temporizador (Minutos)"},
    "autofill": {"English": "Autofill Coordinates with Address", "Español": "Autocompletar Coordenadas con Dirección"},
    "generate": {"English": "Generate Message", "Español": "Generar Mensaje"},
    "coordinates_found": {"English": "📍 Coordinates found:", "Español": "📍 Coordenadas encontradas:"},
    "no_coordinates": {"English": "No coordinates found for the provided address.", "Español": "No se encontraron coordenadas para la dirección proporcionada."},
    "error_coordinates": {"English": "Could not find coordinates. Check the address or try again:", "Español": "No se pudieron encontrar coordenadas. Verifica la dirección o inténtalo de nuevo:"},
    "success_message": {"English": "✅ Message generated and submitted successfully!", "Español": "✅ ¡Mensaje generado y enviado exitosamente!"},
    "error_message": {"English": "Error generating alert:", "Español": "Error al generar la alerta:"},
    "no_openai_key": {"English": "❌ OpenAI API key not set. Cannot generate message.", "Español": "❌ Clave de API de OpenAI no configurada. No se puede generar el mensaje."},
    "community_announcements": {"English": "📋 Community Announcements", "Español": "📋 Anuncios Comunitarios"},
    "safety_note": {"English": "⚠️ Please use caution when visiting any resource shared here. Ensure your safety by verifying details and being mindful of the source of the information.",
                    "Español": "⚠️ Usa precaución al visitar cualquier recurso compartido aquí. Verifica los detalles y ten cuidado con la fuente de información."},
    "filter": {"English": "Filter by Type", "Español": "Filtrar por Tipo"},
    "resource_type": {"English": "**Resource Type:**", "Español": "**Tipo de Recurso:**"},
    "location": {"English": "**Location Name:**", "Español": "**Nombre del Lugar:**"},
    "address_field": {"English": "**Address:**", "Español": "**Dirección:**"},
    "hours_field": {"English": "**Hours Available:**", "Español": "**Horario Disponible:**"},
    "created_at": {"English": "**Created At:**", "Español": "**Creado el:**"},
    "time_remaining": {"English": "🕒 **Time Remaining:**", "Español": "🕒 **Tiempo Restante:**"},
    "expired_message": {"English": "❌ This message has expired and will be removed shortly.", "Español": "❌ Este mensaje ha expirado y será eliminado pronto."},
    "coordinates": {"English": "**Coordinates:**", "Español": "**Coordenadas:**"},
    "no_alerts": {"English": "No alerts to display.", "Español": "No hay alertas para mostrar."},
    "download_bulletin": {"English": "📥 Download Bulletin as Text File", "Español": "📥 Descargar Boletín como Archivo de Texto"},
}

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENCAGE_API_KEY = os.getenv('OPENCAGE_API_KEY')
client = OpenAI()

# Google Sheets Setup
SHEET_NAME = "alerts"
conn = st.connection("gsheets", type=GSheetsConnection)
ALERT_EXPIRATION_HOURS = 48
coords = None

def load_data():
    data = conn.read(worksheet=SHEET_NAME, ttl=5)
    data = data.dropna(how="all")
    now = datetime.now()
    if not data.empty:
        data['timestamp_dt'] = pd.to_datetime(data['timestamp'])
        not_expired = data['timestamp_dt'] + timedelta(hours=ALERT_EXPIRATION_HOURS) > now
        expired = data[~not_expired]
        if not expired.empty:
            data = data[not_expired].drop(columns=["timestamp_dt"])
            conn.update(worksheet=SHEET_NAME, data=data)
        else:
            data = data.drop(columns=["timestamp_dt"])
    return data

alerts = load_data()

# App Interface
st.title(msgs["title"][language])
st.caption(msgs["caption_main"][language])

st.header(msgs["add_new"][language])
with st.form(key='resource_form'):
    resource_type = st.selectbox(msgs["type_resource"][language], ["Water Station", "Free Meal", "Shower", "Health Clinic"])
    location_name = st.text_input(msgs["location_name"][language])
    address = st.text_input(msgs["address"][language])
    hours = st.text_input(msgs["hours"][language])
    timer_duration = st.selectbox(msgs["timer"][language], [1,5,10,15,30,60,120], index=4)
    geocode_button = st.form_submit_button(msgs["autofill"][language])
    submit_button = st.form_submit_button(label=msgs["generate"][language])

# Autofill Coordinates
if address and OPENCAGE_API_KEY:
    try:
        geo_url = f"https://api.opencagedata.com/geocode/v1/json?q={address}&key={OPENCAGE_API_KEY}"
        geo_response = requests.get(geo_url).json()
        if geo_response['results']:
            coords = geo_response['results'][0]['geometry']
            st.success(f"{msgs['coordinates_found'][language]} {coords['lat']}, {coords['lng']}")
        else:
            st.error(msgs["no_coordinates"][language])
    except Exception as e:
        st.error(f"{msgs['error_coordinates'][language]} {e}")

# Submit Resource
if submit_button:
    if client:
        prompt = f"You are helping homeless users find resources. Write a very short, friendly SMS-style alert about a new {resource_type} available at {location_name}, {address}. It is available {hours}. Keep it positive and encouraging."
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You write short, friendly community alerts."},
                          {"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            message = response.choices[0].message.content.strip()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            expiration_time = datetime.now() + timedelta(minutes=timer_duration)

            alert = {
                "timestamp": timestamp,
                "type": resource_type,
                "message": message,
                "location_name": location_name,
                "address": address,
                "coordinates": coords,
                "hours": hours,
                "expiration_time": expiration_time.strftime("%Y-%m-%d %H:%M")
            }
            updated_alerts = pd.concat([alerts, pd.DataFrame([alert])], ignore_index=True)
            conn.update(worksheet=SHEET_NAME, data=updated_alerts)

            st.success(msgs["success_message"][language])
            st.info(message)

            if coords:
                st.map([{"lat": coords['lat'], "lon": coords['lng']}])

        except Exception as e:
            st.error(f"{msgs['error_message'][language]} {e}")
    else:
        st.error(msgs["no_openai_key"][language])

st.divider()

# Community Announcements
st.header(msgs["community_announcements"][language])
st.caption(msgs["safety_note"][language])

filter_type = st.selectbox(msgs["filter"][language], ["All", "Water Station", "Free Meal", "Shower", "Health Clinic"])
alerts_dicts = alerts.to_dict(orient="records")

filtered_alerts = [alert for alert in alerts_dicts if filter_type == "All" or alert["type"] == filter_type]

if filtered_alerts:
    for idx, alert in enumerate(filtered_alerts, 1):
        with st.expander(f"🔔 {idx}. {alert['message']}"):
            st.markdown(f"{msgs['resource_type'][language]} {alert['type']}")
            st.markdown(f"{msgs['location'][language]} {alert['location_name']}")
            st.markdown(f"{msgs['address_field'][language]} {alert['address']}")
            st.markdown(f"{msgs['hours_field'][language]} {alert['hours']}")
            st.markdown(f"{msgs['created_at'][language]} {alert['timestamp']}")

            expiration_time = datetime.strptime(alert['expiration_time'], "%Y-%m-%d %H:%M")
            time_left = expiration_time - datetime.now()
            if time_left.total_seconds() > 0:
                st.markdown(f"{msgs['time_remaining'][language]} {str(time_left).split('.')[0]}")
            else:
                st.markdown(msgs["expired_message"][language])

            if alert.get('coordinates'):
                coords = alert['coordinates']
                if isinstance(coords, str):
                    try:
                        coords = ast.literal_eval(coords)
                    except Exception as e:
                        st.error(f"Error parsing coordinates: {e}")
                        coords = None

                if coords and isinstance(coords, dict) and 'lat' in coords and 'lng' in coords:
                    google_maps_url = f"https://www.google.com/maps?q={coords['lat']},{coords['lng']}"
                    st.markdown(f"{msgs['coordinates'][language]} [Latitude: {coords['lat']}, Longitude: {coords['lng']}]({google_maps_url})", unsafe_allow_html=True)
                    st.map([{"lat": coords['lat'], "lon": coords['lng']}])
else:
    st.info(msgs["no_alerts"][language])

st.download_button(
    label=msgs["download_bulletin"][language],
    data="\n\n".join([a["message"] for a in alerts_dicts]),
    file_name="alerts.txt",
    mime="text/plain"
)
