import streamlit as st
import requests
import os
from dotenv import load_dotenv

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
# Correct Token Function
# ============================
def get_token():
    url = "https://iam.cloud.ibm.com/identity/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = (
        f"grant_type=urn:ibm:params:oauth:grant-type:apikey"
        f"&apikey={API_KEY}"
    )

    res = requests.post(url, headers=headers, data=data)

    if res.status_code != 200:
        print(res.text)
        return None

    return res.json().get("access_token")


# ============================
# Send message to Agent
# ============================
def call_agent(agent_id, user_message):

    token = get_token()
    if token is None:
        return "❌ Error: Unable to obtain authentication token."

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

    res = requests.post(AGENT_URL, headers=headers, json=payload)

    if res.status_code != 200:
        return f"❌ API Error:\n{res.text}"

    try:
        return res.json()["output"]["messages"][0]["content"]
    except:
        return "❌ Error processing the agent's response."


# =========================================================
# UI — No sidebar, 2 tabs
# =========================================================
st.set_page_config(page_title="IBM Agents UI", layout="centered")

st.title("🤖 IBM Watsonx Agents")
st.write("Interact with your agents easily.")

tabs = st.tabs(["Agent 1", "Agent 2"])

# ------------------------
# Agent 1 Tab
# ------------------------
with tabs[0]:
    st.subheader("Agent 1")

    text1 = st.text_area("Write your question:", key="msg1")

    if st.button("Send to Agent 1"):
        if text1.strip() == "":
            st.warning("Please enter a message.")
        else:
            response = call_agent(AGENT_1_ID, text1)
            st.write("### Response:")
            st.write(response)


# ------------------------
# Agent 2 Tab
# ------------------------
with tabs[1]:
    st.subheader("Agent 2")

    text2 = st.text_area("Write your question:", key="msg2")

    if st.button("Send to Agent 2"):
        if text2.strip() == "":
            st.warning("Please enter a message.")
        else:
            response = call_agent(AGENT_2_ID, text2)
            st.write("### Response:")
            st.write(response)
