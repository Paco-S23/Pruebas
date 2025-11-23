import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="IBM Agents UI", layout="wide")

st.title("🤖 IBM Watson Orchestrate Agents")
st.info("👇 El chat debería aparecer dentro del recuadro de abajo. Si ves un icono de chat en la esquina, dale clic.")

# ==========================================
# Configuración (Tus scripts)
# ==========================================
COMMON_CONFIG = {
    "orchestrationID": "03ada0a325ec426d893eef11d68e7d31_f322ed2b-accb-4baa-a7e9-3d0419313afc",
    "hostURL": "https://jp-tok.watson-orchestrate.cloud.ibm.com",
    "crn": "crn:v1:bluemix:public:watsonx-orchestrate:jp-tok:a/03ada0a325ec426d893eef11d68e7d31:f322ed2b-accb-4baa-a7e9-3d0419313afc::"
}

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

# Selector en la barra lateral
agent_selection = st.sidebar.radio("Selecciona el Agente:", list(AGENTS.keys()))

def get_chat_html(agent_name):
    config = AGENTS[agent_name]
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            /* Forzamos que el contenedor ocupe todo el espacio y tenga fondo blanco */
            body, html {{ height: 100%; margin: 0; background-color: #ffffff; }}
            #root {{ width: 100%; height: 100%; }}
        </style>
    </head>
    <body>
        <div id="root">Cargando chat de IBM...</div>

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
          }}, 500);
        </script>
    </body>
    </html>
    """
    return html_code

st.write(f"### Conectado con: {agent_selection}")

# Aquí renderizamos el chat.
# Le puse un borde para que veas el área activa.
components.html(get_chat_html(agent_selection), height=800, scrolling=False)
