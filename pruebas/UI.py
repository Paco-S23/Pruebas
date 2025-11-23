# UI.py - Versión funcional para hackathon (Orchestrate embeds + fallback local LLM)
import streamlit as st
import pandas as pd
import requests
import json
import PyPDF2
import streamlit.components.v1 as components
import re
from html import escape
from pathlib import Path

st.set_page_config(page_title="ProcureWatch • Agentic AI", layout="wide")

# -------------------------------
# 0. ASSET UPLOADED (ruta local que pediste)
# -------------------------------
# Ruta local capturada desde la sesión (imagen subida antes). La incluyo como referencia.
asset_path = "/mnt/data/861b3114-7119-41c5-8a74-39547a9951a9.png"  # <--- ruta local del archivo en tu sesión

# -------------------------------
# 1. SESSION STATE
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# 2. FALLBACK DB (contratos demo)
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
# 3. TRY IMPORT IBM SDK (optional)
# -------------------------------
has_ibm_sdk = True
try:
    from ibm_watson_machine_learning.foundation_models import Model
    from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
except Exception:
    has_ibm_sdk = False

# -------------------------------
# 4. LOCAL FALLBACK SUMMARIZER & HELPERS
# -------------------------------
def safe_shorten(text, max_chars=2000):
    if not text:
        return ""
    return text[:max_chars] + ("..." if len(text) > max_chars else "")

def extract_key_clauses(text):
    clauses = []
    lines = text.splitlines()
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        # heurística simple: líneas numeradas o palabras clave
        if re.match(r'^\d+\.', line_clean) or re.search(r'\bPAYMENT|DELAY|WARRANTY|TERMINATION|PENALTY|AS-IS|REFUND\b', line_clean, re.I):
            clauses.append(line_clean)
        if len(clauses) >= 10:
            break
    return clauses

def local_summarizer(contract_text, role="procurement officer"):
    if not contract_text or len(contract_text.strip()) < 10:
        return "No se encontró texto legible en el contrato. Por favor carga un PDF con texto seleccionable."

    first_lines = [ln.strip() for ln in contract_text.splitlines() if ln.strip()][:6]
    title = first_lines[0] if first_lines else "Contract"
    top_excerpt = "\n".join(first_lines[:4])
    clauses = extract_key_clauses(contract_text)
    clauses_text = "\n".join(f"- {c}" for c in clauses) if clauses else "No se detectaron cláusulas obvias por heurística."

    recommendations = []
    if re.search(r'100%.*advance|pay.*100%', contract_text, re.I):
        recommendations.append("Payment 100% in advance detected: consider escrow / partial payments.")
    if re.search(r'\bas-is\b|\bas is\b', contract_text, re.I):
        recommendations.append("Goods delivered 'AS-IS': request minimum warranty or inspection clause.")
    if re.search(r'\bterminate.*without notice\b', contract_text, re.I):
        recommendations.append("Unilateral termination clause found: negotiate notice or penalties.")
    if not recommendations:
        recommendations.append("No high-severity patterns detected by heuristic; review manually.")

    summary = f"""Resumen rápido ({role}) — {title}

{top_excerpt}

Cláusulas / fragmentos detectados:
{clauses_text}

Recomendaciones:
- {'\n- '.join(recommendations)}

(Heurística local — para análisis profundo usa tu agente Orchestrate embebido)
"""
    return summary

# -------------------------------
# 5. CALL IBM LLM (intenta, si falla usa fallback)
# -------------------------------
def call_ibm_llm(prompt):
    """
    Intenta usar IBM SDK si está instalado y st.secrets tiene credenciales.
    Si falla por cualquier motivo, usamos local_summarizer(prompt).
    """
    # si no hay SDK -> fallback
    if not has_ibm_sdk:
        return "(Fallback) SDK IBM no disponible. Usando resumidor local.\n\n" + local_summarizer(prompt, role="assistant")
    # intenta leer credenciales seguras (recomiendo usar st.secrets)
    api_key = st.secrets.get("IBM_API_KEY") if "IBM_API_KEY" in st.secrets else None
    url = st.secrets.get("WATSONX_URL") if "WATSONX_URL" in st.secrets else None
    project_id = st.secrets.get("PROJECT_ID") if "PROJECT_ID" in st.secrets else None

    if not api_key or not url or not project_id:
        # fallback si faltan credenciales
        return "(Fallback) IBM credentials missing in st.secrets. Usando resumidor local.\n\n" + local_summarizer(prompt, role="assistant")

    # si tenemos SDK y credenciales, intentamos la llamada (capturamos cualquier excepción)
    try:
        creds = {"url": url, "apikey": api_key}
        model_id = "ibm/granite-13b-chat-v2"
        parameters = {
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: 500,
            GenParams.MIN_NEW_TOKENS: 1
        }
        model = Model(model_id=model_id, params=parameters, credentials=creds, project_id=project_id)
        return model.generate_text(prompt=prompt)
    except Exception as e:
        return f"(Fallback) Error connecting to IBM LLM: {e}\n\n" + local_summarizer(prompt, role="assistant")

# -------------------------------
# 6. AGENT SUB-FUNCTIONS
# -------------------------------
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

def agent_web_searcher(user_query):
    clean_query = user_query.replace("search", "").replace("news", "").replace("buscar", "").strip()
    api_key = st.secrets.get("NEWSAPI_KEY", None)
    if not api_key:
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

def main_agent_router(user_query, has_contract_context):
    user_query_lower = user_query.lower()
    if "news" in user_query_lower or "search" in user_query_lower or "alert" in user_query_lower:
        return "SEARCH_AGENT"
    elif has_contract_context:
        return "DOC_AGENT"
    else:
        return "GENERAL_CHAT"

# -------------------------------
# 7. SIDEBAR (chat + upload)
# -------------------------------
with st.sidebar:
    st.title("📑 ProcureWatch")
    st.caption("Multi-Agent System Active")
    st.markdown("---")

    st.subheader("📂 Cargar Contrato (PDF)")
    uploaded_file = st.file_uploader("Sube tu contrato (.pdf)", type=["pdf"])

    contract_text = ""
    selected_contract_name = ""

    if uploaded_file is not None:
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            extracted_text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
            contract_text = extracted_text
            selected_contract_name = uploaded_file.name
            if len(contract_text) < 10:
                st.warning("⚠️ El PDF parece estar vacío o es una imagen escaneada (sin texto seleccionable).")
            else:
                st.success(f"✅ PDF Procesado: {selected_contract_name}")
        except Exception as e:
            st.error(f"Error leyendo el PDF: {e}")
    else:
        st.info("ℹ️ Modo Demo (Usa el desplegable)")
        selected_contract_name = st.selectbox("Selecciona un contrato de ejemplo:", options=list(contracts_db.keys()))
        contract_text = contracts_db[selected_contract_name]

    st.markdown("---")
    col_t, col_b = st.columns([2,1])
    with col_t:
        st.subheader("🤖 Agent Chat")
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

    if prompt := st.chat_input("Pregunta sobre el contrato o busca noticias..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

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
                        text_to_analyze = contract_text[:15000]
                        final_response = agent_document_reader(prompt, text_to_analyze)
                    else:
                        agent_name = "🤖 General Assistant"
                        final_response = call_ibm_llm(f"Answer helpfully: {prompt}")

                    st.markdown(final_response)
                    st.caption(f"⚡ Action handled by: {agent_name}")
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": final_response,
                        "agent_used": agent_name
                    })

# -------------------------------
# 8. MAIN AREA (TABS)
# -------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📘 Internal Contract Monitor", "🌐 Construction & Supply Chain Risk Monitor"])

# TAB 1
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

# TAB 2 - Internal Contract Monitor (embed + actions)
with tab2:
    st.header("Cross-reference contracts against warehouse records")
    st.info(f"📂 Currently Analyzing: **{selected_contract_name}**")

    st.subheader("💬 Watson Orchestrate Assistant — Contract Monitor")
    # Selector de agente (si quieres cambiar al otro desde aquí)
    agent_choice = st.selectbox("Selecciona agente Orchestrate a mostrar:",
                                ("Internal Contract Monitor", "Construction & Supply Chain Risk Monitor"))

    if agent_choice == "Internal Contract Monitor":
        orchestrate_html = """
        <div id="root"></div>
        <script>
          window.wxOConfiguration = {
            orchestrationID: "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
            hostURL: "https://jp-tok.watson-orchestrate.cloud.ibm.com",
            rootElementID: "root",
            deploymentPlatform: "ibmcloud",
            crn: "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::",
            chatOptions: {
                agentId: "df87f2d2-3200-4788-b0bd-de2033f818ee",
                agentEnvironmentId: "f9558573-5f2c-4fc7-bdc3-09c8d590f7de"
            }
          };
          setTimeout(function () {
            const script = document.createElement('script');
            script.src = window.wxOConfiguration.hostURL + "/wxochat/wxoLoader.js?embed=true";
            script.addEventListener('load', function () {
                if (window.wxoLoader) { wxoLoader.init(); }
            });
            document.head.appendChild(script);
          }, 0);
        </script>
        """
        components.html(orchestrate_html, height=650, scrolling=False)
    else:
        orchestrate_html = """
        <div id="root2"></div>
        <script>
          window.wxOConfiguration = {
            orchestrationID: "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
            hostURL: "https://jp-tok.watson-orchestrate.cloud.ibm.com",
            rootElementID: "root2",
            deploymentPlatform: "ibmcloud",
            crn: "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::",
            chatOptions: {
                agentId: "ab2a2d5a-feb8-4756-b8cb-57d78bbb085c",
                agentEnvironmentId: "3ed7b3a1-c9d5-4d20-8ace-beda0ab22455"
            }
          };
          setTimeout(function () {
            const script = document.createElement('script');
            script.src = window.wxOConfiguration.hostURL + "/wxochat/wxoLoader.js?embed=true";
            script.addEventListener('load', function () {
                if (window.wxoLoader) { wxoLoader.init(); }
            });
            document.head.appendChild(script);
          }, 0);
        </script>
        """
        components.html(orchestrate_html, height=650, scrolling=False)

    st.markdown("---")
    st.subheader("⚡ Quick AI Actions")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Generate Summary"):
            safe_text = safe_shorten(contract_text, max_chars=20000)
            with st.spinner("Generando resumen..."):
                # Intentamos LLM remoto (si falla, fallback local)
                result = call_ibm_llm(f"Summarize this contract considering user is a procurement officer: {safe_text}")
                st.markdown(result)
                # ofrecer descarga/copia
                st.download_button("Descargar resumen (.txt)", result, file_name="contract_summary.txt")
                # botón de copiar
                copy_html = f"""
                <button id="copybtn">Copiar resumen</button>
                <script>
                const btn = document.getElementById("copybtn");
                btn.addEventListener('click', () => {{
                    navigator.clipboard.writeText(`{escape(result)}`);
                    btn.innerText = "Copiado ✅";
                    setTimeout(()=>{{btn.innerText = "Copiar resumen";}}, 2000);
                }});
                </script>
                """
                components.html(copy_html, height=60)
    with c2:
        if st.button("Scan Risks"):
            safe_text = safe_shorten(contract_text, max_chars=20000)
            with st.spinner("Escaneando riesgos (heurística)..."):
                clauses = extract_key_clauses(safe_text)
                if clauses:
                    st.warning("Cláusulas potencialmente riesgosas detectadas:")
                    for c in clauses:
                        st.write(f"- {c}")
                else:
                    st.success("No se detectaron cláusulas críticas por heurística local.")
                # copiar resultados
                components.html("""
                <button id="copybtn2">Copiar hallazgos</button>
                <script>
                const btn2 = document.getElementById("copybtn2");
                btn2.addEventListener('click', () => {
                    navigator.clipboard.writeText(document.body.innerText);
                    btn2.innerText = "Copiado ✅";
                    setTimeout(()=>{btn2.innerText = "Copiar hallazgos";}, 2000);
                });
                </script>
                """, height=60)

    with st.expander("View Full Contract Text"):
        st.code(contract_text)

# TAB 3 - Supply Chain Agent
with tab3:
    st.header("External Supply Chain Events")
    st.subheader("🌐 Watson Orchestrate — Supply Chain Risk Monitor (Embed)")
    # mostramos el embed del segundo agente
    components.html("""
    <div id="root2"></div>
    <script>
      window.wxOConfiguration = {
        orchestrationID: "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
        hostURL: "https://jp-tok.watson-orchestrate.cloud.ibm.com",
        rootElementID: "root2",
        deploymentPlatform: "ibmcloud",
        crn: "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::",
        chatOptions: {
            agentId: "ab2a2d5a-feb8-4756-b8cb-57d78bbb085c",
            agentEnvironmentId: "3ed7b3a1-c9d5-4d20-8ace-beda0ab22455"
        }
      };
      setTimeout(function () {
        const script = document.createElement('script');
        script.src = window.wxOConfiguration.hostURL + "/wxochat/wxoLoader.js?embed=true";
        script.addEventListener('load', function () {
            if (window.wxoLoader) { wxoLoader.init(); }
        });
        document.head.appendChild(script);
      }, 0);
    </script>
    """, height=650, scrolling=False)

    st.markdown("---")
    query = st.text_input("Manual Search:", "Supply Chain")
    if st.button("Run Search Agent"):
        with st.spinner("Agent searching..."):
            results = agent_web_searcher(query)
            st.success("Search Complete")
            st.write(results)

# FOOTER
st.markdown("---")
st.caption("Tips: 1) Genera resumen → 2) Copia/descarga → 3) Péga el resumen en el chat Orchestrate para que el agente ejecute workflows automáticos.")

# Mostrar referencia al asset subido (ruta local)
st.info(f"Asset local (capturado en sesión): {asset_path}")
