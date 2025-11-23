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
st.markdown("### Contract Analysis & General AI Assistant")

# Inicializar memoria
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
# BARRA LATERAL
# -------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to:", ["Dashboard", "AI Chat & Analysis"])
st.sidebar.markdown("---")

if st.session_state.contract_text:
    st.sidebar.success("📄 Contract Loaded in Memory")
    if st.sidebar.button("🗑️ Clear Contract"):
        st.session_state.contract_text = ""
        st.experimental_rerun()
else:
    st.sidebar.info("Upload a PDF to enable contract analysis mode.")

# ==============================================================
# PÁGINA 1: DASHBOARD
# ==============================================================
if page == "Dashboard":
    st.header("📊 Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Contracts", "15")
    col2.metric("Risks", "3", "High")
    col3.metric("Pending", "7")

# ==============================================================
# PÁGINA 2: CHAT GENERAL Y ANÁLISIS
# ==============================================================
elif page == "AI Chat & Analysis":
    
    # 1. ZONA DE CARGA (Opcional)
    with st.expander("📂 Upload Contract (Optional)", expanded=not st.session_state.contract_text):
        uploaded = st.file_uploader("Upload PDF", type=["pdf"])
        if uploaded:
            with pdfplumber.open(uploaded) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
                st.session_state.contract_text = text
            st.success("PDF processed! The AI now knows the context of this document.")

    # 2. CHATBOT (Funciona siempre)
    st.subheader("💬 AI Assistant")
    
    # Mostrar historial
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input del usuario
    if prompt := st.chat_input("Ask about the contract or anything else..."):
        # Guardar usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generar respuesta
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                
                # LÓGICA HÍBRIDA:
                # Si hay contrato, lo metemos en el prompt. Si no, es chat general.
                if st.session_state.contract_text:
                    final_prompt = f"""
                    Context (Contract Text):
                    {st.session_state.contract_text[:4000]}
                    
                    User Question: {prompt}
                    
                    Instruction: Answer based on the contract if relevant. If the question is general, answer using your general knowledge.
                    Answer:
                    """
                else:
                    final_prompt = f"""
                    Act as a helpful AI assistant for procurement and business.
                    User Question: {prompt}
                    Answer:
                    """

                response = ask_ibm_watson(final_prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
