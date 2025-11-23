import streamlit as st
import pdfplumber
import pandas as pd
import json
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

# -------------------------------
# CONFIGURACIÓN GENERAL
# -------------------------------
st.set_page_config(page_title="ProcureWatch • AI", layout="wide")

st.title("📑 ProcureWatch")
st.markdown("### Contract Analysis & Supply Chain Monitor")

# Inicializar memorias
if "messages" not in st.session_state:
    st.session_state.messages = []
if "contract_text" not in st.session_state:
    st.session_state.contract_text = ""

# -------------------------------
# BACKEND IBM WATSON
# -------------------------------
def ask_ibm_watson(prompt_text):
    creds = {
        "url": "https://us-south.ml.cloud.ibm.com",
        "apikey": "7df1e07ee763823210cc7609513c0c6fe4ff613cc3583613def0ec12f2570a17"
    }
    project_id = "077c11a6-2c5e-4c89-9a99-c08df3cb67ff"
    model_id = "ibm/granite-13b-chat-v2"
    
    parameters = {
        GenParams.DECODING_METHOD: "greedy",
        GenParams.MAX_NEW_TOKENS: 500,
        GenParams.MIN_NEW_TOKENS: 1,
        GenParams.REPETITION_PENALTY: 1.1
    }

    try:
        model = Model(model_id=model_id, params=parameters, credentials=creds, project_id=project_id)
        return model.generate_text(prompt=prompt_text)
    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------
# BARRA LATERAL (NAVEGACIÓN)
# -------------------------------
st.sidebar.header("Navigation")

# AQUÍ ESTÁN LAS 3 OPCIONES
page = st.sidebar.radio(
    "Go to:", 
    ["Dashboard", "AI Chat & Analysis", "External Risk Alerts"]
)

st.sidebar.markdown("---")

# Indicador de estado del contrato
if st.session_state.contract_text:
    st.sidebar.success("📄 Contract Loaded")
    if st.sidebar.button("🗑️ Unload Contract"):
        st.session_state.contract_text = ""
        st.rerun()

# ==============================================================
# PÁGINA 1: DASHBOARD
# ==============================================================
if page == "Dashboard":
    st.header("📊 Procurement Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Contracts", "15")
    col2.metric("High Risk", "3", "Warning", delta_color="inverse")
    col3.metric("Pending", "7")
    
    st.markdown("---")
    st.subheader("Active Contracts")
    st.dataframe(pd.DataFrame([
        {"Supplier": "Cement Quebec", "Status": "Critical Risk", "Value": "$120k"},
        {"Supplier": "Germany Alum", "Status": "Safe", "Value": "$85k"},
        {"Supplier": "Montreal Steel", "Status": "Review", "Value": "$200k"},
    ]), use_container_width=True)

# ==============================================================
# PÁGINA 2: CHAT GENERAL Y ANÁLISIS
# ==============================================================
elif page == "AI Chat & Analysis":
    
    # 1. ZONA DE CARGA (Opcional, se colapsa si ya cargaste algo)
    with st.expander("📂 Upload Contract (Optional for context)", expanded=not st.session_state.contract_text):
        uploaded = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded:
            with pdfplumber.open(uploaded) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                st.session_state.contract_text = text
            st.success("PDF processed! The AI is now context-aware.")
            st.rerun()

    # 2. CHATBOT INTERACTIVO
    st.subheader("💬 AI Assistant")
    
    # Mostrar historial
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input del usuario
    if prompt := st.chat_input("Ask about the contract or anything else..."):
        # Guardar mensaje usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                
                # LÓGICA HÍBRIDA:
                if st.session_state.contract_text:
                    final_prompt = f"""
                    Context (Contract Text):
                    {st.session_state.contract_text[:4000]}
                    
                    User Question: {prompt}
                    
                    Instruction: Answer based on the contract if relevant. If not, answer generally.
                    Answer:
                    """
                else:
                    final_prompt = f"""
                    Act as a supply chain expert AI.
                    User Question: {prompt}
                    Answer:
                    """

                response = ask_ibm_watson(final_prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

# ==============================================================
# PÁGINA 3: NOTICIAS (EXTERNAL ALERTS) - ¡AQUÍ ESTÁ!
# ==============================================================
elif page == "External Risk Alerts":
    st.header("🌐 Global Supply Chain Alerts")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search news (Simulated):", "construction materials")
    with col2:
        st.write("") # Espacio
        st.write("") 
        search_btn = st.button("Search News")
    
    if search_btn or query:
        st.markdown(f"**Latest updates for:** `{query}`")
        st.markdown("---")
        
        # Noticia 1
        st.subheader("Strike at Montreal Port affects cement logistics")
        st.caption("Source: Logistics Daily • 2 hours ago")
        st.error("🔴 High Impact")
        st.write("Potential delay of 2-3 weeks for incoming shipments due to union strikes.")
        
        st.markdown("---")
        
        # Noticia 2
        st.subheader("Aluminum price stabilizes in EU market")
        st.caption("Source: Global Trade • 5 hours ago")
        st.success("🟢 Low Impact")
        st.write("Prices have normalized after last month's volatility.")

        st.markdown("---")

        # Noticia 3
        st.subheader("New regulations for steel imports in Mexico")
        st.caption("Source: Business World • 1 day ago")
        st.warning("🟠 Medium Impact")
        st.write("New tariffs may affect cost projection for Q1 2026.")
