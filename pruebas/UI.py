import streamlit as st
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
    initial_sidebar_state="expanded"
)

st.title("📑 ProcureWatch")
st.markdown("### AI-powered contract monitoring system")
st.write("Upload a PDF contract to detect risks and extract key data using IBM Granite.")

# -------------------------------
# 2. LÓGICA DE CONEXIÓN CON IBM (BACKEND)
# -------------------------------
def analyze_contract_with_ibm(contract_text):
    # TUS CREDENCIALES
    creds = {
        "url": "https://us-south.ml.cloud.ibm.com", # Dallas
        "apikey": "7df1e07ee763823210cc7609513c0c6fe4ff613cc3583613def0ec12f2570a17"
    }
    project_id = "077c11a6-2c5e-4c89-9a99-c08df3cb67ff"

    # Configuración del modelo
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

        # Instrucción (Prompt)
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
# 3. HELPER: Etiqueta de Riesgo
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
# 4. BARRA LATERAL (Solo Navegación)
# -------------------------------
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Dashboard", "Contract Monitoring", "External Risk Alerts"]
)

st.sidebar.markdown("---")
st.sidebar.caption("Powered by IBM watsonx.ai")

# ==============================================================
# PÁGINA 1: DASHBOARD
# ==============================================================
if page == "Dashboard":
    st.header("📊 Procurement Dashboard")
    
    # Métricas clave (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Contracts", "12")
    col2.metric("High Risk", "3", "+1", delta_color="inverse")
    col3.metric("Medium Risk", "5", "-2")
    col4.metric("Low Risk", "4")

    st.markdown("---")
    st.subheader("Active Contracts Overview")
    
    # Tabla de ejemplo
    df = pd.DataFrame([
        {"Supplier": "Cement Quebec", "Delivery": "2025-02-15", "Risk": "High"},
        {"Supplier": "Germany Alum", "Delivery": "2025-03-01", "Risk": "Medium"},
        {"Supplier": "Montreal Steel", "Delivery": "2025-02-20", "Risk": "Low"},
    ])
    st.dataframe(df, use_container_width=True)

# ==============================================================
# PÁGINA 2: CONTRACT MONITORING (IA REAL)
# ==============================================================
elif page == "Contract Monitoring":
    st.header("📘 Contract Analysis AI")

    uploaded = st.file_uploader("Upload contract (PDF)", type=["pdf"])

    if uploaded:
        # 1. Extraer texto
        with pdfplumber.open(uploaded) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])

        st.success("PDF uploaded successfully!")
        
        # Mostramos un previo del texto (ocultable)
        with st.expander("View extracted text content"):
            st.text(text)

        # 2. Botón de Análisis
        if st.button("🚀 Analyze with IBM Granite", type="primary"):
            
            with st.spinner("🤖 Consulting IBM Watson AI... analyzing risks..."):
                # Llamada al Backend
                raw_response = analyze_contract_with_ibm(text)
                
                # Intentamos limpiar y leer el JSON
                try:
                    # Truco: buscar dónde empieza '{' y termina '}' por si la IA habla de más
                    json_start = raw_response.find('{')
                    json_end = raw_response.rfind('}') + 1
                    
                    if json_start != -1 and json_end != -1:
                        clean_json = raw_response[json_start:json_end]
                        data = json.loads(clean_json)
                        
                        # --- MOSTRAR RESULTADOS ---
                        st.divider()
                        st.subheader(f"Analysis Report: {data.get('supplier', 'Unknown Supplier')}")
                        
                        # Fila de estatus
                        c1, c2 = st.columns(2)
                        with c1:
                            st.caption("Risk Level Detected")
                            risk_badge(data.get('risk_level', 'Unknown'))
                        with c2:
                            st.caption("AI Recommendation")
                            st.info(f"**{data.get('status', 'No status')}**")
                        
                        # Resumen
                        st.write(f"**Summary:** {data.get('summary', 'No summary available.')}")
                        
                        # Lista de Riesgos
                        st.subheader("⚠️ Identified Risks")
                        if data.get('risks'):
                            for r in data.get('risks'):
                                st.warning(f"• {r}")
                        else:
                            st.success("No significant risks detected.")
                            
                    else:
                        st.error("AI Response format error (No JSON found).")
                        st.code(raw_response)
                        
                except Exception as e:
                    st.error("Error interpreting AI response.")
                    st.write("Raw Output:")
                    st.code(raw_response)

# ==============================================================
# PÁGINA 3: EXTERNAL ALERTS
# ==============================================================
elif page == "External Risk Alerts":
    st.header("🌐 Global Supply Chain Alerts")
    
    query = st.text_input("Search news (Simulated):", "construction materials")
    
    if st.button("Search"):
        st.write(f"Searching for: **{query}**...")
        st.markdown("---")
        
        # Noticias simuladas
        st.subheader("Strike at Montreal Port affects cement logistics")
        st.caption("Source: Logistics Daily • 2 hours ago")
        st.error("🔴 High Impact")
        st.write("Potential delay of 2-3 weeks for incoming shipments.")
        
        st.markdown("---")
        
        st.subheader("Aluminum price stabilizes in EU market")
        st.caption("Source: Global Trade • 5 hours ago")
        st.success("🟢 Low Impact")
