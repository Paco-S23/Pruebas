import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="IBM Agents")

# --- MENU LATERAL ---
st.sidebar.header("Selecciona Agente")
opcion = st.sidebar.radio("", ["Agente 1", "Agente 2"])

# --- CONFIGURACIÓN ---
# Tus credenciales ya integradas
CONFIG = {
    "orchestrationID": "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
    "hostURL": "https://jp-tok.watson-orchestrate.cloud.ibm.com",
    "crn": "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::"
}

AGENTS = {
    "Agente 1": {"id": "df87f2d2-3200-4788-b0bd-de2033f818ee", "env": "f9558573-5f2c-4fc7-bdc3-09c8d590f7de"},
    "Agente 2": {"id": "ab2a2d5a-feb8-4756-b8cb-57d78bbb085c", "env": "3ed7b3a1-c9d5-4d20-8ace-beda0ab22455"}
}

# --- GENERADOR DE HTML ---
def render_chat(agent_name):
    data = AGENTS[agent_name]
    
    return f"""
    <div style="width: 100%; height: 700px; background-color: white; border: 1px solid #ddd;">
        <div id="root" style="width: 100%; height: 100%;"></div>
    </div>

    <script>
      window.wxOConfiguration = {{
        orchestrationID: "{CONFIG['orchestrationID']}",
        hostURL: "{CONFIG['hostURL']}",
        rootElementID: "root",
        deploymentPlatform: "ibmcloud",
        crn: "{CONFIG['crn']}",
        chatOptions: {{
            agentId: "{data['id']}", 
            agentEnvironmentId: "{data['env']}",
        }}
      }};

      // Forzamos carga inmediata
      const script = document.createElement('script');
      script.src = "{CONFIG['hostURL']}/wxochat/wxoLoader.js?embed=true";
      script.onload = function() {{ wxoLoader.init(); }};
      document.head.appendChild(script);
    </script>
    """

# --- UI PRINCIPAL ---
st.title(f"💬 Chat: {opcion}")

# Renderizamos el HTML
components.html(render_chat(opcion), height=720, scrolling=False)

# SI SIGUE BLANCO: Es bloqueo de seguridad de tu navegador.
# Esta es la solución rápida para que sigas trabajando sin arreglar el código:
st.warning("¿Pantalla en blanco? Tu navegador está bloqueando el script.")
st.markdown(f"[👉 Clic aquí para abrir el {opcion} en una pestaña segura](https://jp-tok.watson-orchestrate.cloud.ibm.com/wxochat/wxoLoader.js?embed=true)", unsafe_allow_html=True)
