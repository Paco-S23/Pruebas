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
    
    # --- A. CARGA DE ARCHIVO (Contexto Global) ---
    uploaded = st.file_uploader("Upload Context (PDF)", type=["pdf"], key="sidebar_uploader")
    
    contract_text = ""
    if uploaded:
        contract_text = extract_text_from_pdf(uploaded)
        st.success("✅ Context Active")
    
    st.markdown("---")
    
    # --- B. AI ASSISTANT (CHAT) ---
    st.subheader("🤖 AI Assistant")
    
    # Chat History Container
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Input del Chat (Se ancla al fondo)
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
            final_prompt = f"Question: {prompt}\nAnswer as expert:"

        # 3. Respuesta
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    response = ask_ibm_watson(final_prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

# -------------------------------
# 4. ÁREA PRINCIPAL CON PESTAÑAS (TABS)
# -------------------------------

# Creamos las 3 pestañas
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📘 Contract Analysis", "🌐 External Alerts"])

# ==============================================================
# PESTAÑA 1: DASHBOARD
# ==============================================================
with tab1:
    st.header("Procurement Overview")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Contracts", "15")
    col2.metric("High Risk", "3", "Warning", delta_color="inverse")
    col3.metric("Pending", "7")
    
    st.markdown("---")
    st.subheader("Active Contracts")
    
    # Tabla con índice corregido (Empieza en 1)
    df = pd.DataFrame([
        {"Supplier": "Cement Quebec", "Status": "Critical Risk", "Value": "$120k"},
        {"Supplier": "Germany Alum", "Status": "Safe", "Value": "$85k"},
        {"Supplier": "Montreal Steel", "Status": "Review", "Value": "$200k"},
    ])
    df.index = df.index + 1
    st.dataframe(df, use_container_width=True)

# ==============================================================
# PESTAÑA 2: ANÁLISIS DE CONTRATO
# ==============================================================
with tab2:
    st.header("Detailed Analysis")
    
    if contract_text:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Auto-Summary")
            if st.button("Generate Summary"):
                with st.spinner("Processing..."):
                    res = ask_ibm_watson(f"Summarize this: {contract_text[:3000]}")
                    st.write(res)
        
        with col2:
            st.subheader("Risk Detection")
            if st.button("Scan for Risks"):
                with st.spinner("Scanning..."):
                    res = ask_ibm_watson(f"List 3 risks in this contract: {contract_text[:3000]}")
                    st.warning(res)

        st.markdown("---")
        with st.expander("📄 View Full Contract Text"):
            st.text(contract_text)
            
    else:
        st.info("👈 Please upload a PDF in the Sidebar to activate the analysis tools.")

# ==============================================================
# PESTAÑA 3: NOTICIAS
# ==============================================================
with tab3:
    st.header("Global Supply Chain Alerts")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search news:", "construction materials")
    with col2:
        st.write("") 
        st.write("") 
        search_btn = st.button("Search")
    
    if search_btn or query:
        st.markdown("---")
        st.subheader("Strike at Montreal Port")
        st.caption("Logistics Daily • 2h ago")
        st.error("🔴 High Impact")
        
        st.markdown("---")
        st.subheader("Aluminum Prices Stable")
        st.caption("Global Trade • 5h ago")
        st.success("🟢 Low Impact")
