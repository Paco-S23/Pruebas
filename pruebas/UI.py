import streamlit as st
import pdfplumber
import pandas as pd
import requests
import json
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

# -------------------------------
# 1. CONFIGURACIÓN
# -------------------------------
st.set_page_config(page_title="ProcureWatch • Agentic AI", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# 2. DEFINICIÓN DE AGENTES
# -------------------------------

# --- HERRAMIENTA: LEER PDF (CACHÉ) ---
@st.cache_data
def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    return text

# --- MOTOR LLM (CEREBRO DE IBM) ---
def call_ibm_llm(prompt):
    creds = {
        "url": "https://us-south.ml.cloud.ibm.com",
        "apikey": "7df1e07ee763823210cc7609513c0c6fe4ff613cc3583613def0ec12f2570a17"
    }
    project_id = "077c11a6-2c5e-4c89-9a99-c08df3cb67ff"
    model_id = "ibm/granite-13b-chat-v2"
    
    parameters = {
        GenParams.DECODING_METHOD: "greedy",
        GenParams.MAX_NEW_TOKENS: 500,
        GenParams.MIN_NEW_TOKENS: 1
    }
    try:
        model = Model(model_id=model_id, params=parameters, credentials=creds, project_id=project_id)
        return model.generate_text(prompt=prompt)
    except Exception as e:
        return f"Error: {str(e)}"

# --- SUB-AGENTE 1: DOCUMENT READER ---
def agent_document_reader(user_query, context_text):
    prompt = f"""
    ACT AS: Expert Contract Lawyer.
    TASK: Answer the question based STRICTLY on the provided contract text.
    
    CONTRACT CONTEXT:
    {context_text[:4000]}
    
    USER QUESTION: {user_query}
    
    ANSWER:
    """
    return call_ibm_llm(prompt)

# --- SUB-AGENTE 2: WEB SEARCHER (NEWS API) ---
def agent_web_searcher(user_query):
    # Limpiamos la query para la búsqueda (quitamos palabras como "busca", "noticias")
    clean_query = user_query.replace("search", "").replace("news", "").replace("buscar", "").strip()
    
    # ⚠️ TU API KEY DE NEWSAPI
    api_key = "TU_API_KEY_DE_NEWSAPI_AQUI" 
    
    if api_key == "TU_API_KEY_DE_NEWSAPI_AQUI":
        return "⚠️ Error: Please configure your NewsAPI Key in the code to use the Search Agent."

    url = f"https://newsapi.org/v2/everything?q={clean_query}&sortBy=publishedAt&apiKey={api_key}&language=en&pageSize=3"
    
    try:
        response = requests.get(url)
        data = response.json()
        articles = data.get("articles", [])
        
        if not articles:
            return "I searched the web but found no recent news on that topic."
            
        # Formateamos las noticias para que el LLM las resuma
        summary = "Here are the latest news found:\n"
        for art in articles:
            summary += f"- Title: {art['title']}. Source: {art['source']['name']}.\n"
            
        return summary
    except:
        return "I tried to connect to the news feed but failed."

# --- AGENTE PRINCIPAL: EL ORQUESTADOR ---
def main_agent_router(user_query, has_contract_context):
    """
    Este agente decide a quién llamar.
    """
    user_query_lower = user_query.lower()
    
    # LÓGICA DE DECISIÓN (ROUTING)
    
    # 1. Si el usuario pide explícitamente buscar/noticias -> SUB-AGENTE BUSCADOR
    if "news" in user_query_lower or "search" in user_query_lower or "alert" in user_query_lower:
        return "SEARCH_AGENT"
        
    # 2. Si hay un contrato cargado y la pregunta parece del documento -> SUB-AGENTE LECTOR
    elif has_contract_context:
        return "DOC_AGENT"
        
    # 3. Si no, respuesta genérica -> LLM DIRECTO
    else:
        return "GENERAL_CHAT"


# -------------------------------
# 3. UI: BARRA LATERAL (EL CHAT INTELIGENTE)
# -------------------------------
with st.sidebar:
    st.title("📑 ProcureWatch")
    st.caption("Multi-Agent System Active")
    st.markdown("---")
    
    # A. CARGA DE CONTEXTO
    uploaded = st.file_uploader("Upload Contract (PDF)", type=["pdf"], key="sidebar_uploader")
    contract_text = ""
    if uploaded:
        contract_text = extract_text_from_pdf(uploaded)
        st.success("✅ Document Agent Ready")
    
    st.markdown("---")
    
    # B. INTERFAZ DE CHAT
    col_t, col_b = st.columns([2,1])
    with col_t: st.subheader("🤖 Agent Chat")
    with col_b: 
        if st.button("🗑️ Clear"): 
            st.session_state.messages = []
            st.rerun()
            
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "agent_used" in msg:
                    st.caption(f"Processed by: {msg['agent_used']}")

    # C. INPUT Y LÓGICA DEL AGENTE PRINCIPAL
    if prompt := st.chat_input("Ask about contracts or search news..."):
        
        # 1. Guardar mensaje usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # 2. EL AGENTE PRINCIPAL DECIDE
        decision = main_agent_router(prompt, bool(contract_text))
        
        final_response = ""
        agent_name = ""

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner(f"Orchestrator is routing to {decision}..."):
                    
                    # --- EJECUCIÓN DE SUB-AGENTES ---
                    
                    if decision == "SEARCH_AGENT":
                        agent_name = "🌐 Search Agent"
                        raw_news = agent_web_searcher(prompt)
                        # Usamos a IBM para resumir las noticias bonitas
                        final_response = call_ibm_llm(f"Summarize these news for the user: {raw_news}")
                        
                    elif decision == "DOC_AGENT":
                        agent_name = "📄 Document Agent"
                        final_response = agent_document_reader(prompt, contract_text)
                        
                    else:
                        agent_name = "🤖 General Assistant"
                        final_response = call_ibm_llm(f"Answer helpfuly: {prompt}")

                    st.markdown(final_response)
                    st.caption(f"⚡ Action handled by: {agent_name}")
                    
                    # Guardar en historial con etiqueta
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": final_response,
                        "agent_used": agent_name
                    })

# -------------------------------
# 4. ÁREA PRINCIPAL (TABS)
# -------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📘 Internal Contract Monitor", "🌐 Construction & Supply Chain Risk Monitor"])

# PESTAÑA 1: DASHBOARD
with tab1:
    st.header("Procurement Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Contracts", "15")
    c2.metric("High Risk", "3", "Warning", delta_color="inverse")
    c3.metric("Pending", "7")
    st.markdown("---")
    
    df = pd.DataFrame([
        {"Supplier": "Cement Quebec", "Status": "Critical Risk", "Value": "$120k"},
        {"Supplier": "Germany Alum", "Status": "Safe", "Value": "$85k"},
        {"Supplier": "Montreal Steel", "Status": "Review", "Value": "$200k"},
    ])
    df.index = df.index + 1
    st.dataframe(df, use_container_width=True)

# PESTAÑA 2: ANÁLISIS
with tab2:
    st.header("Cross-reference all contracts against actual warehouse records to identify compliance issues, delivery failures, and specification mismatches.")
    if contract_text:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Generate Summary"):
                st.write(call_ibm_llm(f"Summarize: {contract_text[:3000]}"))
        with c2:
            if st.button("Scan Risks"):
                st.warning(call_ibm_llm(f"Find risks: {contract_text[:3000]}"))
        with st.expander("View Text"):
            st.text(contract_text)
    else:
        st.info("👈 Upload a PDF in the Sidebar first.")

# PESTAÑA 3: NOTICIAS
with tab3:
    st.header("Scans online sources to detect external events that may impact the supply chain or specific contracts.")
    query = st.text_input("Manual Search:", "Supply Chain")
    if st.button("Run Search Agent"):
        with st.spinner("Agent searching..."):
            # Reutilizamos el sub-agente de búsqueda
            results = agent_web_searcher(query)
            st.success("Search Complete")
            st.write(results)


