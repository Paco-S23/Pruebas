import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ============================
# Configuración
# ============================
API_KEY = os.getenv("WATSONX_APIKEY")
PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
AGENT_1_ID = os.getenv("AGENT_1_ID")
AGENT_2_ID = os.getenv("AGENT_2_ID")

BASE_URL = "https://us-south.ml.cloud.ibm.com"
TOKEN_URL = f"{BASE_URL}/v1/authorize"
AGENT_URL = f"{BASE_URL}/watsonx/agents/v1/agent_runs"

# ============================
# Función para obtener token
# ============================
def get_token():
    headers = {"Content-Type": "application/json"}
    payload = {"apikey": API_KEY, "grant_type": "urn:ibm:params:oauth:grant-type:apikey"}

    res = requests.post(TOKEN_URL, json=payload, headers=headers)
    if res.status_code != 200:
        return None
    return res.json().get("access_token", None)

# ============================
# Función para enviar mensaje
# ============================
def call_agent(agent_id, user_message):
    token = get_token()
    if token is None:
        return "❌ Error: No se pudo obtener token."

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "agent_id": agent_id,
        "project_id": PROJECT_ID,
        "input": {
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
    }

    res = requests.post(AGENT_URL, headers=headers, json=payload)

    if res.status_code != 200:
        return f"❌ Error en la API: {res.text}"

    data = res.json()
    try:
        return data["output"]["messages"][0]["content"]
    except:
        return "❌ Error procesando respuesta."


# =========================================================
# INTERFAZ — SIN SIDEBAR y solo 2 pestañas
# =========================================================
st.set_page_config(page_title="Agentes IBM", layout="centered")

st.title("🤖 IBM Watsonx — Agentes")
st.write("Interactúa con tus agentes de forma rápida y sencilla.")

tabs = st.tabs(["Agente 1", "Agente 2"])

# ------------------------
# Pestaña Agente 1
# ------------------------
with tabs[0]:
    st.subheader("Agente 1")

    msg1 = st.text_area("Escribe tu consulta:", key="msg1")

    if st.button("Enviar al Agente 1"):
        if msg1.strip() == "":
            st.warning("Escribe un mensaje primero.")
        else:
            respuesta = call_agent(AGENT_1_ID, msg1)
            st.write("### Respuesta:")
            st.write(respuesta)

# ------------------------
# Pestaña Agente 2
# ------------------------
with tabs[1]:
    st.subheader("Agente 2")

    msg2 = st.text_area("Escribe tu consulta:", key="msg2")

    if st.button("Enviar al Agente 2"):
        if msg2.strip() == "":
            st.warning("Escribe un mensaje primero.")
        else:
            respuesta = call_agent(AGENT_2_ID, msg2)
            st.write("### Respuesta:")
            st.write(respuesta)
