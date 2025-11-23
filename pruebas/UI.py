import streamlit as st
import pandas as pd
import PyPDF2
import streamlit.components.v1 as components
import re
from html import escape

# -------------------------------
# 1. CONFIGURACIÓN
# -------------------------------
st.set_page_config(page_title="ProcureWatch • Agentic AI", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------
# 2. BASE DE DATOS SIMULADA
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
# 3. FUNCIONES AUXILIARES (LOCAL FALLBACK)
# -------------------------------

def safe_shorten(text, max_chars=2000):
    if not text:
        return ""
    return text[:max_chars] + ("..." if len(text) > max_chars else "")

def extract_key_clauses(text):
    # Heurística simple: buscar líneas que empiecen con números o palabras clave legales
    clauses = []
    lines = text.splitlines()
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
        if re.match(r'^\d+\.|\bPAYMENT|DELAY|WARRANTY|TERMINATION|PENALTY|WARRANTY\b', line_clean, re.I):
            clauses.append(line_clean)
        if len(clauses) >= 8:
            break
    return clauses

def local_summarizer(contract_text, role="procurement officer"):
    """
    Generador de resumen local y seguro (heurístico).
    - Extrae título / metadata (si hay)
    - Extrae primeras líneas
    - Lista cláusulas clave encontradas
    - Genera recomendaciones básicas
    """
    if not contract_text or len(contract_text.strip()) < 10:
        return "No se encontró texto legible en el contrato. Por favor carga un PDF con texto seleccionable."

    t = contract_text.strip()
    # metadata/title heurístico
    first_lines = [ln.strip() for ln in t.splitlines() if ln.strip()][:6]
    title = first_lines[0] if first_lines else "Contract"
    top_excerpt = "\n".join(first_lines[:4])

    clauses = extract_key_clauses(contract_text)
    clauses_text = "\n".join(f"- {c}" for c in clauses) if clauses else "No se detectaron cláusulas obvias por heurística."

    # recomendaciones simples
    recommendations = []
    if any(re.search(r'100%.*advance|pay.*100%', contract_text, re.I) for _ in [1]):
        recommendations.append("Payment in advance detected: verify escrow or partial payment options.")
    if any(re.search(r'\bas-is\b|\bas is\b', contract_text, re.I) for _ in [1]):
        recommendations.append("Goods delivered 'AS-IS': consider requesting a minimum quality/warranty clause.")
    if any(re.search(r'\bterminate.*without notice\b', contract_text, re.I) for _ in [1]):
        recommendations.append("Unilateral termination clause found: negotiate notice period or penalties.")
    if not recommendations:
        recommendations.append("No high-severity patterns detected by heuristic; still review manually.")

    summary = f"""**Resumen rápido ({role}) — {title}**

{escape(top_excerpt)}

**Cláusulas / fragmentos detectados:**
{escape(clauses_text)}

**Recomendaciones:**
- {'\n- '.join([escape(r) for r in recommendations])}

**(Heurística local — para un análisis profundo usa tu agente Orchestrate en la pestaña 'Internal Contract Monitor')**
"""
    return summary

# -------------------------------
# 4. FUNCIONES PARA LA UI
# -------------------------------

def copy_to_clipboard_button(text, button_label="Copiar al portapapeles"):
    """Inserta un pequeño componente HTML+JS que copia texto al portapapeles."""
    safe_text = escape(text)
    html = f"""
    <button id="copybtn">{button_label}</button>
    <script>
    const btn = document.getElementById("copybtn");
    btn.addEventListener('click', () => {{
        const text = `{safe_text}`;
        navigator.clipboard.writeText(text).then(function() {{
            btn.innerText = "Copiado ✅";
            setTimeout(()=>{{btn.innerText = "{button_label}";}}, 2000);
        }}, function(err) {{
            btn.innerText = "Error";
        }});
    }});
    </script>
    """
    components.html(html, height=45)

# -------------------------------
# 5. UI: BARRA LATERAL (EL CHAT INTELIGENTE)
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
                # extract_text puede devolver None en páginas vacías
                page_text = page.extract_text()
                if page_text:
                    extracted_text += page_text + "\n"
            contract_text = extracted_text
            selected_contract_name = uploaded_file.name
            
            if len(contract_text) < 10:
                st.warning("⚠️ El PDF parece estar vacío o es una imagen escaneada.")
            else:
                st.success(f"✅ PDF Procesado: {selected_contract_name}")
                
        except Exception as e:
            st.error(f"Error leyendo el PDF: {e}")
    else:
        st.info("ℹ️ Modo Demo (Usa el desplegable)")
        selected_contract_name = st.selectbox(
            "Selecciona un contrato de ejemplo:",
            options=list(contracts_db.keys())
        )
        contract_text = contracts_db[selected_contract_name]
    
    st.markdown("---")
    
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

    if prompt := st.chat_input("Pregunta sobre el contrato o busca noticias..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Decide: en esta versión local no llamamos a LLM, avisamos usar Orchestrate
        decision = ("SEARCH_AGENT" if any(k in prompt.lower() for k in ["news","search","alert"])
                    else "DOC_AGENT" if contract_text else "GENERAL_CHAT")
        
        final_response = ""
        agent_name = ""

        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner(f"Orchestrator routing simulation ({decision})..."):
                    if decision == "SEARCH_AGENT":
                        agent_name = "🌐 Search Agent (simulated)"
                        final_response = "Heurística local: para búsquedas use el panel 'External Supply Chain Events' o el agente embebido."
                    elif decision == "DOC_AGENT":
                        agent_name = "📄 Document Agent (simulated)"
                        # respuesta rápida usando heurística local
                        final_response = local_summarizer(contract_text, role="assistant")
                    else:
                        agent_name = "🤖 General Assistant (simulated)"
                        final_response = "Estoy en modo offline: usa el agente Orchestrate embebido para respuestas inteligentes."

                    st.markdown(final_response)
                    st.caption(f"⚡ Action handled by: {agent_name}")
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": final_response,
                        "agent_used": agent_name
                    })

# -------------------------------
# 6. ÁREA PRINCIPAL (TABS)
# -------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📘 Internal Contract Monitor", "🌐 Construction & Supply Chain Risk Monitor"])

# TAB 1 -----------------------------------------
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

# TAB 2 -----------------------------------------
with tab2:
    st.header("Cross-reference contracts against warehouse records")
    st.info(f"📂 Currently Analyzing: **{selected_contract_name}**")

    # Selector de agente (permite cambiar entre los dos que tienes)
    agent_choice = st.selectbox("Selecciona agente Orchestrate a mostrar:", 
                                ("Internal Contract Monitor", "Construction & Supply Chain Risk Monitor"))

    st.subheader("💬 Watson Orchestrate Assistant — Contract Monitor")

    # Render del agente elegido (usa root / root2 internamente para evitar choques)
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
            script.src = `${window.wxOConfiguration.hostURL}/wxochat/wxoLoader.js?embed=true`;
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
            script.src = `${window.wxOConfiguration.hostURL}/wxochat/wxoLoader.js?embed=true`;
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
            with st.spinner("Generando resumen local..."):
                summary = local_summarizer(safe_text, role="procurement officer")
                st.markdown(summary)
                st.caption("Resumen generado localmente. Copia y pégalo en el chat embebido para que el agente lo use como contexto.")
                copy_to_clipboard_button(summary, "Copiar resumen para Orchestrate")
    with c2:
        if st.button("Scan Risks"):
            safe_text = safe_shorten(contract_text, max_chars=20000)
            with st.spinner("Escaneando riesgos (heurística local)..."):
                clauses = extract_key_clauses(safe_text)
                if clauses:
                    st.warning("Cláusulas potencialmente riesgosas detectadas:")
                    for c in clauses:
                        st.write(f"- {c}")
                else:
                    st.success("No se detectaron cláusulas críticas por heurística local.")
                st.caption("Copia los hallazgos y pégalos en el agente Orchestrate para validación y acciones automatizadas.")
                copy_to_clipboard_button("\n".join(clauses) if clauses else "No clauses found", "Copiar hallazgos")

    with st.expander("View Full Contract Text"):
        st.code(contract_text)

# TAB 3 -----------------------------------------
with tab3:
    st.header("External Supply Chain Events")

    st.subheader("🌐 Watson Orchestrate — Supply Chain Risk Monitor (Embed)")
    # mostramos el segundo agente aquí también para conveniencia (root2)
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
            script.src = `${window.wxOConfiguration.hostURL}/wxochat/wxoLoader.js?embed=true`;
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
            # simulación local: recordatorio para usar Orchestrate
            st.info("Ejecuta búsquedas complejas directamente desde el agente Orchestrate embebido (usa el agente de Supply Chain).")
            st.write("Simulated search result: Supply-chain disruptions in the harbour region (demo).")

# -------------------------------
# 7. FOOTER / HELP
# -------------------------------
st.markdown("---")
st.caption("Tips: 1) Genera el resumen localmente → 2) Copia el resumen → 3) Pégalo en el agente Orchestrate embebido para que el agente ejecute acciones (revisar, alertar, crear tareas).")
