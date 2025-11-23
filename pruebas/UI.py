import streamlit as st
import pdfplumber
import pandas as pd
import json
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

# -------------------------------
# 1. CONFIGURACIÓN GENERAL
# -------------------------------
st.set_page_config(
    page_title="ProcureWatch • Contract AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📑 ProcureWatch")
st.markdown("### Interactive Contract Analysis System")

# Inicializar memoria del chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Inicializar memoria del texto del contrato
if "contract_text" not in st.session_state:
    st.session_state.contract_text = ""

# -------------------------------
# 2. LÓGICA DE CONEXIÓN CON IBM (BACKEND)
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
        GenParams.MAX_NEW_TOKENS: 400,
        GenParams.MIN_NEW_TOKENS: 1,
        GenParams.REPETITION_PENALTY: 1.1
    }

    try:
        model = Model(model_id=model_id, params=parameters, credentials=creds, project_id=project_id)
        response = model.generate_text(prompt=prompt_text)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------
# 3. HELPER: Etiqueta de Riesgo
# -------------------------------
def risk_badge(level):
    if level == "High":
        st.error("🔴 High Risk")
    elif level == "Medium":
        st.warning("🟠 Medium Risk")
    elif level == "Low":
        st.success("🟢 Low Risk")

# -------------------------------
# 4. BARRA LATERAL (NAVEGACIÓN)
# -------------------------------
st.sidebar.header("Navigation")
# AQUÍ AGREGUÉ DE NUEVO LAS 3 OPCIONES
page = st.sidebar.radio(
    "Go to:",
    ["Dashboard", "Contract Analysis & Chat", "External Risk Alerts"]
)
st.sidebar.markdown("---")
st.sidebar.info("💡 Select 'Contract Analysis' to use the AI Chat.")

# ==============================================================
# PÁGINA 1: DASHBOARD
# ==============================================================
if page == "Dashboard":
    st.header("📊 Procurement Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Contracts Analyzed", "15")
    col2.metric("High Risk Detected", "3", "Warning", delta_color="inverse")
    col3.metric("Pending Review", "7")
    
    st.markdown("---")
    st.dataframe(pd.DataFrame([
        {"Supplier": "Cement Quebec", "Status": "Critical Risk", "Value": "$120k"},
        {"Supplier": "Germany Alum", "Status": "Safe", "Value": "$85k"},
        {"Supplier": "Montreal Steel", "Status": "Review", "Value": "$200k"},
    ]), use_container_width=True)

# ==============================================================
# PÁGINA 2: ANÁLISIS Y CHAT (AQUÍ ESTÁ LO QUE BUSCAS)
# ==============================================================
elif page == "Contract Analysis & Chat":
    st.header("📘 Interactive Contract Monitor")

    uploaded = st.file_uploader("1. Upload Contract (PDF)", type=["pdf"])

    if uploaded:
        if st.session_state.contract_text == "":
            with pdfplumber.open(uploaded) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                st.session_state.contract_text = text
            st.success("✅ PDF processed! Scroll down to chat.")

    if st.session_state.contract_text:
        
        # --- PARTE A: ANÁLISIS RÁPIDO ---
        with st.expander("📄 View Contract Text & Auto-Analysis"):
            st.text(st.session_state.contract_text[:1000] + "...")
            
            if st.button("Generate Risk Report (JSON)"):
                with st.spinner("Analyzing..."):
                    json_prompt = f"""
                    Analyze this contract and output ONLY JSON:
                    {{ "supplier": "name", "risk": "High/Low", "summary": "short summary" }}
                    Text: {st.session_state.contract_text[:3000]}
                    Output JSON:
                    """
                    analysis = ask_ibm_watson(json_prompt)
                    st.code(analysis, language="json")

        st.markdown("---")
        st.subheader("💬 Chat with your Contract")
        st.caption("Ask questions like: 'What is the payment term?' or 'Is there a penalty clause?'")

        # --- PARTE B: CHAT INTERACTIVO ---
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask something about the contract..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("Thinking...")
                
                chat_prompt = f"""
                Act as a legal assistant. Answer based strictly on the contract text below.
                Contract Text: {st.session_state.contract_text[:4000]}
                User Question: {prompt}
                Answer:
                """
                full_response = ask_ibm_watson(chat_prompt)
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
    else:
        st.info("Please upload a PDF to start the chat.")

# ==============================================================
# PÁGINA 3: NOTICIAS (YA LA PUSE OTRA VEZ)
# ==============================================================
elif page == "External Risk Alerts":
    st.header("🌐 Global Supply Chain Alerts")
    
    query = st.text_input("Search news (Simulated):", "construction materials")
    
    if st.button("Search"):
        st.write(f"Searching for: **{query}**...")
        st.markdown("---")
        
        st.subheader("Strike at Montreal Port affects cement logistics")
        st.caption("Source: Logistics Daily • 2 hours ago")
        st.error("🔴 High Impact")
        st.write("Potential delay of 2-3 weeks for incoming shipments.")
        
        st.markdown("---")
        
        st.subheader("Aluminum price stabilizes in EU market")
        st.caption("Source: Global Trade • 5 hours ago")
        st.success("🟢 Low Impact")
