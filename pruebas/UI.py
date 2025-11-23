import streamlit as st
import pdfplumber
import pandas as pd
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

# -------------------------------
# 1. CONFIGURACIÓN GENERAL
# -------------------------------
st.set_page_config(page_title="ProcureWatch • AI", layout="wide")

# Inicializar memoria del chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# 2. FUNCIONES (OPTIMIZADAS CON CACHÉ)
# -------------------------------

# ESTA ES LA CLAVE PARA QUE NO SE TRABE
# Guarda el texto en memoria para no volver a leer el PDF a cada rato
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
# 3. BARRA LATERAL (NAVEGACIÓN + CHAT)
# -------------------------------
with st.sidebar:
    st.header("Navigation")
    
    # Mantenemos tu estructura de 3 páginas
    page = st.sidebar.radio(
        "Go to:", 
        ["Dashboard", "Contract Analysis", "External Risk Alerts"]
    )
    
    st.markdown("---")
    st.subheader("🤖 AI Assistant")
    
    # ZONA DE CARGA (En el sidebar para dar contexto siempre)
    uploaded = st.file_uploader("Upload PDF (Context)", type=["pdf"], key="sidebar_uploader")
    
    contract_text = ""
    if uploaded:
        contract_text = extract_text_from_pdf(uploaded) # Usa la función con caché
        st.success("✅ Context Loaded")
    
    # ZONA DE CHAT (En el sidebar)
    # Contenedor para mensajes
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Input del chat
    if prompt := st.chat_input("Ask about the contract..."):
        # 1. Guardar y mostrar
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # 2. Preparar contexto
        if contract_text:
            final_prompt = f"""
            Context (Contract): {contract_text[:3000]}
            User Question: {prompt}
            Answer:
            """
        else:
            final_prompt = f"User Question: {prompt}\nAnswer as a helpful assistant:"

        # 3. Responder
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    response = ask_ibm_watson(final_prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

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
    
    # --- TU PETICIÓN: ÍNDICE INICIA EN 1 ---
    df = pd.DataFrame([
        {"Supplier": "Cement Quebec", "Status": "Critical Risk", "Value": "$120k"},
        {"Supplier": "Germany Alum", "Status": "Safe", "Value": "$85k"},
        {"Supplier": "Montreal Steel", "Status": "Review", "Value": "$200k"},
    ])
    
    df.index = df.index + 1  # <--- AQUÍ ESTÁ EL CAMBIO
    
    st.dataframe(df, use_container_width=True)

# ==============================================================
# PÁGINA 2: ANÁLISIS (DETALLES)
# ==============================================================
elif page == "Contract Analysis":
    st.header("📘 Contract Details")
    
    if contract_text:
        st.success("PDF Content is ready for analysis.")
        
        # Opciones extra de análisis (Json, Resumen)
        col_btn1, col_btn2 = st.columns(2)
        
        if col_btn1.button("📄 Generate Summary"):
            with st.spinner("Summarizing..."):
                prompt_sum = f"Summarize this contract in 3 sentences:\n{contract_text[:3000]}"
                st.info(ask_ibm_watson(prompt_sum))
                
        if col_btn2.button("⚠️ Detect Risks (JSON)"):
            with st.spinner("Detecting..."):
                prompt_json = f"Extract risks in JSON format from:\n{contract_text[:3000]}"
                st.code(ask_ibm_watson(prompt_json), language="json")
                
        with st.expander("View Full Text"):
            st.text(contract_text)
    else:
        st.info("Please upload a PDF in the Sidebar 👈 to start analyzing.")

# ==============================================================
# PÁGINA 3: NOTICIAS (EXTERNAL ALERTS)
# ==============================================================
elif page == "External Risk Alerts":
    st.header("🌐 Global Supply Chain Alerts")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search news (Simulated):", "construction materials")
    with col2:
        st.write("") 
        st.write("") 
        search_btn = st.button("Search News")
    
    if search_btn or query:
        st.markdown(f"**Latest updates for:** `{query}`")
        st.markdown("---")
        
        st.subheader("Strike at Montreal Port affects cement logistics")
        st.caption("Source: Logistics Daily • 2 hours ago")
        st.error("🔴 High Impact")
        
        st.markdown("---")
        
        st.subheader("Aluminum price stabilizes in EU market")
        st.caption("Source: Global Trade • 5 hours ago")
        st.success("🟢 Low Impact")
