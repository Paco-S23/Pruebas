import streamlit as st
import pdfplumber
import pandas as pd
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

# -------------------------------
# 1. CONFIGURACIÓN
# -------------------------------
st.set_page_config(page_title="ProcureWatch • AI", layout="wide")

# Inicializar memoria
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# 2. FUNCIONES (OPTIMIZADAS)
# -------------------------------
@st.cache_data
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    return text

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
        return model.generate_text(prompt=prompt_text)
    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------
# 3. BARRA LATERAL (CHAT GLOBAL + UPLOADER)
# -------------------------------
with st.sidebar:
    st.title("📑 ProcureWatch")
    st.caption("AI Supply Chain Monitor")
    
    st.markdown("---")
    
    # --- A. CARGA DE ARCHIVO ---
    uploaded = st.file_uploader("Upload Context (PDF)", type=["pdf"], key="sidebar_uploader")
    
    contract_text = ""
    if uploaded:
        contract_text = extract_text_from_pdf(uploaded)
        st.success("✅ Context Active")
    
    st.markdown("---")
    
    # --- B. AI ASSISTANT (CHAT) ---
    col_title, col_btn = st.columns([2,1])
    with col_title:
        st.subheader("🤖 Chat")
    with col_btn:
        # BOTÓN PARA BORRAR COMENTARIOS
        if st.button("🗑️ Clear", type="primary"):
            st.session_state.messages = []
            st.rerun()
    
    # Chat History Container
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.info("👋 Hi! I'm ready to help.")
            
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Input del Chat
    if prompt := st.chat_input("Ask AI..."):
        # 1. Guardar
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # 2. Prompt
        if contract_text:
            final_prompt = f"Context: {contract_text[:3000]}\nQuestion: {prompt}\nAnswer:"
        else:
            final_prompt = f"
