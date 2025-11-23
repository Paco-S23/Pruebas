import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================
# Configuration
# ============================
API_KEY = os.getenv("WATSONX_APIKEY")
PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
AGENT_1_ID = os.getenv("AGENT_1_ID")
AGENT_2_ID = os.getenv("AGENT_2_ID")

BASE_URL = "https://us-south.ml.cloud.ibm.com"
AGENT_URL = f"{BASE_URL}/watsonx/agents/v1/agent_runs"

# ============================
# Function to get Token
# ============================
def get_token():
    if not API_KEY:
        st.error("❌ API KEY missing in .env file")
        return None

    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = (
        f"grant_type=urn:ibm:params:oauth:grant-type:apikey"
        f"&apikey={API_KEY}"
    )

    try:
        res = requests.post(url, headers=headers, data=data)
        res.raise_for_status() # Raises error if status is not 200
        return res.json().get("access_token")
    except Exception as e:
        st.error(f"❌ Error obtaining token: {e}")
        return None

# ============================
# Send message to Agent
# ============================
def call_agent(agent_id, user_message):
    token = get_token()
    if token is None:
        return "❌ Error: Unable to obtain authentication token."

    if not agent_id:
        return "❌ Error: Agent ID not configured."

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "agent_id": agent_id,
        "project_id": PROJECT_ID,
        "input": {
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
    }

    try:
        res = requests.post(AGENT_URL, headers=headers, json=payload)
        
        if res.status_code != 200:
            return f"❌ API Error ({res.status_code}):\n{res.text}"

        # Attempt to parse the response
        data = res.json()
        # Adjust this path according to the exact response structure of your agent
        return data.get("output", {}).get("messages", [{}])[0].get("content", "No content received")
        
    except Exception as e:
        return f"❌ Error processing agent response: {str(e)}"

# =========================================================
# UI — User Interface
# =========================================================
st.set_page_config(page_title="IBM Agents UI", layout="centered")

st.title("🛡️ SmartChain Guardian")
st.write("Interact with your IBM Watsonx AI agents.")

# Check basic configuration
if not PROJECT_ID:
    st.warning("⚠️ Warning: PROJECT_ID not found in environment variables.")

tabs = st.tabs(["🤖 Internal Monitor", "🌍 External Risk Monitor"])

# ------------------------
# Agent 1 Tab
# ------------------------
with tabs[0]:
    st.subheader("Internal Contract Monitor")
    st.info("This agent cross-references all contracts with actual warehouse records to identify compliance issues.")
    
    text1 = st.text_area("Enter your query regarding internal contracts:", key="msg1")

    if st.button("Send to Agent 1"):
        if text1.strip() == "":
            st.warning("Please enter a message.")
        else:
            with st.spinner("Consulting Agent 1..."):
                response = call_agent(AGENT_1_ID, text1)
                st.write("### Response:")
                st.markdown(response)

# ------------------------
# Agent 2 Tab
# ------------------------
with tabs[1]:
    st.subheader("Supply Chain Risk Monitor")
    st.info("This agent scans online sources to detect external events that may impact the supply chain.")

    text2 = st.text_area("Enter your query regarding external risks:", key="msg2")

    if st.button("Send to Agent 2"):
        if text2.strip() == "":
            st.warning("Please enter a message.")
        else:
            with st.spinner("Consulting Agent 2..."):
                response = call_agent(AGENT_2_ID, text2)
                st.write("### Response:")
                st.markdown(response)
