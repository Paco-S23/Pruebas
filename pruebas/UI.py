# UI.py - Funcional (Orchestrate embeds + acciones: subir, resumir, scan, chat, descargar)
import streamlit as st
import pandas as pd
import requests
import json
import PyPDF2
import streamlit.components.v1 as components
import re
from html import escape
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="ProcureWatch • Agentic AI", layout="wide")

# -------------------------------
# CONFIG / ASSETS
# -------------------------------
asset_path = "/mnt/data/861b3114-7119-41c5-8a74-39547a9951a9.png"  # ruta local en sesión (imagen de referencia)

# -------------------------------
# SESSION
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_summary" not in st.session_state:
    st.session_state.last_summary = ""

if "last_clauses" not in st.session_state:
    st.session_state.last_clauses = []

# -------------------------------
# FALLBACK DB
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
# HELPERS: summarizer heurístico + clause extraction
# -------------------------------
def safe_shorten(text, max_chars=20000):
    if not text:
        return ""
    return text[:max_chars] + ("..." if len(text) > max_chars else "")

def extract_key_clauses(text, limit=20):
    clauses = []
    lines = text.splitlines()
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if re.match(r'^\d+\.', line_clean) or re.search(r'\bPAYMENT|DELAY|WARRANTY|TERMINATION|PENALTY|AS-IS|REFUND|LIMITATION|LIABILITY\b', line_clean, re.I):
            clauses.append(line_clean)
        if len(clauses) >= limit:
            break
    return clauses

def detect_breach_patterns(text):
    # heurística simple para detectar incumplimientos o cláusulas abusivas
    findings = []
    if re.search(r'100%.*advance|pay.*100%', text, re.I):
        findings.append("Payment 100% in advance detected — possible cashflow/risk for buyer.")
    if re.search(r'\bas-is\b|\bas is\b', text, re.I):
        findings.append("AS-IS delivery clause found — consider requiring inspection or warranty.")
    if re.search(r'\bterminate.*without notice\b', text, re.I):
        findings.append("Unilateral termination without notice — high risk.")
    if re.search(r'\bcap\b.*\b(liability|responsibility)\b', text, re.I):
        findings.append("Liability cap detected — check amount and exclusions.")
    return findings

def local_summarizer(contract_text, role="procurement officer"):
    if not contract_text or len(contract_text.strip()) < 10:
        return "No se encontró texto legible en el contrato. Por favor carga un PDF con texto seleccionable."
    first_lines = [ln.strip() for ln in contract_text.splitlines() if ln.strip()][:8]
    title = first_lines[0] if first_lines else "Contract"
    excerpt = "\n".join(first_lines[:4])
    clauses = extract_key_clauses(contract_text, limit=12)
    findings = detect_breach_patterns(contract_text)
    recs = []
    if findings:
        for f in findings:
            recs.append(f)
    else:
        recs.append("No high-severity patterns detected by heuristic; still review manually.")

    summary = "Resumen rápido (" + role + ") — " + title + "\n\n"
    summary += "Excerpt:\n" + excerpt + "\n\n"
    summary += "Cláusulas detectadas:\n"
    if clauses:
        for c in clauses:
            summary += "- " + c + "\n"
    else:
        summary += "- No se detectaron cláusulas obvias por heurística.\n"
    summary += "\nRecomendaciones:\n"
    for r in recs:
        summary += "- " + r + "\n"
    summary += "\n(Heurística local - para análisis más profundo usa Orchestrate embebido)\n"
    return summary

# -------------------------------
# TRY IBM SDK (opcional). Si falla, usamos fallback
# -------------------------------
has_ibm_sdk = True
try:
    from ibm_watson_machine_learning.foundation_models import Model
    from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams
except Exception:
    has_ibm_sdk = False

def call_ibm_llm(prompt):
    if not has_ibm_sdk:
        return "(Fallback) IBM SDK not available. Using local summarizer.\n\n" + local_summarizer(prompt, role="assistant")
    # Try to get secrets
    api_key = st.secrets.get("IBM_API_KEY") if "IBM_API_KEY" in st.secrets else None
    url = st.secrets.get("WATSONX_URL") if "WATSONX_URL" in st.secrets else None
    project_id = st.secrets.get("PROJECT_ID") if "PROJECT_ID" in st.secrets else None
    if not api_key or not url or not project_id:
        return "(Fallback) IBM credentials missing. Using local summarizer.\n\n" + local_summarizer(prompt, role="assistant")
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
        return "(Fallback) Error connecting to IBM LLM: " + str(e) + "\n\n" + local_summarizer(prompt, role="assistant")

# -------------------------------
# ORCHESTRATE EMBED RENDER (safe)
# -------------------------------
def render_orchestrate_embed(root_id, orchestration_id, host_url, crn, agent_id, agent_env_id):
    html = """
    <div id="%s" style="height: 600px; width: 100%%;"></div>
    <script>
    window.wxOConfiguration = {
      orchestrationID: "%s",
      hostURL: "%s",
      rootElementID: "%s",
      deploymentPlatform: "ibmcloud",
      crn: "%s",
      chatOptions: {
        agentId: "%s",
        agentEnvironmentId: "%s"
      }
    };
    setTimeout(function () {
      var script = document.createElement('script');
      script.src = window.wxOConfiguration.hostURL + "/wxochat/wxoLoader.js?embed=true";
      script.addEventListener('load', function () {
        if (window.wxoLoader) { try { wxoLoader.init(); } catch(e) { console.error(e); } }
      });
      document.head.appendChild(script);
    }, 0);
    </script>
    """ % (root_id, orchestration_id, host_url, root_id, crn, agent_id, agent_env_id)
    components.html(html, height=650, scrolling=False)

# -------------------------------
# UI: Sidebar (chat + upload)
# -------------------------------
with st.sidebar:
    st.title("📑 ProcureWatch")
    st.caption("Multi-Agent System Active")
    st.markdown("---")

    st.subheader("📂 Cargar Contrato (PDF / TXT)")
    uploaded_file = st.file_uploader("Sube tu contrato (.pdf, .txt)", type=["pdf", "txt"])

    contract_text = ""
    selected_contract_name = ""
    if uploaded_file is not None:
        try:
            if uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                extracted_text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
                contract_text = extracted_text
                selected_contract_name = uploaded_file.name
            else:
                # txt
                raw = uploaded_file.read()
                try:
                    contract_text = raw.decode("utf-8")
                except:
                    contract_text = str(raw)
                selected_contract_name = uploaded_file.name

            if len(contract_text) < 10:
                st.warning("⚠️ El archivo tiene poco o ningún texto seleccionable.")
            else:
                st.success("✅ Archivo procesado: " + selected_contract_name)
        except Exception as e:
            st.error("Error leyendo el archivo: " + str(e))
    else:
        st.info("Modo demo: selecciona un contrato de ejemplo")
        selected_contract_name = st.selectbox("Selecciona un contrato de ejemplo:", options=list(contracts_db.keys()))
        contract_text = contracts_db[selected_contract_name]

    st.markdown("---")
    st.subheader("🤖 Agent Chat (local)")
    # Chat input
    user_msg = st.text_input("Escribe tu pregunta para el asistente (local/IBM):", key="local_chat_input")
    if st.button("Enviar al asistente (local/IBM)"):
        if user_msg and len(user_msg.strip())>0:
            st.session_state.messages.append({"role":"user","content":user_msg})
            # decide routing
            if any(k in user_msg.lower() for k in ["news","search","alert"]):
                answer = agent_web_searcher(user_msg)
            elif contract_text:
                answer = agent_document_reader(user_msg, contract_text[:15000])
            else:
                answer = call_ibm_llm(user_msg)
            st.session_state.messages.append({"role":"assistant","content":answer,"agent_used":"local_or_ibm"})
            # clear input
            st.experimental_rerun()
        else:
            st.warning("Escribe algo antes de enviar.")

    st.markdown("---")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.experimental_rerun()

    # Show chat history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown("**Tú:** " + msg["content"])
        else:
            st.markdown("**Asistente:** " + msg["content"])
            if "agent_used" in msg:
                st.caption("Processed by: " + msg["agent_used"])

# -------------------------------
# MAIN AREA (tabs)
# -------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📘 Internal Contract Monitor", "🌐 Construction & Supply Chain Risk Monitor"])

# TAB 1 - Dashboard (overview + asset)
with tab1:
    st.header("Procurement Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Contracts", "15")
    c2.metric("High Risk", "3", "Warning", delta_color="inverse")
    c3.metric("Pending", "7")
    st.markdown("---")
    df = pd.DataFrame([
        {"Supplier":"Cement Quebec","Status":"Critical Risk","Value":"$120k"},
        {"Supplier":"Germany Alum","Status":"Safe","Value":"$85k"},
        {"Supplier":"Montreal Steel","Status":"Review","Value":"$200k"}
    ])
    df.index = df.index + 1
    st.dataframe(df, use_container_width=True)

    st.markdown("---")
    st.subheader("Image / Asset (session)")
    try:
        # try to render the local asset path if present
        components.html("<img src='%s' style='max-width:100%%;height:auto;'/>" % asset_path, height=240, scrolling=False)
    except:
        st.info("No se pudo cargar el asset local.")

# TAB 2 - Internal Contract Monitor
with tab2:
    st.header("Cross-reference contracts against warehouse records")
    st.info("📂 Currently Analyzing: **%s**" % selected_contract_name)

    st.subheader("💬 Watson Orchestrate Assistant — Contract Monitor")
    # selector to choose which embed root to use
    which = st.selectbox("Mostrar agente:", ("Internal Contract Monitor", "Construction & Supply Chain Risk Monitor"))
    if which == "Internal Contract Monitor":
        render_orchestrate_embed("root", "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
                                "https://jp-tok.watson-orchestrate.cloud.ibm.com",
                                "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::",
                                "df87f2d2-3200-4788-b0bd-de2033f818ee",
                                "f9558573-5f2c-4fc7-bdc3-09c8d590f7de")
    else:
        render_orchestrate_embed("root2", "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
                                "https://jp-tok.watson-orchestrate.cloud.ibm.com",
                                "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::",
                                "ab2a2d5a-feb8-4756-b8cb-57d78bbb085c",
                                "3ed7b3a1-c9d5-4d20-8ace-beda0ab22455")

    st.markdown("---")
    st.subheader("⚡ Quick AI Actions")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Generate Summary (local/IBM)"):
            safe_text = safe_shorten(contract_text, max_chars=20000)
            with st.spinner("Generando resumen..."):
                output = ""
                # Try IBM / fallback
                if contract_text and len(safe_text) > 0:
                    output = call_ibm_llm("Summarize this contract considering user is a procurement officer:\n\n" + safe_text)
                else:
                    output = local_summarizer(contract_text, role="procurement officer")
                st.code(output)
                st.session_state.last_summary = output
                # download as .txt
                st.download_button("Descargar resumen (.txt)", output, file_name="contract_summary.txt")
                # download clauses as csv if any
                clauses = extract_key_clauses(safe_text)
                st.session_state.last_clauses = clauses
                if clauses:
                    df_clauses = pd.DataFrame({"clause": clauses})
                    csv_bytes = df_clauses.to_csv(index=False).encode("utf-8")
                    st.download_button("Descargar cláusulas (.csv)", csv_bytes, file_name="contract_clauses.csv", mime="text/csv")
                # attempt generate PDF using reportlab if present
                try:
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
                    buffer = BytesIO()
                    p = canvas.Canvas(buffer, pagesize=letter)
                    text_lines = output.splitlines()
                    y = 750
                    p.setFont("Helvetica", 10)
                    for line in text_lines:
                        p.drawString(40, y, line[:95])
                        y -= 12
                        if y < 40:
                            p.showPage()
                            y = 750
                            p.setFont("Helvetica", 10)
                    p.save()
                    buffer.seek(0)
                    st.download_button("Descargar resumen (.pdf)", buffer, file_name="contract_summary.pdf", mime="application/pdf")
                except Exception:
                    # reportlab not available - skip pdf
                    pass

                # show button to send the summary to the embedded agent (tries injection, falls back to clipboard)
                # Use components.html to create a small UI that calls window.wxoLoader.sendMessage or copies.
                safe_output = escape(output)
                inject_html = """
                <div>
                  <button id="injectBtn">Enviar resumen al agente (intenta inyección)</button>
                  <button id="clipBtn">Copiar al portapapeles</button>
                  <script>
                    const inj = document.getElementById('injectBtn');
                    const clip = document.getElementById('clipBtn');
                    inj.addEventListener('click', function() {
                      // Try wxoLoader injection
                      try {
                        if (window.wxoLoader && typeof window.wxoLoader.sendMessage === 'function') {
                          window.wxoLoader.sendMessage(%s);
                          inj.innerText = "Enviado ✅";
                        } else {
                          // try postMessage to iframe if present
                          if (window.parent) {
                            window.parent.postMessage({type:'wxo_inject', payload: %s}, '*');
                            inj.innerText = "Intento postMessage ✅";
                          } else {
                            inj.innerText = "No disponible";
                          }
                        }
                      } catch(e) {
                        inj.innerText = "Fallo inyección";
                      }
                    });
                    clip.addEventListener('click', function() {
                      navigator.clipboard.writeText(`%s`).then(function(){ clip.innerText = "Copiado ✅"; setTimeout(()=>{clip.innerText="Copiar al portapapeles";},2000); });
                    });
                  </script>
                </div>
                """ % (json.dumps(safe_output), json.dumps(safe_output), safe_output)
                components.html(inject_html, height=90, scrolling=False)

    with c2:
        if st.button("Scan Risks (heuristic)"):
            safe_text = safe_shorten(contract_text, max_chars=20000)
            with st.spinner("Escaneando riesgos..."):
                clauses = extract_key_clauses(safe_text)
                findings = detect_breach_patterns(safe_text)
                if clauses:
                    st.warning("Cláusulas detectadas:")
                    for c in clauses:
                        st.write("- " + c)
                else:
                    st.success("No se detectaron cláusulas obvias por heurística.")
                if findings:
                    st.error("Patrones de riesgo encontrados:")
                    for f in findings:
                        st.write("- " + f)
                else:
                    st.info("No se detectaron patrones de riesgo automáticos.")
                # Export
                if clauses:
                    df_clauses = pd.DataFrame({"clause": clauses})
                    csv_bytes = df_clauses.to_csv(index=False).encode("utf-8")
                    st.download_button("Descargar hallazgos (.csv)", csv_bytes, file_name="risk_findings.csv", mime="text/csv")

    st.markdown("---")
    with st.expander("View Full Contract Text"):
        st.code(contract_text)

# TAB 3 - Supply Chain Agent (show second embed and a small manual-search pane)
with tab3:
    st.header("External Supply Chain Events")
    st.subheader("🌐 Watson Orchestrate — Supply Chain Risk Monitor (Embed)")
    render_orchestrate_embed("root2", "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
                             "https://jp-tok.watson-orchestrate.cloud.ibm.com",
                             "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::",
                             "ab2a2d5a-feb8-4756-b8cb-57d78bbb085c",
                             "3ed7b3a1-c9d5-4d20-8ace-beda0ab22455")
    st.markdown("---")
    query = st.text_input("Manual Search:", "Supply Chain")
    if st.button("Run Search Agent"):
        with st.spinner("Agent searching..."):
            # local simulation + suggestion to use embed agent
            st.info("Usa el agente embebido de Supply Chain para búsquedas avanzadas.")
            st.write("Simulated: Increased delays at Port X affecting cement imports.")

# Footer
st.markdown("---")
st.caption("Tips: 1) Genera resumen → 2) Copia/descarga → 3) Péga el resumen en el chat Orchestrate o usa 'Enviar resumen' (intento de inyección).")

