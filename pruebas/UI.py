import streamlit as st
import base64

st.set_page_config(page_title="IBM Orchestrate UI", layout="wide")

# --------------------------------------------------------------------------------
# FUNCIÓN PARA INCRUSTAR AGENTE DE ORCHESTRATE
# --------------------------------------------------------------------------------
def render_orch_embed(orchestration_id, host_url, crn, agent_id, agent_env_id):
    embed_code = """
    <div id="root"></div>
    <script>
      window.wxOConfiguration = {
        orchestrationID: "%s",
        hostURL: "%s",
        rootElementID: "root",
        deploymentPlatform: "ibmcloud",
        crn: "%s",
        chatOptions: {
            agentId: "%s", 
            agentEnvironmentId: "%s"
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
    """ % (orchestration_id, host_url, crn, agent_id, agent_env_id)

    st.components.v1.html(embed_code, height=650, scrolling=True)

# --------------------------------------------------------------------------------
# CONFIGURACIONES DE TUS DOS AGENTES
# --------------------------------------------------------------------------------

agents = {
    "Internal Contract Monitor": {
        "orch_id": "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
        "url": "https://jp-tok.watson-orchestrate.cloud.ibm.com",
        "crn": "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::",
        "agent": "df87f2d2-3200-4788-b0bd-de2033f818ee",
        "env": "f9558573-5f2c-4fc7-bdc3-09c8d590f7de"
    },
    "Construction & Supply Chain Risk Monitor": {
        "orch_id": "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
        "url": "https://jp-tok.watson-orchestrate.cloud.ibm.com",
        "crn": "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::",
        "agent": "ab2a2d5a-feb8-4756-b8cb-57d78bbb085c",
        "env": "3ed7b3a1-c9d5-4d20-8ace-beda0ab22455"
    }
}

# --------------------------------------------------------------------------------
# UI PRINCIPAL
# --------------------------------------------------------------------------------
st.title("🤖 IBM Watson Orchestrate – Multi-Agent UI")
st.write("Selecciona el agente que quieras cargar:")

opcion = st.selectbox(
    "Agentes disponibles",
    list(agents.keys())
)

st.subheader("Agente seleccionado: " + opcion)

# Obtiene la config
cfg = agents[opcion]

# Renderiza el agente de Orchestrate
render_orch_embed(
    cfg["orch_id"],
    cfg["url"],
    cfg["crn"],
    cfg["agent"],
    cfg["env"]
)

st.success("Agente cargado correctamente.")
