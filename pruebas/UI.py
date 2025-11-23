import streamlit as st
import streamlit.components.v1 as components
import pdfplumber
import pandas as pd
import json
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

# -------------------------------
# CONFIGURACIÓN DE LA APP
# -------------------------------
st.set_page_config(
    page_title="ProcureWatch • Contract & Supply Monitor",
    layout="wide",
)

st.title("📑 ProcureWatch")
st.write("AI-powered contract monitoring and external supply-chain risk detection.")


# -------------------------------
# FUNCIÓN DE IBM WATSON (Backend)
# -------------------------------
def analyze_contract_with_ibm(contract_text):
    # 1. CREDENCIALES
    creds = {
        "url": "https://us-south.ml.cloud.ibm.com",
        "apikey": "7df1e07ee763823210cc7609513c0c6fe4ff613cc3583613def0ec12f2570a17"
    }
    project_id = "077c11a6-2c5e-4c89-9a99-c08df3cb67ff"

    # 2. MODELO
    model_id = "ibm/granite-13b-chat-v2"

    parameters = {
        GenParams.DECODING_METHOD: "greedy",
        GenParams.MAX_NEW_TOKENS: 500,
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

        # 3. PROMPT
        prompt = f"""
        Analyze the following contract text and extract key information in valid JSON format.

        Text:
        {contract_text[:3000]} 

        Required JSON Structure:
        {{
            "supplier": "Name of supplier",
            "risk_level": "High/Medium/Low",
            "risks": ["risk 1", "risk 2"],
            "status": "Recommended status",
            "summary": "Short summary of the contract"
        }}

        Output only the JSON. Do not add markdown formatting:
        """

        generated_response = model.generate_text(prompt=prompt)
        return generated_response

    except Exception as e:
        return f"Error: {str(e)}"


# -------------------------------
# COMPONENTES UI (Helpers)
# -------------------------------
def risk_badge(level):
    if level == "High":
        st.error("🔴 High Risk")
    elif level == "Medium":
        st.warning("🟠 Medium Risk")
    else:
        st.success("🟢 Low Risk")


# -------------------------------
# NAVEGACIÓN SIDEBAR
# -------------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Dashboard", "Contract Monitoring", "External Risk Alerts"]
)

# --- CHAT DE IBM EN EL SIDEBAR ---
with st.sidebar:
    st.markdown("---")
    st.subheader("🤖 AI Assistant")

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
    components.html(ibm_chat_embed, height=600)

# ==============================================================
# PÁGINA 1 • DASHBOARD
# ==============================================================
if page == "Dashboard":
    st.header("📊 Procurement Dashboard")

    # Mock Data
    contracts_data = pd.DataFrame([
        {"Supplier": "Cement Quebec Inc.", "Material": "Cement", "Risk": "High"},
        {"Supplier": "Germany Alum Co.", "Material": "Aluminum", "Risk": "Medium"},
        {"Supplier": "Montreal SteelWorks", "Material": "Steel", "Risk": "High"}
    ])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Contracts", 3)
    col2.metric("High Risk", 2)
    col3.metric("Medium Risk", 1)
    col4.metric("Low Risk", 0)

    st.markdown("---")
    st.subheader("📄 Active Contracts Overview")
    st.dataframe(contracts_data, use_container_width=True)

# ==============================================================
# PÁGINA 2 • CONTRACT MONITORING (LÓGICA CORREGIDA)
# ==============================================================
elif page == "Contract Monitoring":
    st.header("📘 Contract Monitoring")

    uploaded = st.file_uploader("Upload contract PDF", type=["pdf"])

    if uploaded:
        with pdfplumber.open(uploaded) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])

        st.subheader("Extracted Contract Text")
        st.text_area("Content", text, height=150)

        # --- AQUÍ ESTABA EL ERROR: FALTABA EL BOTÓN ---
        if st.button("Analyze Contract with IBM Granite"):

            with st.spinner("🤖 Consulting IBM Watson AI..."):
                # 1. Llamar a la función
                raw_response = analyze_contract_with_ibm(text)

                # 2. Intentar convertir el texto a JSON real
                try:
                    # A veces la IA devuelve texto extra, intentamos limpiar si es necesario
                    # o confiar en que granite siga la instrucción JSON
                    response_json = json.loads(raw_response)

                    st.success("Analysis Complete!")

                    # 3. Mostrar resultados bonitos
                    st.subheader("📄 Extracted Information")
                    st.write(f"**Supplier:** {response_json.get('supplier', 'Unknown')}")
                    st.write(f"**Summary:** {response_json.get('summary', 'No summary provided')}")

                    st.subheader("⚠️ Risks Identified")
                    for r in response_json.get("risks", []):
                        st.warning(r)

                    st.subheader("Overall Risk Level")
                    risk_badge(response_json.get("risk_level", "Unknown"))

                    st.subheader("Contract Status")
                    st.info(response_json.get("status", "Unknown"))

                except json.JSONDecodeError:
                    st.error("Error parsing AI response via JSON.")
                    st.write("Raw response form AI:")
                    st.code(raw_response)

# ==============================================================
# PÁGINA 3 • EXTERNAL RISK ALERTS
# ==============================================================
elif page == "External Risk Alerts":
    st.header("🌐 External Risk Alerts")
    query = st.text_input("Search news related to:", "cement, aluminum, logistics")

    if st.button("Fetch News"):
        st.info("Searching global news sources...")
        # Mock results
        st.subheader("Aluminum plant in Germany shuts down temporarily")
        st.write("📰 Source: Reuters")
        risk_badge("High")
        st.markdown("---")