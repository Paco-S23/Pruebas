import streamlit as st
import pdfplumber
import pandas as pd
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

# -------------------------------
# 1. CONFIGURACIÓN E INICIO
# -------------------------------
st.set_page_config(page_title="ProcureWatch • AI", layout="wide")

# Inicializar memoria del chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# 2. FUNCIONES OPTIMIZADAS (CACHÉ)
# -------------------------------

# ESTA FUNCIÓN EVITA QUE SE TRABE
# @st.cache_data guarda el resultado. Si subes el mismo PDF, no lo procesa de nuevo.
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
        GenParams.MAX_NEW_TOKENS: 300, # Un poco menos para que responda rápido en el chat
        GenParams.MIN_NEW_TOKENS: 1,
        GenParams.REPETITION_PENALTY: 1.1
    }

    try:
        model = Model(model_id=model_id, params=parameters, credentials=creds, project_id=project_id)
        return model.generate_text(prompt=prompt_text)
    except Exception as e:
        return f"Error: {str(e)}"

# -------------------------------
# 3. BARRA LATERAL (SIDEBAR) - AQUÍ VIVE EL CHAT AHORA
# -------------------------------
with st.sidebar:
    st.title("🤖 AI Assistant")
    
    # --- ZONA DE CARGA (Siempre visible para dar contexto) ---
    uploaded = st.file_uploader("Upload Context (PDF)", type=["pdf"], key="sidebar_uploader")
    
    contract_text = ""
    if uploaded:
        # Usamos la función con caché para que no se trabe
        contract_text = extract_text_from_pdf(uploaded)
        st.success("✅ Contract Loaded")
    
    st.markdown("---")
    
    # --- CHATBOT EN EL SIDEBAR ---
    # Contenedor para los mensajes (para que aparezcan arriba del input)
    messages_container = st.container()
    
    # Mostramos historial
    with messages_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Input del chat (Se ancla al fondo del sidebar automáticamente)
    if prompt := st.chat_input("Ask me anything..."):
        
        # 1. Guardar y mostrar mensaje usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with messages_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # 2. Preparar Prompt
        if contract_text:
            final_prompt = f"""
            Context: {contract_text[:3000]}
            User Question: {prompt}
            Answer based on context:
            """
        else:
            final_prompt = f"User Question: {prompt}\nAnswer as a helpful assistant:"

        # 3. Generar respuesta
        with messages_container:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = ask_ibm_watson(final_prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

# -------------------------------
# 4. PÁGINA PRINCIPAL (MAIN AREA)
# -------------------------------
st.title("📑 ProcureWatch Dashboard")

# Menú de navegación superior (Pestañas) para aprovechar el espacio
tab1, tab2 = st.tabs(["📊 Dashboard", "🌐 Risk Alerts"])

with tab1:
    st.header("Contract Overview")
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Analyzed Contracts", "12")
    col2.metric("High Risks", "2", "Critical", delta_color="inverse")
    col3.metric("Pending", "5")
    
    st.markdown("---")
    
    # Tabla (Índice corregido iniciando en 1)
    df = pd.DataFrame([
        {"Supplier": "Cement Quebec", "Status": "Critical Risk", "Value": "$120k"},
        {"Supplier": "Germany Alum", "Status": "Safe", "Value": "$85k"},
        {"Supplier": "Montreal Steel", "Status": "Review", "Value": "$200k"},
    ])
    df.index = df.index + 1
    st.dataframe(df, use_container_width=True)
    
    # Si hay contrato subido, mostramos su texto aquí también
    if contract_text:
        st.markdown("---")
        st.subheader("📄 Current Contract Content")
        with st.expander("Click to view full text"):
            st.text(contract_text)

with tab2:
    st.header("Global Supply Chain Alerts")
    
    col_search, col_btn = st.columns([4,1])
    query = col_search.text_input("Search News", "Logistics")
    if col_btn.button("Search"):
        st.info(f"Showing results for: {query}")
        
        st.subheader("Strike at Montreal Port")
        st.caption("Logistics Daily • 2h ago")
        st.error("🔴 High Impact")
        
        st.divider()
        
        st.subheader("Aluminum Prices Stable")
        st.caption("Global Trade • 5h ago")
        st.success("🟢 Low Impact")
