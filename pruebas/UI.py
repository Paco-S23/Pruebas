import streamlit as st
import pdfplumber
import pandas as pd
import requests  # <--- NUEVA LIBRERÍA PARA CONECTAR CON LA API
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
# 2. FUNCIONES DE CONEXIÓN (BACKEND)
# -------------------------------

# A. CACHÉ DE PDF
@st.cache_data
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    return text

# B. IBM WATSON (YA LA TIENES)
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

# C. NUEVA FUNCIÓN: NOTICIAS REALES (NEWS API)
def get_real_news(query):
    # ⚠️ PON AQUÍ TU API KEY DE NEWSAPI.ORG
    api_key = "TU_API_KEY_DE_NEWSAPI_AQUI" 
    
    if api_key == "TU_API_KEY_DE_NEWSAPI_AQUI":
        return [{"title": "Error: Missing API Key", "source": {"name": "System"}, "description": "Please get a free key at newsapi.org and paste it in the code.", "url": "#"}]

    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={api_key}&language=en&pageSize=5"
    
    try:
        response = requests.get(url)
        data = response.json()
        if data.get("status") == "ok":
            return data.get("articles", [])
        else:
            return []
    except:
        return []

# -------------------------------
# 3. BARRA LATERAL
# -------------------------------
with st.sidebar:
    st.title("📑 ProcureWatch")
    st.caption("AI Supply Chain Monitor")
    st.markdown("---")
    
    uploaded = st.file_uploader("Upload Context (PDF)", type=["pdf"], key="sidebar_uploader")
    contract_text = ""
    if uploaded:
        contract_text = extract_text_from_pdf(uploaded)
        st.success("✅ Context Active")
    st.markdown("---")
    
    col_title, col_btn = st.columns([2,1])
    with col_title:
        st.subheader("🤖 Chat")
    with col_btn:
        if st.button("🗑️ Clear", type="primary"):
            st.session_state.messages = []
            st.rerun()
    
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.info("👋 Ready to help.")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    if prompt := st.chat_input("Ask AI..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        if contract_text:
            final_prompt = f"""Context: {contract_text[:3000]}
            Question: {prompt}
            Answer:"""
        else:
            final_prompt = f"""Question: {prompt}
            Answer as expert:"""

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    response = ask_ibm_watson(final_prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

# -------------------------------
# 4. ÁREA PRINCIPAL (TABS)
# -------------------------------

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📘 Contract Analysis", "🌐 External Alerts"])

# PESTAÑA 1: DASHBOARD
with tab1:
    st.header("Procurement Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Contracts", "15")
    col2.metric("High Risk", "3", "Warning", delta_color="inverse")
    col3.metric("Pending", "7")
    st.markdown("---")
    st.subheader("Active Contracts")
    
    df = pd.DataFrame([
        {"Supplier": "Cement Quebec", "Status": "Critical Risk", "Value": "$120k"},
        {"Supplier": "Germany Alum", "Status": "Safe", "Value": "$85k"},
        {"Supplier": "Montreal Steel", "Status": "Review", "Value": "$200k"},
    ])
    df.index = df.index + 1
    st.dataframe(df, use_container_width=True)

# PESTAÑA 2: ANÁLISIS
with tab2:
    st.header("Detailed Analysis")
    if contract_text:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Generate Summary"):
                with st.spinner("Processing..."):
                    res = ask_ibm_watson(f"Summarize this: {contract_text[:3000]}")
                    st.write(res)
        with col2:
            if st.button("Scan for Risks"):
                with st.spinner("Scanning..."):
                    res = ask_ibm_watson(f"List 3 risks: {contract_text[:3000]}")
                    st.warning(res)
        with st.expander("📄 View Full Text"):
            st.text(contract_text)
    else:
        st.info("👈 Upload a PDF in the Sidebar first.")

# PESTAÑA 3: NOTICIAS REALES (AQUÍ ESTÁ EL CAMBIO)
with tab3:
    st.header("Global Supply Chain Alerts (Live)")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("Search Live News:", "Supply Chain")
    with col2:
        st.write("") 
        st.write("") 
        search_btn = st.button("Search Web")
    
    if search_btn or query:
        with st.spinner(f"Searching latest news for: {query}..."):
            
            # LLAMADA A LA NUEVA FUNCIÓN DE API REAL
            articles = get_real_news(query)
            
            if articles:
                for article in articles:
                    st.markdown("---")
                    st.subheader(article.get("title", "No Title"))
                    
                    # Fuente y Fecha
                    source_name = article.get("source", {}).get("name", "Unknown")
                    st.caption(f"Source: {source_name}")
                    
                    # Descripción
                    st.write(article.get("description", "No description available."))
                    
                    # Link original
                    link = article.get("url", "#")
                    st.markdown(f"[Read full article >]({link})")
            else:
                st.warning("No news found or API Key invalid.")
