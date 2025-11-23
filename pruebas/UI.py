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

# Inicializar memoria del chat si no existe
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
# 3. BARRA LATERAL
# -------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to:", ["Dashboard", "Contract Analysis & Chat"])
st.sidebar.markdown("---")
st.sidebar.info("💡 Tip: Upload a PDF to start chatting with it.")

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
    ]), use_container_width=True)

# ==============================================================
# PÁGINA 2: ANÁLISIS Y CHAT (INTERACTIVO)
# ==============================================================
elif page == "Contract Analysis & Chat":
    st.header("📘 Interactive Contract Monitor")

    uploaded = st.file_uploader("1. Upload Contract (PDF)", type=["pdf"])

    # Si se sube un archivo, extraemos el texto y lo guardamos en memoria
    if uploaded:
        if st.session_state.contract_text == "":
            with pdfplumber.open(uploaded) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                st.session_state.contract_text = text # Guardar en memoria
            st.success("✅ PDF processed! You can now chat with this document.")

    # Mostrar contenido solo si hay texto procesado
    if st.session_state.contract_text:
        
        # --- SECCIÓN A: RESUMEN AUTOMÁTICO ---
        with st.expander("📄 View Contract Text & Auto-Analysis"):
            st.text(st.session_state.contract_text[:1000] + "...")
            
            if st.button("Generate Risk Report (JSON)"):
                with st.spinner("Analyzing..."):
                    # Prompt específico para JSON
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

        # --- SECCIÓN B: CHAT INTERACTIVO (LO NUEVO) ---
        
        # 1. Mostrar historial de mensajes
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # 2. Campo de entrada del usuario
        if prompt := st.chat_input("Ask something about the contract..."):
            
            # Guardar y mostrar mensaje del usuario
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # 3. Generar respuesta con IBM
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("Thinking...")
                
                # Crear el prompt conversacional
                chat_prompt = f"""
                Act as a legal assistant. Answer the question based strictly on the contract text provided below.
                
                Contract Text:
                {st.session_state.contract_text[:4000]}
                
                User Question: {prompt}
                
                Answer:
                """
                
                # Llamar a la API
                full_response = ask_ibm_watson(chat_prompt)
                
                # Mostrar y guardar respuesta
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})

    else:
        st.info("Please upload a PDF to start the analysis.")
