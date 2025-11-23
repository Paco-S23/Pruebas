import streamlit as st
import streamlit.components.v1 as components
import pdfplumber
import pandas as pd
import json
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

# -------------------------------
# 1. CONFIGURACIÓN GENERAL
# -------------------------------
st.set_page_config(
    page_title="ProcureWatch • Contract & Supply Monitor",
    layout="wide",
)

st.title("📑 ProcureWatch")
st.write("AI-powered contract monitoring and external supply-chain risk detection.")

# -------------------------------
# 2. LÓGICA DE CONEXIÓN CON IBM (BACKEND)
# -------------------------------
def analyze_contract_with_ibm(contract_text):
    # TUS CREDENCIALES (Ya puestas)
    creds = {
        "url": "https://us-south.ml.cloud.ibm.com", # Dallas
        "apikey": "7df1e07ee763823210cc7609513c0c6fe4ff613cc3583613def0ec12f2570a17"
    }
    project_id = "077c11a6-2c5e-4c89-9a99-c08df3cb67ff"

    # Configuración del modelo (Granite 13b es rápido y eficiente)
    model_id = "ibm/granite-13b-chat-v2"
    
    parameters = {
        GenParams.DECODING_METHOD: "greedy",
        GenParams.MAX_NEW_TOKENS: 600,
        GenParams.MIN_NEW_TOKENS: 10,
        GenParams.REPETITION_PENALTY: 1.1
    }

    try:
        model = Model(
            model_id=model_id,
            params=parameters,
            credentials=creds,
            project_id=project_id
        )

        # Instrucción estricta para que responda en JSON
        prompt = f"""
        Act as a procurement expert. Analyze the contract text below.
        Extract the following fields and return ONLY a valid JSON object.
        
        Fields required:
        - supplier: Name of the supplier.
        - summary: A 1-sentence summary of the contract.
        - risk_level: "High", "Medium", or "Low".
        - risks: A list of specific risks found (max 3).
        - status: Recommendation (e.g., "Review Required", "Approved").

        Contract Text:
        {contract_text[:3500]} 
        
        Output format (JSON only):
        """

        generated_response = model.generate_text(prompt=prompt)
        return generated_response

    except Exception as e:
        return f"Error connecting to IBM: {str(e)}"

# -------------------------------
# 3. COMPONENTES VISUALES
# -------------------------------
def risk_badge(level):
    if level == "High":
        st.error("🔴 High Risk")
    elif level == "Medium":
        st.warning("🟠 Medium Risk")
    elif level == "Low":
        st.success("🟢 Low Risk")
    else:
        st.info(f"⚪ {level}")

# -------------------------------
# 4. BARRA LATERAL (Navegación + Chat)
# -------------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Dashboard", "Contract Monitoring", "External Risk Alerts"]
)

# --- CHAT DE IBM ORCHESTRATE (EMBED) ---
with st.sidebar:
    st.markdown("---")
    st.subheader("🤖 AI Assistant")
    
    # Script de IBM Orchestrate
    ibm_chat_embed = """
    <div style="height: 550px; width: 100%;">
        <script>
          window.wxOConfiguration = {
            orchestrationID: "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
            hostURL: "https://jp-tok.watson-orchestrate.cloud.ibm.com",
            rootElementID: "root",
            deploymentPlatform: "ibmcloud",
            crn: "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::",
            chatOptions: {
                agentId: "96f81e4f-6c52-4162-9d2e-7b054586f1ed", 
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
    </div>
    """
    # Altura suficiente para que el chat no se corte
    components.html(ibm_chat_embed, height=600)


# ==============================================================
# PÁGINA 1: DASHBOARD
# ==============================================================
if page == "Dashboard":
    st.header("📊 Procurement Dashboard")
    
    # Datos de ejemplo
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Contracts", "12")
    col2.metric("High Risk", "3", "+1")
    col3.metric("Medium Risk", "5", "-2")
    col4.metric("Low Risk", "4")

    st.markdown("---")
    st.subheader("Active Contracts")
    df = pd.DataFrame([
        {"Supplier": "Cement Quebec", "Status": "Review", "Risk": "High"},
        {"Supplier": "Germany Alum", "Status": "Active", "Risk": "Medium"},
    ])
    st.dataframe(df, use_container_width=True)

# ==============================================================
# PÁGINA 2: CONTRACT MONITORING (AQUÍ ESTÁ LA IA)
# ==============================================================
elif page == "Contract Monitoring":
    st.header("📘 Contract Analysis AI")

    uploaded = st.file_uploader("Upload contract (PDF)", type=["pdf"])

    if uploaded:
        # Extraer texto del PDF
        with pdfplumber.open(uploaded) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])

        st.success("PDF uploaded successfully!")
        with st.expander("See extracted text"):
            st.text(text[:1000] + "...")

        # BOTÓN PARA LLAMAR A IBM WATSONX
        if st.button("🚀 Analyze with IBM Granite"):
            
            with st.spinner("Consulting IBM Watson AI... please wait..."):
                # 1. Llamada a la API
                raw_response = analyze_contract_with_ibm(text)
                
                # 2. Procesar respuesta
                try:
                    # Limpiamos la respuesta por si la IA añade texto extra fuera del JSON
                    json_start = raw_response.find('{')
                    json_end = raw_response.rfind('}') + 1
                    clean_json = raw_response[json_start:json_end]
                    
                    data = json.loads(clean_json)
                    
                    # 3. Mostrar resultados
                    st.divider()
                    st.subheader(f"Analysis for: {data.get('supplier', 'Unknown Supplier')}")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.caption("Risk Level")
                        risk_badge(data.get('risk_level', 'Unknown'))
                    with c2:
                        st.caption("Recommendation")
                        st.info(data.get('status', 'No status'))
                    
                    st.write(f"**Summary:** {data.get('summary', '')}")
                    
                    st.subheader("⚠️ Detected Risks")
                    for r in data.get('risks', []):
                        st.warning(f"• {r}")
                        
                except Exception as e:
                    st.error("Error interpreting AI response.")
                    st.text("Raw response received:")
                    st.code(raw_response)
                    st.error(f"Details: {e}")

# ==============================================================
# PÁGINA 3: EXTERNAL ALERTS
# ==============================================================
elif page == "External Risk Alerts":
    st.header("🌐 Global Supply Chain Alerts")
    st.info("News feed simulation active.")
    st.write("• **High Risk:** Strike at Montreal Port affects logistics.")
    st.write("• **Medium Risk:** Aluminum price fluctuation in EU market.")
