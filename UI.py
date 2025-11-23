import streamlit as st
import pdfplumber
import pandas as pd

# -------------------------------
# GENERAL CONFIGURATION
# -------------------------------
st.set_page_config(
    page_title="ProcureWatch • Contract & Supply Monitor",
    layout="wide",
)

st.title("📑 ProcureWatch")
st.write("AI-powered contract monitoring and external supply-chain risk detection.")

# -------------------------------
# SIDEBAR NAVIGATION
# -------------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Dashboard", "Contract Monitoring", "External Risk Alerts"]
)

# --------------------------------------------------------------
# KPI CARDS COMPONENT
# --------------------------------------------------------------
def kpi_card(label, value, delta=None):
    col = st.container()
    with col:
        st.metric(label, value, delta)

# --------------------------------------------------------------
# RISK BADGE COMPONENT
# --------------------------------------------------------------
def risk_badge(level):
    if level == "High":
        st.error("🔴 High Risk")
    elif level == "Medium":
        st.warning("🟠 Medium Risk")
    else:
        st.success("🟢 Low Risk")


# --------------------------------------------------------------
# MOCK DATA (REPLACE WITH REAL API LATER)
# --------------------------------------------------------------
contracts_data = pd.DataFrame([
    {
        "Supplier": "Cement Quebec Inc.",
        "Material": "Cement",
        "Delivery Date": "2025-02-15",
        "Status": "Under Review",
        "Risk": "High"
    },
    {
        "Supplier": "Germany Alum Co.",
        "Material": "Aluminum",
        "Delivery Date": "2025-03-01",
        "Status": "On Track",
        "Risk": "Medium"
    },
    {
        "Supplier": "Montreal SteelWorks",
        "Material": "Steel",
        "Delivery Date": "2025-02-20",
        "Status": "Delayed",
        "Risk": "High"
    }
])

# Calculate KPIs
total_contracts = len(contracts_data)
high_risk_count = sum(contracts_data["Risk"] == "High")
medium_risk_count = sum(contracts_data["Risk"] == "Medium")
low_risk_count = sum(contracts_data["Risk"] == "Low")


# ==============================================================
# PAGE 1 • DASHBOARD
# ==============================================================
if page == "Dashboard":
    st.header("📊 Procurement Dashboard")

    # KPI CARDS ROW
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Contracts", total_contracts)
    col2.metric("High Risk", high_risk_count)
    col3.metric("Medium Risk", medium_risk_count)
    col4.metric("Low Risk", low_risk_count)

    st.markdown("---")
    st.subheader("📄 Active Contracts Overview")

    st.dataframe(contracts_data, use_container_width=True)


# ==============================================================
# PAGE 2 • CONTRACT MONITORING
# ==============================================================
elif page == "Contract Monitoring":
    st.header("📘 Contract Monitoring")

    uploaded = st.file_uploader("Upload contract PDF", type=["pdf"])

    if uploaded:
        with pdfplumber.open(uploaded) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])

        st.subheader("Extracted Contract Text")
        st.text_area("Content", text, height=250)

        if st.button("Analyze Contract"):
            # Mock example results (replace with IBM agent response)
            response = {
                "document_type": "Supply Contract",
                "fields": {
                    "supplier": "Cement Quebec Inc.",
                    "quantity": "500 tons",
                    "delivery_date": "2025-02-15",
                    "cost": "$120,000 CAD"
                },
                "risks": [
                    "Delivery date approaching with no shipment verification.",
                    "Quality specifications missing.",
                    "Penalty clause unclear."
                ],
                "risk_level": "High",
                "status": "Under Review"
            }

            st.subheader("📄 Extracted Information")
            st.json(response["fields"])

            st.subheader("⚠️ Risks")
            for r in response["risks"]:
                st.warning(r)

            st.subheader("Overall Risk Level")
            risk_badge(response["risk_level"])

            st.subheader("Contract Status")
            st.info(response["status"])


# ==============================================================
# PAGE 3 • EXTERNAL RISK ALERTS
# ==============================================================
elif page == "External Risk Alerts":
    st.header("🌐 External Risk Alerts")

    query = st.text_input("Search news related to:", "cement, aluminum, logistics")

    if st.button("Fetch News"):
        news_results = [
            {
                "title": "Aluminum plant in Germany shuts down temporarily",
                "source": "Reuters",
                "risk": "High",
                "impact": "Possible disruption in aluminum supply."
            },
            {
                "title": "Severe snowstorm expected in Quebec",
                "source": "CBC News",
                "risk": "Medium",
                "impact": "Potential delays in cement transportation."
            }
        ]

        for news in news_results:
            st.subheader(news["title"])
            st.write(f"📰 Source: {news['source']}")
            st.write(f"📌 Impact: {news['impact']}")
            risk_badge(news["risk"])

            st.markdown("---")
