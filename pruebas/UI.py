import streamlit as st

st.set_page_config(page_title="IBM Orchestrate Multi-Agent UI", layout="wide")

st.title("IBM Watsonx Orchestrate – Multi-Agent Chat")
st.write("Selecciona un agente y chatea directamente desde Streamlit.")

# === EMBEDS DE TUS DOS AGENTES ===

embed_internal_contract_monitor = """
<div id="root" style="height: 700px; width: 100%;"></div>

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
        wxoLoader.init();
    });
    document.head.appendChild(script);
  }, 0);
</script>
"""

embed_construction_risk_monitor = """
<div id="root" style="height: 700px; width: 100%;"></div>

<script>
  window.wxOConfiguration = {
    orchestrationID: "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
    hostURL: "https://jp-tok.watson-orchestrate.cloud.ibm.com",
    rootElementID: "root",
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
        wxoLoader.init();
    });
    document.head.appendChild(script);
  }, 0);
</script>
"""

# === SELECTOR DE AGENTES ===

agent_choice = st.selectbox(
    "Selecciona el agente que deseas usar:",
    [
        "Internal Contract Monitor",
        "Construction & Supply Chain Risk Monitor"
    ]
)

# === RENDER DEL AGENTE SELECCIONADO ===

if agent_choice == "Internal Contract Monitor":
    st.subheader("Agente: Internal Contract Monitor")
    st.components.v1.html(embed_internal_contract_monitor, height=750)

elif agent_choice == "Construction & Supply Chain Risk Monitor":
    st.subheader("Agente: Construction & Supply Chain Risk Monitor")
    st.components.v1.html(embed_construction_risk_monitor, height=750)
