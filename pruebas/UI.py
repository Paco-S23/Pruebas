import streamlit as st
import pandas as pd
import requests
import json
import PyPDF2  # <--- NUEVA LIBRERÍA PARA LEER PDFs
import streamlit.components.v1 as components
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

# -------------------------------
# 1. CONFIGURACIÓN
# -------------------------------
st.set_page_config(page_title="ProcureWatch • Agentic AI", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# 2. BASE DE DATOS SIMULADA (CONTRATOS - FALLBACK)
# -------------------------------
contracts_db = {
    "⚠️ Heavy Metal Solutions (High Risk)": """
    CONTRACT ID: HMS-2025-001
    SUPPLIER: Heavy Metal Solutions S.A.
    DATE: Nov 24, 2025
     
    1. PAYMENT TERMS: Client must pay 100% of the total value in advance before loading. No refunds.
    2. DELAY PENALTY: In case of delay, the penalty is $10 USD per day, capped at a maximum of $100 USD total.
    3. WARRANTY: Goods are delivered 'AS-IS'. The Supplier accepts no responsibility for oxidation, fatigue, or defects.
    4. TERMINATION: The Supplier reserves the right to terminate this agreement unilaterally without notice.
    """,
     
    "✅ Global Cement Corp (Safe)": """
    CONTRACT ID: GCC-2025-998
    SUPPLIER: Global Cement Corp.
    DATE: Oct 10, 2025
     
    1. PAYMENT TERMS: Net 60 days after successful delivery and inspection.
    2. DELAY PENALTY: 5% of the total contract value for every week of delay.
    3. WARRANTY: 2-year full warranty on material quality and structural integrity.
    4. TERMINATION: 30 days written notice required by either party to terminate.
    """,
     
    "📋 Montreal SteelWorks (Standard)": """
    CONTRACT ID: MSW-2025-055
    SUPPLIER: Montreal SteelWorks
    DATE: Dec 01, 2025

    1. PAYMENT TERMS: 50% upfront, 50% upon delivery at port.
    2. DELAY PENALTY: Standard market rate applicable (0.5% per day).
    3. WARRANTY: 1-year standard warranty against manufacturing defects.
    4. TERMINATION: Termination requires mutual agreement.
    """
}

# -------------------------------
# 3. DEFINICIÓN DE AGENTES
# -------------------------------

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
        return f"Error conectando con IBM LLM: {str(e)}"

# --- SUB-AGENTE 1: DOCUMENT READER ---
def agent_document_reader(user_query, context_text):
    prompt = f"""
    ACT AS: Expert Contract Lawyer.
    TASK: Answer the question based STRICTLY on the provided contract text.
     
    CONTRACT CONTEXT:
    {context_text}
     
    USER QUESTION: {user_query}
     
    ANSWER:
    """
    return call_ibm_llm(prompt)

# --- SUB-AGENTE 2: WEB SEARCHER (NEWS API) ---
def agent_web_searcher(user_query):
    clean_query = user_query.replace("search", "").replace("news", "").replace("buscar", "").strip()
     
    # RECUERDA PONER TU API KEY REAL DE NEWSAPI AQUI
    api_key = "TU_API_KEY_DE_NEWSAPI_AQUI" 
     
    if api_key == "TU_API_KEY_DE_NEWSAPI_AQUI":
        return "⚠️ NewsAPI Key missing. Simulation: Found recent news about supply chain disruptions in logistics sectors."

    url = f"https://newsapi.org/v2/everything?q={clean_query}&sortBy=publishedAt&apiKey={api_key}&language=en&pageSize=3"
     
    try:
        response = requests.get(url)
        data = response.json()
        articles = data.get("articles", [])
         
        if not articles:
            return "I searched the web but found no recent news on that topic."
            
        summary = "Here are the latest news found:\n"
        for art in articles:
            summary += f"- Title: {art['title']}. Source: {art['source']['name']}.\n"
            
        return summary
    except:
        return "I tried to connect to the news feed but failed."

# --- AGENTE PRINCIPAL: EL ORQUESTADOR ---
def main_agent_router(user_query, has_contract_context):
    user_query_lower = user_query.lower()
     
    # 1. Búsqueda
    if "news" in user_query_lower or "search" in user_query_lower or "alert" in user_query_lower:
        return "SEARCH_AGENT"
    # 2. Documento
    elif has_contract_context:
        return "DOC_AGENT"
    # 3. General
    else:
        return "GENERAL_CHAT"

# -------------------------------
# 4. UI: BARRA LATERAL (EL CHAT INTELIGENTE)
# -------------------------------
with st.sidebar:
    st.title("📑 ProcureWatch")
    st.caption("Multi-Agent System Active")
    st.markdown("---")
    
    st.subheader("📂 Cargar Contrato (PDF)")
    # CAMBIO AQUI: Aceptamos type="pdf"
    uploaded_file = st.file_uploader("Sube tu contrato (.pdf)", type=["pdf"])
    
    contract_text = ""
    selected_contract_name = ""

    if uploaded_file is not None:
        # CASO 1: El usuario subió un PDF
        try:
            # Lógica de lectura de PDF con PyPDF2
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            extracted_text = ""
            # Iteramos por todas las páginas para extraer el texto
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
            
            contract_text = extracted_text
            selected_contract_name = uploaded_file.name
            
            if len(contract_text) < 10:
                st.warning("⚠️ El PDF parece estar vacío o es una imagen escaneada (sin texto seleccionable).")
            else:
                st.success(f"✅ PDF Procesado: {selected_contract_name}")
                
        except Exception as e:
            st.error(f"Error leyendo el PDF: {e}")
    else:
        # CASO 2: No hay archivo, usamos la Base de Datos de Ejemplo
        st.info("ℹ️ Modo Demo (Usa el desplegable)")
        selected_contract_name = st.selectbox(
            "Selecciona un contrato de ejemplo:",
            options=list(contracts_db.keys())
        )
        contract_text = contracts_db[selected_contract_name]
    
    st.markdown("---")
    
    # B. INTERFAZ DE CHAT (SIDEBAR)
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

    # C. INPUT Y LÓGICA
    if prompt := st.chat_input("Pregunta sobre el contrato o busca noticias..."):
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Decidimos qué agente usar
        decision = main_agent_router(prompt, bool(contract_text))
        
        final_response = ""
        agent_name = ""

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner(f"Orchestrator is routing to {decision}..."):
                    
                    if decision == "SEARCH_AGENT":
                        agent_name = "🌐 Search Agent"
                        raw_news = agent_web_searcher(prompt)
                        final_response = call_ibm_llm(f"Summarize these news for the user: {raw_news}")
                        
                    elif decision == "DOC_AGENT":
                        agent_name = "📄 Document Agent"
                        # Recortamos un poco el texto si es muy largo para no romper el token limit
                        text_to_analyze = contract_text[:15000] 
                        final_response = agent_document_reader(prompt, text_to_analyze)
                        
                    else:
                        agent_name = "🤖 General Assistant"
                        final_response = call_ibm_llm(f"Answer helpfuly: {prompt}")

                    st.markdown(final_response)
                    st.caption(f"⚡ Action handled by: {agent_name}")
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": final_response,
                        "agent_used": agent_name
                    })

# -------------------------------
# 5. ÁREA PRINCIPAL (TABS)
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

# PESTAÑA 2: ANÁLISIS + WATSON ORCHESTRATE
with tab2:
    st.header("Cross-reference contracts against warehouse records")
    
    # Mostrar qué contrato está activo actualmente (Demo o Real)
    st.info(f"📂 Currently Analyzing: **{selected_contract_name}**")

    # --- INICIO: EMBEBIDO DE WATSON ORCHESTRATE ---
    st.subheader("💬 Watson Orchestrate Assistant")
    
    # Usamos components.html para inyectar el JS proporcionado
    components.html("""
        <script>
          window.wxOConfiguration = {
            orchestrationID: "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
            hostURL: "https://jp-tok.watson-orchestrate.cloud.ibm.com",
            rootElementID: "root",
            deploymentPlatform: "ibmcloud",
            crn: "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::",
            chatOptions: {
                agentId: "df87f2d2-3200-4788-b0bd-de2033f818ee", 
                agentEnvironmentId: "f9558573-5f2c-4fc7-bdc3-09c8d590f7de",
            }
          };
          setTimeout(function () {
            const script = document.createElement('script');
            script.src = `${window.wxOConfiguration.hostURL}/wxochat/wxoLoader.js?embed=true`;
            script.addEventListener('load', function () {
                wxoLoader.init();
            });
            document.head.appendChild(script);
          }, 0);                      
        </script>
    """, height=600, scrolling=False)
    # --- FIN: EMBEBIDO DE WATSON ORCHESTRATE ---

    st.markdown("---")
    st.subheader("⚡ Quick AI Actions")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Generate Summary"):
            # Recorte de seguridad para no saturar el prompt
            safe_text = contract_text[:10000] 
            with st.spinner("Analyzing contract text..."):
                st.write(call_ibm_llm(f"Summarize this contract considering user is a procurement officer: {safe_text}"))
    with c2:
        if st.button("Scan Risks"):
            safe_text = contract_text[:10000]
            with st.spinner("Scanning for risks..."):
                st.warning(call_ibm_llm(f"Find high risk clauses in this text: {safe_text}"))
            
    with st.expander("View Full Contract Text"):
        st.code(contract_text)

# PESTAÑA 3: NOTICIAS
with tab3:
    st.header("External Supply Chain Events")
    query = st.text_input("Manual Search:", "Supply Chain")
    if st.button("Run Search Agent"):
        with st.spinner("Agent searching..."):
            results = agent_web_searcher(query)
            st.success("Search Complete")
            st.write(results)
