import streamlit as st
import streamlit.components.v1 as components

# ==========================================
# Configuración de la página
# ==========================================
st.set_page_config(page_title="IBM Agents - Web Chat", layout="wide")

st.title("🤖 IBM Watson Orchestrate Agents")
st.write("Selecciona un agente en el menú de la izquierda para interactuar.")

# ==========================================
# Definición de las Credenciales (Extraídas de tus scripts)
# ==========================================
# Configuración común para ambos agentes
COMMON_CONFIG = {
    "orchestrationID": "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
    "hostURL": "https://jp-tok.watson-orchestrate.cloud.ibm.com",
    "crn": "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::"
}

# Configuración específica por Agente
AGENTS = {
    "Agente 1": {
        "agentId": "df87f2d2-3200-4788-b0bd-de2033f818ee",
        "agentEnvironmentId": "f9558573-5f2c-4fc7-bdc3-09c8d590f7de"
    },
    "Agente 2": {
        "agentId": "ab2a2d5a-feb8-4756-b8cb-57d78bbb085c",
        "agentEnvironmentId": "3ed7b3a1-c9d5-4d20-8ace-beda0ab22455"
    }
}

# ==========================================
# Selector de Agente
# ==========================================
agent_selection = st.sidebar.radio("Elige tu Agente:", ["Agente 1", "Agente 2"])

# ==========================================
# Generador de HTML para el Chat
# ==========================================
def get_chat_html(agent_name):
    config = AGENTS[agent_name]
    
    # Creamos el HTML completo inyectando las variables correctas
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ margin: 0; padding: 0; background-color: #f0f2f6; font-family: sans-serif; }}
            #root {{ width: 100%; height: 600px; }}
        </style>
    </head>
    <body>
        <div id="root"></div>

        <script>
          window.wxOConfiguration = {{
            orchestrationID: "{COMMON_CONFIG['orchestrationID']}",
            hostURL: "{COMMON_CONFIG['hostURL']}",
            rootElementID: "root",
            deploymentPlatform: "ibmcloud",
            crn: "{COMMON_CONFIG['crn']}",
            chatOptions: {{
                agentId: "{config['agentId']}", 
                agentEnvironmentId: "{config['agentEnvironmentId']}",
            }}
          }};

          setTimeout(function () {{
            const script = document.createElement('script');
            script.src = "{COMMON_CONFIG['hostURL']}/wxochat/wxoLoader.js?embed=true";
            script.addEventListener('load', function () {{
                wxoLoader.init();
            }});
            document.head.appendChild(script);
          }}, 0);
        </script>
    </body>
    </html>
    """
    return html_code

# ==========================================
# Renderizado
# ==========================================
st.subheader(f"Conectado con: {agent_selection}")

# Renderizamos el HTML dentro de un iframe de Streamlit
# Height=700 para dar espacio al chat completo
components.html(get_chat_html(agent_selection), height=700, scrolling=True)
